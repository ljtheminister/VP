import pandas as pd
import numpy as np
from collections import defaultdict
from decimal import Decimal
import xlwt
import csv
import cPickle as pickle

data = pd.read_csv('Raw Data File for Business One.csv')

data['copay'] = data['Avg_Wt_Copay'].apply(lambda x: 0 if x=='-' else Decimal(x.strip('$')))
data['copay_Rx_lives'] = data.ix[:, ['Total_Lives_Rx', 'Avg_Wt_Copay']].apply(lambda x: 0 if x['Avg_Wt_Copay']=='-' else x['Total_Lives_Rx'], axis=1)

# Life count by channel
all_years = {}
channel_data = data.groupby('Channel')
for channel, channel_grp in channel_data:
    all_lives = 0
    rx_lives = 0 
    entities = channel_grp.groupby(['Entity_Name', 'Period_Year'])
    for entity, entity_grp in entities:
        #all_lives += entity_grp['Total_Lives'].mean()
        #rx_lives += entity_grp['Total_Lives_Rx'].mean()
        all_lives += entity_grp['Total_Lives'].sum()/12.
        rx_lives += entity_grp['Total_Lives_Rx'].sum()/12.
    all_years[channel] = (all_lives, rx_lives)

# Life count by channel/year
yearly = {}
grouped_data = data.groupby(['Period_Year', 'Channel'])
for channel_year, group in grouped_data:
    all_lives = 0
    rx_lives = 0
    entities = group.groupby(['Entity_Name'])
    for entity, entity_grp in entities:
        #all_lives += entity_grp['Total_Lives'].mean()
        #rx_lives += entity_grp['Total_Lives_Rx'].mean()
        all_lives += entity_grp['Total_Lives'].sum()/12.
        rx_lives += entity_grp['Total_Lives_Rx'].sum()/12.
    yearly[channel_year] = (all_lives, rx_lives) 
    

yearly_lives = defaultdict(dict)
for year, channel in yearly.keys():
    yearly_lives[year][channel] = yearly[(year,channel)]

channels = ['Commercial', 'DoD', 'Managed Medicaid', 'Medicare', 'PBM Commercial', 'PBM Medicare', 'State Medicaid', 'VA']

with open('BusinessOne_Overall_Monthly.csv', 'wb') as f:
    csvwriter = csv.writer(f, delimiter=',')
    csvwriter.writerow(['All Years'])
    csvwriter.writerow(['', 'All Lives', 'Rx Lives'])
    for channel in channels:
        all_lives, rx_lives = all_years[channel]
        csvwriter.writerow([channel, int(all_lives), int(rx_lives)])

    for year in yearly_lives.keys():
        csvwriter.writerow([])
        csvwriter.writerow([str(year)])
        csvwriter.writerow(['', 'All Lives', 'Rx Lives'])
        for channel in channels: 
            try:
                all_lives, rx_lives = yearly_lives[year][channel] 
            except: 
                all_lives, rx_lives = 0, 0
            csvwriter.writerow([channel, int(all_lives), int(rx_lives)]) 

def compute_lives_copay(data, tiered_data, year, channel, tier, restriction):
    all_lives = 0
    rx_lives = 0
    rx_lives_sum = 0
    copay = 0 # average weighted copay
    copay_sum = 0
    entities = data.groupby('Entity_Name')
    for entity, entity_grp in entities:
        #all_lives += entity_grp['Total_Lives'].mean()
        #rx_lives += entity_grp['Total_Lives_Rx'].mean()
        all_lives += entity_grp['Total_Lives'].sum()/12.
        rx_lives += entity_grp['Total_Lives_Rx'].sum()/12.
        rx_lives_sum += entity_grp['Total_Lives_Rx'].sum()
        copay_sum += (entity_grp.copay * entity_grp.copay_Rx_lives).sum()

    if rx_lives_sum == 0:
        pass
    else:
        copay = copay_sum/rx_lives_sum

    restrict_dict = tiered_data[year][channel][tier][restriction] 
    restrict_dict['All Lives'] = all_lives
    restrict_dict['Rx Lives'] = rx_lives
    restrict_dict['Copay'] = copay
    restrict_dict['Copay sum'] = copay_sum
    restrict_dict['Copay Rx Lives'] = rx_lives_sum
    all_plans = tiered_data[year]['All Plans'][tier][restriction]
    all_plans['All Lives'] += all_lives
    all_plans['Rx Lives'] += rx_lives
    all_plans['Copay sum'] += copay_sum
    all_plans['Copay Rx Lives'] += rx_lives_sum
    if all_plans['Copay Rx Lives']:
        all_plans['Copay'] = all_plans['Copay sum']/all_plans['Copay Rx Lives']


