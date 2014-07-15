import pandas as pd
import numpy as np

import openpyxl
import xlrd


workbook = xlrd.open_workbook('ONCOLOGY Report July2014.xlsx')

print data.sheet_names()

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
    '''
    if worksheet.name == 'July2014':
        curr_row = 9
        header = worksheet.row(curr_row)
        header = [str(x.value) for x in header]
    else:
    '''
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


df_list = []

worksheets = workbook.sheet_names()
for worksheet_name in worksheets:
    worksheet = workbook.sheet_by_name(worksheet_name)
    df = process_worksheet(worksheet)
    df_list.append(df)

data = pd.concat(df_list, ignore_index=True)
data.to_csv('Fingertip_agg.csv', index=False)


data = pd.read_csv('Fingertip_agg.csv')
data['Plan Type'].value_counts()

for year, grp in data.groupby('Year'):
    print year
    print grp['Plan Type'].value_counts()




for state in states.values():
    data[state] = 'No'

for i, row in data.iterrows():
    print i
    states_list = row['State(s) of Operation'].split(',')
    if states_list[0] != '':
        for state in states_list:
            state_abbrev = state.split()[0]
            data[states[state_abbrev]] = 'Yes'
    else:
        pass




drug['PA'] = 'No'
drug['QL'] = 'No'
drug['ST'] = 'No'
drug['OR'] = 'No'




drug_name = 'Tarceva'

def filter_drug(data, drug_name):
    drug = data[['Health Plan', 'Plan Type', drug_name]]
    print len(drug)
    drug['PA'] = 'No'
    drug['QL'] = 'No'
    drug['ST'] = 'No'
    drug['OR'] = 'No'
    drug['Tier'] = np.nan

    for i, row in drug.iterrows():
        print i
        d = row[drug_name]

        if '(PA)' in d: 
            drug.loc[i, 'PA'] = 'Yes'

        if '(QL)' in d:
            drug.loc[i, 'QL'] = 'Yes'

        if '(ST)' in d:
            drug.loc[i, 'ST'] = 'Yes'

        if '(OR)' in d:
            drug.loc[i, 'OR'] = 'Yes'

        if 'Tier' in d:
            tier = d[5]
            drug.loc[i, 'Tier'] = tier
        elif 'NC' in d:
            drug.loc[i, 'Tier'] = 'NC'

        elif 'N/A' in d:
            drug.loc[i, 'Tier'] = 'N/A'

    return drug

tarceva = filter_drug(data, 'Tarceva')

tarceva.to_csv('Fingertip_Tarceva.csv', index=False)















tarceva = 














































