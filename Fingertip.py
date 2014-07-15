import pandas as pd
import numpy as np
import openpyxl
import xlrd
import csv
import string
import Queue
import cPickle as pickle

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


def classify_tier(d, drug_data):
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
        classify_tier(d, drug)
        
    return drug

drug_name = 'Tarceva'
tarceva = filter_drug(data, 'Tarceva')
pickle.dump(tarceva, open('Fingertip_Tarceva.p', 'wb'))
tarceva.to_csv('Fingertip_Tarceva.csv', index=False)


def process_to_individual_drug(data):
# Dictionary of drug datasets
drug_map = {}
drug_map['Gleevec'] = data['Gleevec']
drug_map['Nexavar'] = data['Nexavar']
drug_map['Revlimid'] = data['Revlimid']
drug_map['Tykerb'] = data['Tykerb']
drug_map['Zytiga'] = data['Zytiga']
drug_map['Tarceva'] = data['Tarceva']

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
        classify_tier(row[drug_name], drug_map[drug_name])

rest_of_data = data.ix[['Health Plan', 'Provider', 'Plan Type', 'State(s) of Operation']]

for drug_data in drug_data.values():
    drug_data = pd.concat([drug_data, rest_of_data], axis=1)

return drug_map


drug_map = process_to_individual_drug(data)
pickle.dump(drug_map, open('drug_map.p', 'rb'))





























