years = sorted(data['Period_Year'].unique())
channels = sorted(data['Channel'].unique())
tiers = sorted(data['Form_Status'].unique())
restrictions = ['PA only', 'PA plus', 'Non-PA', 'No Restrictions']
items = ['All Lives', 'Rx Lives', 'Copay', 'Copay sum', 'Copay Rx Lives']

def instantiate_tiered_data():
    tiered_data = {}
    channels.append('All Plans')
    for year in years:
        tiered_data[year] = {}
        t_year = tiered_data[year]
        for channel in channels:
            t_year[channel] = {}
            t_channel = t_year[channel]
            for tier in tiers:
                t_channel[tier] = {}
                t_tier = t_channel[tier]
                for restriction in restrictions:
                    t_tier[restriction] = {}
                    t_restriction = t_tier[restriction]
                    for item in items:
                        t_restriction[item] = 0
    channels.pop()
    return tiered_data 

def compute_tier_counts(data):
    tiered_data = instantiate_tiered_data()
    years_group = data.groupby(['Period_Year'])

    for year, year_data in years_group:
        print year
        channels_group = year_data.groupby(['Channel'])

        for channel, channel_data in channels_group:
            print channel
            tiers_group = channel_data.groupby(['Form_Status'])

            for tier, tier_data in tiers_group:
                print tier
                PA_only = tier_data.query("Restrict_PA=='Y' and Restrict_SE=='-' and Restrict_QL=='-' and Restrict_AR=='-'")
                compute_lives_copay(PA_only, tiered_data, year, channel, tier, 'PA only')

                PA_plus = tier_data.query("Restrict_PA=='Y' and (Restrict_SE=='Y' or Restrict_QL=='Y' or Restrict_AR=='Y')")
                compute_lives_copay(PA_plus, tiered_data, year, channel, tier, 'PA plus')

                Non_PA = tier_data.query("Restrict_PA=='-' and (Restrict_SE=='Y' or Restrict_QL=='Y' or Restrict_AR=='Y')")
                compute_lives_copay(Non_PA, tiered_data, year, channel, tier, 'Non-PA')

                No_restrictions = tier_data.query("Restrict_PA=='-' and Restrict_SE=='-' and Restrict_QL=='-' and Restrict_AR=='-'")
                compute_lives_copay(No_restrictions, tiered_data, year, channel, tier, 'No Restrictions')
    return tiered_data


tiered_data = compute_tier_counts(data)
pickle.dump(tiered_data, open('tiered_BusinessOne.p', 'wb'))

# Write out tiered results to csv

#tier_labels = ['', '', 'Tier 1', '', '', 'Tier 2', '', '', 'Tier 3', '', '', 'Tier 4', '', '', 'Tiers 5-8', '']
#restrictions_labels = ['', 'PA Only', 'PA +', 'R (Non-PA)', 'PA Only', 'PA +', 'R (Non-PA)', 'PA Only', 'PA +', 'R (Non-PA)', 'PA Only', 'PA +', 'R (Non-PA)', 'PA Only', 'PA +', 'R (Non-PA)']

tier_labels = ['', 'Tier 1', '', '', '',  'Tier 2', '', '', '',  'Tier 3', '', '', '',  'Tier 4', '', '', '',  'Tier 5-8', '', '', '']

