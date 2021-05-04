import logging
import os
import ssl
from datetime import datetime
import json
from irods.column import Criterion, Like
from irods.models import Collection, DataObject
from irods.session import iRODSSession
from config import YODATEST, AIMMS, SURF, SURF_PRE, MAIL_TO, MAIL_FROM, SMTP_HOST

today = datetime.now()
today_str = today.strftime('%Y%m%d')

def setup_logging():
    LOGFILE = 'adminyoda-tasks-%s.log' % (today_str)
    logger = logging.getLogger('irods_tasks')
    hdlr = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger

def get_collections(connection):
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
    ssl_settings = {'ssl_context': ssl_context}
    data={}
    with iRODSSession(irods_env_file=env_file, **ssl_settings) as session:
        coll=session.collections.get(f'/{connection["zone"]}/home')
        for col in coll.subcollections:
           data[col.name]={}
    return data

def get_sizes(data):
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
    ssl_settings = {'ssl_context': ssl_context}
    with iRODSSession(irods_env_file=env_file, **ssl_settings) as session:
        for path in data:
            print(path)
            query=session.query(DataObject.size).filter(Like(Collection.name, f'/{SURF_PRE["zone"]}/home/{path}%')).count(DataObject.id).sum(DataObject.size)
            result=next(iter(query)) # only one result
            data[path]['size']=result[DataObject.size]
            data[path]['count']=result[DataObject.id]
    return data
logger=setup_logging()

statsfile=f'collections-{today_str}.json'
if os.path.exists(statsfile):
   with open(statsfile, 'r') as fp:
        data=json.load(fp)
else:
    data=get_collections(SURF_PRE)
    data=get_sizes(data)
    with open(statsfile, 'w') as fp:
        json.dump(data, fp)

print(data)

# TODO: get collection category from metadata
# TODO: get vault datasets (one down)
"""
Write a json file like below to a dir. 
On Django schedule a task which periodically picks up the json file and writes everything to the database.
That way the Django web application and the irods functionality can stay completely decoupled. 
{
    datamanager: {
        datamanager-aimms: {
            category: 'aimms',
            managers: ['pvs220']
        },
        datamanager-clue: {
            category: 'clue',
            managers: []
        }
    },
    research: {
        research-folder1: {
            size: 1234,
            count: 1234,
            category: 'aimms'
        },
        research-folder2: {
            size: 1234,
            count: 1234,
            category: 'clue'
        }
    },
    vault: {
        vault-folder1: {
            size: 1234,
            count: 1234,
            datasets: [{
                name: somedataset[1322434],
                size: 1243,
                count: 1233,
                published: false
            },
            {
                name: someotherdataset[13224334],
                size: 1243,
                count: 1233,
                published: true,
                doi: 1234/132132134,
                yoda_id: TYM897
            }],
        },
        vault-folder2: {
            size: 0,
            count: 0,
            datasets: []
        }
    } 
}
"""