from irods.column import Like
from irods.models import Collection, DataObject
from setup_session import setup_session

# loop through all vault subfolders and get metadata json from root
# or do a query for files called metadata.json

def get_home_collections(session):
    collections = {}
    coll = session.collections.get(f'/{session.zone}/home')
    for col in coll.subcollections:
        collections[col.name] = {}
    return collections


irods_session = setup_session()
home_collections = get_home_collections(irods_session)  # try once to see if we are logged in

for home_collection in home_collections:
    if home_collection.startswith('vault-'):
        coll = irods_session.collections.get(f'/{irods_session.zone}/home/{home_collection}')
        for dataset_collection in coll.subcollections:  # datasets
            print(dataset_collection.name)
        


irods_session.cleanup()