restrictions_labels = ['', 'PA Only', 'PA +', 'R (Non-PA)', 'No Restrictions', 'PA Only', 'PA +', 'R (Non-PA)', 'No Restrictions', 'PA Only', 'PA +', 'R (Non-PA)', 'No Restrictions', 'PA Only', 'PA +', 'R (Non-PA)', 'No Restrictions', 'PA Only', 'PA +', 'R (Non-PA)', 'No Restrictions']


tiers_of_interest = ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4', 'Tier 5-8']

tiers_of_interest = tiers
tier_labels = ['']
restriction_labels = ['']
for tier in tiers:
    tier_labels.append(tier)
    for i in xrange(3):
        tier_labels.append('')
    for restriction in restrictions:
        restrictions_labels.append(restriction) 


def aggregate_channel_data(data, year, channel, item):
    channel_data = [channel]
    d = data[year][channel]
    for tier in tiers_of_interest:
        for restriction in restrictions:
            channel_data.append(d[tier][restriction][item])
    return channel_data
    
def write_tiered_data(filename, tiered_data, item):
    with open('%s.csv'%(filename), 'wb') as f:
        csvwriter = csv.writer(f, delimiter=',')
        for year in years:
            csvwriter.writerow([str(year)])
            csvwriter.writerow(tier_labels)
            csvwriter.writerow(restriction_labels)
            for channel in channels:
                channel_data = aggregate_channel_data(tiered_data, year, channel, item)
                csvwriter.writerow(channel_data)
            all_plans_sum = aggregate_channel_data(tiered_data, year, 'All Plans', item)
            csvwriter.writerow(all_plans_sum)
            csvwriter.writerow([])


items = ['All Lives', 'Rx Lives', 'Copay']
write_tiered_data('BusinessOne_All_Lives', tiered_data, 'All Lives')
write_tiered_data('BusinessOne_Rx_Lives', tiered_data, 'Rx Lives')
write_tiered_data('BusinessOne_Copay', tiered_data, 'Copay')

csv_list = ['BusinessOne_Overall', 'BusinessOne_Overall_Monthly', 'BusinessOne_All_Lives', 'BusinessOne_Rx_Lives', 'BusinessOne_Copay']

workbook = xlwt.Workbook()
for csv_name in csv_list:
    f = open(csv_name + '.csv', 'rb')
    g = csv.reader(f, delimiter=',')
    sheet = workbook.add_sheet(csv_name) 

    for i, row in enumerate(g):
        for j, value in enumerate(row):
            sheet.write(i, j, value)

workbook.save('BusinessOne.xls')

#### CHECKING FOR MULTIPLE TIER IN SAME ENTITY/YEAR 

tier_counts = defaultdict(int)
entities_group = data.groupby(['Entity_Name', 'Period_Year', 'Channel'])
index = pd.Series()

for entity, entity_data in entities_group:
    print entity
    tier_count = len(entity_data['Form_Status'].unique())
    tier_counts[tier_count] += 1
    if tier_count > 1:
        index = index.append(pd.Series(entity_data.index))

index = pd.Series(index)
tiers_data = data.ix[index]

multiple_tiers = tiers_data.groupby(['Entity_Name', 'Period_Year', 'Channel'])
tier_combos = defaultdict(int)

for entity, entity_data in multiple_tiers:
    tier_combo = sorted(entity_data['Form_Status'].unique())
    tier_combos[str(tier_combo)] += 1


'''
workbook = xlwt.Workbook()
sheet = workbook.add_sheet('BusinessOne-Overall')

sheet.write(0, 0, 'All Years')
sheet.write(1, 1, 'All Lives')
sheet.write(1, 2, 'Rx Lives')

row_num = 2
for channel in channels:
    all_lives, rx_lives = all_years[channel]
    sheet.write(row_num, 0, '%s, %s, %s'%(channel, str(all_lives), str(rx_lives)))
    row_num += 1

workbook.save('BusinessOne.xls')
'''
