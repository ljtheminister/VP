import pandas as pd
import numpy as np
import openpyxl
import xlrd
import csv
import string
import Queue
import cPickle as pickle
from collections import defaultdict

states = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

months = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
}

def process_worksheet(worksheet):
    name = worksheet.name
    year = name[-4:]
    month = months[name[:-4][:3]]

    num_rows = worksheet.nrows
    curr_row = 10
    header = worksheet.row(curr_row)
    header = [str(x.value) for x in header]

    table = []
    while curr_row < num_rows:
        curr_row += 1
        row = worksheet.row(curr_row)
        row = [str(x.value) for x in row]
        if row[0] != '':
            table.append(row)
        else:
            break
    '''
    reason_codes = {}
    curr_row += 2 #skip "Reason Codes" row
    while curr_row < num_rows:
        row = worksheet.row(curr_row)
        row = [str(x.value) for x in row]
        code, reason = row[0].split('- ')
        reason_codes[str(code)] = str(reason)
        curr_row += 1
    '''
    df = pd.DataFrame(table)
    df.columns = header
    df['Month'] = month
    df['Year'] = year
    return df
    #return df, reason_codes

def aggregate_data(workbook):
    workbook = xlrd.open_workbook('ONCOLOGY Report July2014.xlsx')
    worksheets = workbook.sheet_names()

    df_list = []
    for worksheet_name in worksheets:
        worksheet = workbook.sheet_by_name(worksheet_name)
        df = process_worksheet(worksheet)
        df_list.append(df)

    data = pd.concat(df_list, ignore_index=True)
    data.to_csv('Fingertip_agg.csv', index=False)

workbook_name = 'ONCOLOGY Report July2014.xlsx'
aggregate_data(workbook_name)

data = pd.read_csv('Fingertip_agg.csv')

plan_types = sorted(data['Plan Type'].unique())
plan_types.remove('HIX')
q = Queue.Queue()
for letter in string.lowercase:
    q.put(letter)


with open('FingertipFormulary_Overall.csv', 'wb') as f:
    csvwriter = csv.writer(f, delimiter=',')
    csvwriter.writerow(['Table 5%s. Available Fingertip Formulary Data for all years.'%(q.get())])
    csvwriter.writerow(['', 'Number of Plans'])
    all_counts = data['Plan Type'].value_counts()
    for plan_type in plan_types:
        csvwriter.writerow([plan_type, all_counts[plan_type]])

    for year, yearly_grp in data.groupby('Year'): 
        csvwriter.writerow([])
        csvwriter.writerow(['Table 5%s. Available Fingertip Formulary Data for %s.'%(q.get(), str(year))])
        csvwriter.writerow(['', 'Number of Plans'])
        yearly_counts = yearly_grp['Plan Type'].value_counts()
        for plan_type in plan_types:
            csvwriter.writerow([plan_type, yearly_counts[plan_type]])


def expand_state_var(data):
    # Expanding the state variable
    for state in states.values():
        data[state] = 'No' # defaulting to No

    for i, row in data.iterrows():
        if type(row['State(s) of Operation'])==str:
            states_list = row['State(s) of Operation'].split(',')
            if states_list[0] != '':
                for state in states_list:
                    state_abbrev = state.split()[0]
                    data.ix[i, states[state_abbrev]] = 'Yes'


pickle.dump(data, open('Fingertip_agg.p', 'wb'))
data.to_csv('Fingertip_agg.csv', index=False)



# Expanding the restrictions variable


def classify_tier(d, drug_data, i):
    if type(d)==str:
        if '(PA)' in d: 
            drug_data.ix[i, 'PA'] = 'Yes'

        if '(QL)' in d:
            drug_data.ix[i, 'QL'] = 'Yes'

        if '(ST)' in d:
            drug_data.ix[i, 'ST'] = 'Yes'

        if '(OR)' in d:
            drug_data.ix[i, 'OR'] = 'Yes'

        if 'Tier' in d:
            tier = d[5]
            drug_data.ix[i, 'Tier'] = tier

        elif 'NC' in d:
            drug_data.ix[i, 'Tier'] = 'NC'

        elif 'N/A' in d:
            drug_data.ix[i, 'Tier'] = 'N/A'

    elif np.isnan(d):
        drug_data.ix[i, 'Tier'] = 'N/A'


