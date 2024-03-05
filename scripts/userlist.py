import json
import pandas as pd
from datetime import datetime
import os, glob

def find_newest_json(directory):
    print(directory)
    list_of_files = glob.glob(f'{directory}/*')  # get list of all json files
    print(list_of_files)
    if not list_of_files:  # if list is empty, return None
        return None
    latest_file = max(list_of_files, key=os.path.getctime)  # find the latest file
    return latest_file


latest_file = find_newest_json('data/archived')
print(latest_file)
with open(latest_file, 'r') as fp:
    data = json.load(fp)
    list={'member': [], 'domain':[]}
    for group in data['groups']:
        for member in data['groups'][group]['members']:
           if member not in list['member'] and '@' in member:
               print(member)
               list['domain'].append(member.split("@",1)[1])
               list['member'].append(member)
        for member in data['groups'][group]['read_members']:
           if member not in list['member'] and '@' in member:
               list['domain'].append(member.split("@",1)[1])
               list['member'].append(member)


for member in list:
    print(member)


today = datetime.now()
filename = f'users_{today.strftime("%U")}.xlsx'
writer = pd.ExcelWriter(filename, engine="xlsxwriter")
dfg = pd.DataFrame.from_dict(data=list)
dfg.to_excel(writer, sheet_name="general", index=False)

writer.close()