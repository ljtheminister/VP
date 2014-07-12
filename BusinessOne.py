import pandas as pd
import numpy as np

data = pd.read_csv('Raw Data File for Business One.csv')

channel_data = data.groupby('Channel')



all_years = {}

for channel, channel_grp in channel_data:
    all_lives = 0
    rx_lives = 0 
    entities = channel_grp.groupby(['Entity_Name', 'Period_Year'])
    for entity, entity_grp in entities:
        all_lives += entity_grp['Total_Lives'].mean()
        rx_lives += entity_grp['Total_Lives_Rx'].mean()
    all_years[channel] = (all_lives, rx_lives)



yearly = {}

grouped_data = data.groupby(['Period_Year', 'Channel']

for channel_year, group in grouped_data:
    all_lives = 0
    rx_lives = 0
    entities = group.groupby(['Entity_Name'])
    for entity, entity_grp in entities:
        all_lives += entity_grp['Total_Lives'].mean()
        rx_lives += entity_grp['Total_Lives_Rx'].mean()
    yearly[channel_year] = (all_lives, rx_lives) 
    