def filter_drug(data, drug_name):
    drug = data[['Health Plan', 'Plan Type', drug_name]]
    drug['PA'] = 'No'
    drug['QL'] = 'No'
    drug['ST'] = 'No'
    drug['OR'] = 'No'
    drug['Tier'] = 'N/A'

    for i, row in drug.iterrows():
        print i
        d = row[drug_name]
        classify_tier(d, drug, i)
        
    return drug

drug_name = 'Tarceva'
tarceva = filter_drug(data, 'Tarceva')
pickle.dump(tarceva, open('Fingertip_Tarceva.p', 'wb'))
tarceva.to_csv('Fingertip_Tarceva.csv', index=False)


def process_to_individual_drug(data):
    # Dictionary of drug datasets
    drug_map = {}
    drug_map['Gleevec'] = pd.DataFrame(data['Gleevec'])
    drug_map['Nexavar'] = pd.DataFrame(data['Nexavar'])
    drug_map['Revlimid'] = pd.DataFrame(data['Revlimid'])
    drug_map['Tykerb'] = pd.DataFrame(data['Tykerb'])
    drug_map['Zytiga'] = pd.DataFrame(data['Zytiga'])
    drug_map['Tarceva'] = pd.DataFrame(data['Tarceva'])
    print 'Starting instantiation'

    drug_names = drug_map.keys()
    # Instatiate new restriction and tier columns within each drug dataset
    for drug_data in drug_map.values(): 
        drug_data['PA'] = 'No'
        drug_data['QL'] = 'No'
        drug_data['ST'] = 'No'
        drug_data['OR'] = 'No'
        drug_data['Tier'] = 'N/A'

    print len(data)
    for i, row in data.iterrows():
        print i
        for drug_name in drug_names:
            classify_tier(row[drug_name], drug_map[drug_name], i)

    rest_of_data = data.ix[:,['Health Plan', 'Preferred Brand Tier', 'Provider', 'Plan Type', 'State(s) of Operation', 'Month', 'Year']]

    for drug_name, drug_data in drug_map.iteritems():
        drug_map[drug_name] = pd.concat([drug_data, rest_of_data], axis=1)
         
    return drug_map

'''
drug_map = process_to_individual_drug(data)
pickle.dump(drug_map, open('drug_map.p', 'wb'))

drug_name = 'Tarceva'
data = pd.read_csv(drug_name + '.csv')
'''




def instantiate_tiered_data():
    tiered_data = {}
    plans.append('All Plans')

    for year in years:
        tiered_data[year] = {}
        t_year = tiered_data[year]
        for plan in plans:
            t_year[plan] = {}
            t_plan = t_year[plan]
            for tier in tiers:
                t_plan[tier] = {}
                t_tier = t_plan[tier]
                for restriction in restrictions:
                    t_tier[restriction] = {}
                    t_restriction = t_tier[restriction]
                    for item in items:
                        t_restriction[item] = 0
    plans.pop()
    return tiered_data


def count_number_plans(data, tiered_data, year, plan, tier, restriction):
    num_plans = 0
    num_plans_sum = 0
    months = data.groupby('Month')
    num_months = 0 
    for month, month_grp in months:
        num_months += 1 
        num_plans_sum += len(month_grp)
    if num_months:
        num_plans = num_plans_sum/float(num_months)
    tiered_data[year][plan][tier][restriction]['Number of Plans'] = num_plans
    tiered_data[year]['All Plans'][tier][restriction]['Number of Plans'] += num_plans

