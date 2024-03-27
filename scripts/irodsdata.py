from irods.column import Like
from irods.models import Collection, DataObject
import logging
from datetime import datetime
from setup_session import setup_session

logger = logging.getLogger('irods_tasks')


def handle_exception():
    logger.warning('script failed with an error')
    raise SystemExit(0)


class IrodsData():
    def __init__(self):
        self.session = None
        self.data = {'collections': {}, 'groups': []}

    def collect(self):
        self.data['collections'] = self.get_home_collections()
        self.data['groups'] = self.get_groups()

        total_size = 0
        for path in self.data['collections']:
            self.data['collections'][path] = self.get_stats(path=path)
            total_size = total_size + self.data['collections'][path]['size']

        self.data['revision_collections'] = self.get_revision_collections()
        for path in self.data['revision_collections']:
            self.data['revision_collections'][path] = self.get_stats(path=path, root='yoda/revisions')
            # total_size = total_size + self.data['collections'][path]['size']

        self.data['misc'] = {}
        self.data['misc']['size_total'] = total_size

        public_internal, public_external = self.get_member_count('public')
        self.data['misc']['internal_public_users_total'] = public_internal
        self.data['misc']['external_public_users_total'] = public_external
        self.data['misc']['public_users_total'] = public_internal + public_external

        self.data['misc']['revision_size'] = self.get_revision_size()
        self.data['misc']['trash_size'] = self.get_trash_size()

        research_group_members = []
        for g in self.data['groups']:
            research_group_members = list(set(research_group_members + self.data['groups'][g]['members']))
            research_group_members = list(set(research_group_members + self.data['groups'][g]['read_members']))
        internal = 0
        external = 0
        for name in research_group_members:
            if ("@" in name) and ("@vu.nl" not in name):
                external += 1
            else:
                internal += 1
        self.data['misc']['internal_users_total'] = internal
        self.data['misc']['external_users_total'] = external
        self.data['misc']['users_total'] = internal + external
        return self.data

    def close_session(self):
        self.session.cleanup()
        self.session = None
        logger.info('irods session closed')

    def get_session(self):
        try:
            logger.info('setup irods session')
            self.session = setup_session()
            self.get_home_collections()  # try once to see if we are logged in
        except:
            logger.error('could not get collections and groups, probably an authentication error')
            handle_exception()
        return True

    def get_home_collections(self):
        collections = {}
        coll = self.session.collections.get(f'/{self.session.zone}/home')
        for col in coll.subcollections:
            collections[col.name] = {}
        return collections

    def get_revision_collections(self):
        collections = {}
        coll = self.session.collections.get(f'/{self.session.zone}/yoda/revisions')
        for col in coll.subcollections:
            collections[col.name] = {}
        return collections

    def get_member_count(self, group_name):
        internal = 0
        external = 0
        for user in self.session.user_groups.get(group_name).members:
            if user.name.endswith(("vu.nl", "acta.nl")):
                internal += 1
            else:
                external += 1
        return internal, external

    def get_revision_size(self):
        size, cnt = self.query_collection_stats(f'/{self.session.zone}/yoda/revisions')
        return size

    def get_trash_size(self):
        size, cnt = self.query_collection_stats(f'/{self.session.zone}/trash')
        return size

    def get_groups(self):
        groups = {}
        for path in self.data['collections']:
            if path.startswith('research-') or path.startswith('datamanager-'):
                groupname = path
                groups[groupname] = {}
                group_obj = self.session.user_groups.get(groupname)
                groups[groupname]['category'] = group_obj.metadata.get_one('category').value
                try:
                    groups[groupname]['data_classification'] = group_obj.metadata.get_one('data_classification').value
                except:
                    groups[groupname]['data_classification'] = "NA"
                member_names = [user.name for user in group_obj.members]
                groups[groupname]['members'] = member_names
                groups[groupname]['read_members'] = []
                if path.startswith('research-'):
                    read_group_obj = self.session.user_groups.get(groupname.replace('research-', 'read-', 1))
                    read_member_names = [user.name for user in read_group_obj.members]
                    groups[groupname]['read_members'] = read_member_names
        return groups

    def query_collection_stats(self, full_path):
        query = self.session.query(DataObject.size).filter(Like(Collection.name, f'{full_path}%')).count(
            DataObject.id).sum(DataObject.size)
        result = next(iter(query))  # only one result
        size = result[DataObject.size]
        if size is None: size = 0
        return size, result[DataObject.id]

    def query_collection_newest(self, full_path):
        query = self.session.query(DataObject.name, DataObject.create_time).filter(
            Like(Collection.name, f'{full_path}%')).order_by(DataObject.create_time, order='desc').first()
        try:
            newest=query[DataObject.create_time]
        except:
            newest=datetime(1970, 1, 1)
        return newest.isoformat()

    def get_stats(self, path, root='home'):
        stats = {}
        stats['size'], stats['count'] = self.query_collection_stats(full_path=f'/{self.session.zone}/{root}/{path}')
        stats['newest'] = self.query_collection_newest(full_path=f'/{self.session.zone}/{root}/{path}')
        if path.startswith('vault-'):
            stats['datasets'] = {}
            coll = self.session.collections.get(f'/{self.session.zone}/{root}/{path}')
            for col in coll.subcollections:  # datasets
                dataset = col.name
                stats['datasets'][dataset] = {}
                stats['datasets'][dataset]['size'], stats['datasets'][dataset]['count'] = self.query_collection_stats(
                    full_path=f'/{self.session.zone}/{root}/{path}/{dataset}%')
                try:
                    status = col.metadata.get_one(
                        'org_vault_status').value  # won't be set on status "approved for publication"
                except:
                    status = ''
                if status in ['PUBLISHED', 'DEPUBLISHED']:
                    try:
                        stats['datasets'][dataset]['landingPageUrl'] = col.metadata.get_one(
                            'org_publication_landingPageUrl').value
                    except:
                        stats['datasets'][dataset]['landingPageUrl'] = ''
                    try:
                        stats['datasets'][dataset]['doi'] = col.metadata.get_one('org_publication_versionDOI').value
                    except:
                        stats['datasets'][dataset]['doi'] = ''
                    try:
                        stats['datasets'][dataset]['publication_date'] = col.metadata.get_one(
                            'org_publication_publicationDate').value   
                    except:	
                        stats['datasets'][dataset]['publication_date'] = ''
                stats['datasets'][dataset]['status'] = status
                try:
                    retention_period = col.metadata.get_one('Retention_Period').value
                except:
                    retention_period = '0'
                stats['datasets'][dataset]['retention_period'] = retention_period
                try:
                    data_classification = col.metadata.get_one('Data_Classification').value
                except:
                    data_classification = ''
                stats['datasets'][dataset]['data_classification'] = data_classification
                try:
                    data_access_rights = col.metadata.get_one('org_publication_accessRestriction').value
                except:
                    data_access_rights = ''
        return stats
