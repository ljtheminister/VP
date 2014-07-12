import pandas as pd
import numpy as np
from collections import defaultdict
from decimal import Decimal

data = pd.read_csv('Raw Data File for Business One.csv')

data['copay'] = data['Avg_Wt_Copay'].apply(lambda x: 0 if x=='-' else Decimal(x.strip('$')))

# Life count by channel
all_years = {}
channel_data = data.groupby('Channel')
for channel, channel_grp in channel_data:
    all_lives = 0
    rx_lives = 0 
    entities = channel_grp.groupby(['Entity_Name', 'Period_Year'])
    for entity, entity_grp in entities:
        all_lives += entity_grp['Total_Lives'].mean()
        rx_lives += entity_grp['Total_Lives_Rx'].mean()
    all_years[channel] = (all_lives, rx_lives)


# Life count by channel/year
yearly = {}
grouped_data = data.groupby(['Period_Year', 'Channel'])
for channel_year, group in grouped_data:
    all_lives = 0
    rx_lives = 0
    entities = group.groupby(['Entity_Name'])
    for entity, entity_grp in entities:
        all_lives += entity_grp['Total_Lives'].mean()
        rx_lives += entity_grp['Total_Lives_Rx'].mean()
    yearly[channel_year] = (all_lives, rx_lives) 
    

'''
Do I have to clean-up the tier data?
'''


def compute_lives(data, all_dict, rx_dict, key1, key2):
    all_lives = 0
    rx_lives = 0
    entities = data.groupby('Entity_Name')
    for entity, entity_grp in entities:
        all_lives += entity_grp['Total_Lives'].mean()
        rx_lives += entity_grp['Total_Lives_Rx'].mean()
    all_dict[key1][key2] = all_lives
    rx_dict[key1][key2] = rx_lives
 

def compute_lives_copay(data, all_dict, rx_dict, copay_dict, key1, key2):
    all_lives = 0
    rx_lives = 0
    copay = 0
    entities = data.groupby('Entity_Name')
    for entity, entity_grp in entities:
        all_lives += entity_grp['Total_Lives'].mean()
        rx_lives += entity_grp['Total_Lives_Rx'].mean()
        rx_lives_sum = entity_grp['Total_Lives_Rx'].sum()
        if rx_lives_sum == 0:
            pass
        else:
            copay += (entity_grp.copay * entity_grp.Total_Lives_Rx).mean()/rx_lives_sum
    all_dict[key1][key2] = all_lives
    rx_dict[key1][key2] = rx_lives
    copay_dict[key1][key2] = copay

all_lives_tier = defaultdict(dict)
rx_lives_tier = defaultdict(dict)
avg_copay = defaultdict(dict)

for channel_year, group in grouped_data:
    print channel_year
    tiers = group.groupby(['Form_Status'])
    for tier, tier_data in tiers:
        print tier
        PA_only = tier_data.query("Restrict_PA=='Y'")
        compute_lives_copay(PA_only, all_lives_tier, rx_lives_tier, avg_copay, channel_year, 'PA_only')
        PA_plus = tier_data.query("Restrict_PA=='Y' and (Restrict_SE=='Y' or Restrict_QL=='Y' or Restrict_AR=='Y')")
        compute_lives_copay(PA_plus, all_lives_tier, rx_lives_tier, avg_copay, channel_year, 'PA_plus')
        Non_PA = tier_data.query("Restrict_PA=='-' and (Restrict_SE=='Y' or Restrict_QL=='Y' or Restrict_AR=='Y')")
        compute_lives_copay(Non_PA, all_lives_tier, rx_lives_tier, avg_copay, channel_year, 'Non_PA')


'''
sub = data.query("Channel=='Commercial' and Form_Status=='Tier 2' and Restrict_PA=='Y'")
group = grouped_data.get_group((2010, 'Commercial'))
tiers = group.groupby(['Form_Status'])
tier_data = tiers.get_group('Tier 2')
for i, row in Non_PA[['Restrict_PA', 'Restrict_SE', 'Restrict_QL', 'Restrict_AR']].iterrows():
    print row
#PA_plus[['Restrict_PA', 'Restrict_SE', 'Restrict_QL', 'Restrict_AR']]
'''
