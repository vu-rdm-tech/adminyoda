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
    for group in data['groups']:
        
        if len(data['groups'][group]['read_members'])>0:
            print(group, len(data['groups'][group]['read_members']))