def compute_tier_counts(data):
    tiered_data = instantiate_tiered_data()

    years_group = data.groupby(['Year'])
    
    for year, year_data in years_group: 
        print year
        plans_group = year_data.groupby(['Plan Type'])

        for plan, plan_data in plans_group:
            print plan
            tiers_group = plan_data.groupby(['Tier'])

            for tier, tier_data in tiers_group:
                print tier
                PA_only = tier_data.query("PA=='Yes' and QL=='No' and ST=='No' and OR=='No'")
                count_number_plans(PA_only, tiered_data, year, plan, tier, 'PA')

                PA_plus = tier_data.query("PA=='Yes' and (QL=='Yes' or ST=='Yes' or OR=='Yes')")
                count_number_plans(PA_plus, tiered_data, year, plan, tier, 'PA plus')

                Non_PA = tier_data.query("PA=='No' and (QL=='Yes' or ST=='Yes' or OR=='Yes')")
                count_number_plans(Non_PA, tiered_data, year, plan, tier, 'Non-PA')

                No_restrictions = tier_data.query("PA=='No' and (QL=='No' or ST=='No' or OR=='No')")
                count_number_plans(No_restrictions, tiered_data, year, plan, tier, 'No Restrictions')
    return tiered_data


def define_tier_labels(tiers_of_interest):
    tier_labels = ['']
    for x in tiers_of_interest:
        tier_labels.append('Tier ' + x)
        for i in xrange(3):
            tier_labels.append('')
    return tier_labels


def define_restriction_labels(tiers_of_interest, restrictions):
    restriction_labels = ['']
    for i in xrange(len(tiers_of_interest)):
        for restriction in restrictions:
            restriction_labels.append(restriction)
    return restriction_labels

def aggregate_plan_data(data, year, plan, item, tiers_of_interest):
    plan_data = [plan] 
    d = data[year][plan]
    for tier in tiers_of_interest:
        print tier
        for restriction in restrictions:
            print restriction
            plan_data.append(d[tier][restriction][item])
    return plan_data


def write_tiered_data(filename, tiered_data, item):
    years = sorted(data['Year'].unique())
    plans = sorted(data['Plan Type'].unique())
    '''
    tiers_of_interest = [str(x+1) for x in xrange(7)]
    tiers_of_interest.append('NC')
    '''
    tiers = sorted(tarceva['Tier'].unique())
    tiers_of_interest = tiers
    restrictions = ['PA only', 'PA plus', 'Non-PA', 'No Restrictions']
    items = ['Number of Plans']
    tier_labels = define_tier_labels(tiers_of_interest)
    restriction_labels = define_restriction_labels(tiers_of_interest, restrictions)        

    with open('%s.csv'%(filename), 'wb') as f:
        csvwriter = csv.writer(f, delimiter=',')
        for year in years:
            print year
            csvwriter.writerow([str(year)])
            csvwriter.writerow(tier_labels)
            csvwriter.writerow(restriction_labels)
            for plan in plans:
                print plan
                plan_data = aggregate_plan_data(tiered_data, year, plan, item, tiers_of_interest)
                csvwriter.writerow(plan_data)
            all_plans_sum = aggregate_plan_data(tiered_data, year, 'All Plans', item, tiers_of_interest)
            csvwriter.writerow(all_plans_sum)
            csvwriter.writerow([])


def write_drug_data(drug_map, drug_name=None):
    if drug_name==None:
        for drug_name, drug_data in drug_map.iteritems():
            data = drug_map[drug_name]
            counts = compute_tier_counts(data)
            filename = 'Fingertip_' + drug_name
            write_tiered_data(filename, counts, items[0])
    else:
        data = drug_map[drug_name]
        counts = compute_tier_counts(data)
        filename = 'Fingertip_' + drug_name
        write_tiered_data(filename, counts, items[0])
    return counts


tier_labels = define_tier_labels()
restriction_labels = define_restriction_labels()        
write_drug_data(drug_map, 'Tarceva')


write_tiered_data('Fingertip_Tarceva', counts_tarceva, 'Number of Plans')





tier_counts = defaultdict(int)
index = pd.Series()
entities_group = tarceva.groupby(['Health Plan', 'Year', 'Plan Type'])

for entity, entity_data in entities_group:
    print entity
    tier_count = len(entity_data['Tier'].unique())
    tier_counts[tier_count] += 1
    if tier_count > 1:
        index = index.append(pd.Series(entity_data.index))

index = pd.Series(index)
tiers_data = tarceva.ix[index]

multiple_tiers = tiers_data.groupby(['Health Plan', 'Year', 'Plan Type'])
tier_combos = defaultdict(int)

for entity, entity_data in multiple_tiers:
    tier_combo = sorted(entity_data['Tier'].unique())
    tier_combos[str(tier_combo)] += 1

















