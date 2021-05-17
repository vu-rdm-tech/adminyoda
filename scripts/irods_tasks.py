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


def get_session():
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
    ssl_settings = {'ssl_context': ssl_context}
    return iRODSSession(irods_env_file=env_file, **ssl_settings)


def get_collections(session, data):
    coll = session.collections.get(f'/{SURF_PRE["zone"]}/home')
    for col in coll.subcollections:
        data['collections'][col.name] = {}
    return data


def get_research_groups(session, data):
    groups = {}
    for path in data['collections']:
        if path.startswith('research-') or path.startswith('datamanager-'):
            groupname = path
            groups[groupname] = {}
            group_obj = session.user_groups.get(groupname)
            groups[groupname]['category'] = group_obj.metadata.get_one('category').value
            member_names = [user.name for user in group_obj.members]
            groups[groupname]['members'] = member_names
    data['groups'] = groups
    return data


def get_sizes(session, data):
    for path in data['collections']:
        query = session.query(DataObject.size).filter(Like(Collection.name, f'/{SURF_PRE["zone"]}/home/{path}%')).count(
            DataObject.id).sum(DataObject.size)
        result = next(iter(query))  # only one result
        data['collections'][path]['size'] = result[DataObject.size]
        data['collections'][path]['count'] = result[DataObject.id]
    return data


def get_datasets(session, data):
    for path in data['collections']:
        if path.startswith('vault-'):
            data['collections'][path]['datasets'] = {}
            coll = session.collections.get(f'/{SURF_PRE["zone"]}/home/{path}')
            for col in coll.subcollections:  # datasets
                dataset = col.name
                data['collections'][path]['datasets'][dataset] = {}
                query = session.query(DataObject.size).filter(
                    Like(Collection.name, f'/{SURF_PRE["zone"]}/home/{path}/{dataset}%')).count(
                    DataObject.id).sum(DataObject.size)
                result = next(iter(query))  # only one result
                data['collections'][path]['datasets'][dataset]['size'] = result[DataObject.size]
                data['collections'][path]['datasets'][dataset]['count'] = result[DataObject.id]
                status = col.metadata.get_one('org_vault_status').value
                data['collections'][path]['datasets'][dataset]['status'] = status
                if status in ['PUBLISHED', 'DEPUBLISHED']:
                    data['collections'][path]['datasets'][dataset]['landingPageUrl'] = col.metadata.get_one(
                        'org_publication_landingPageUrl').value
    return data


logger = setup_logging()
statsfile = f'collections-{today_str}.json'
irods_session = get_session()
if os.path.exists(statsfile):
    with open(statsfile, 'r') as fp:
        data = json.load(fp)
else:
    data = {'collections': {}, 'groups': []}
    data = get_collections(irods_session, data)
    data = get_sizes(irods_session, data)
    data = get_research_groups(irods_session, data)
    data = get_datasets(irods_session, data)
    with open(statsfile, 'w') as fp:
        json.dump(data, fp)

# print(data)
