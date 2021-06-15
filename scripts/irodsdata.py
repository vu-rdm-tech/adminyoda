import os
import ssl
from irods.column import Like
from irods.models import Collection, DataObject
from irods.session import iRODSSession
import irods.exception
from config import SURF_PRE
import logging

logger = logging.getLogger('irods_tasks')


def handle_exception():
    logger.warning('script failed with an error')
    raise SystemExit(0)


class IrodsData():
    def __init__(self):
        self.data = {'collections': {}, 'groups': []}
        self.session = self._get_session()

    def collect(self):
        try:
            self.data['collections'] = self.get_home_collections()
            self.data['groups'] = self.get_groups()
            total_size = 0
            for path in self.data['collections']:
                self.data['collections'][path] = self.get_stats(path=path)
                if not self.data['collections'][path]['size'] is None:
                    total_size = total_size + self.data['collections'][path]['size']

            self.data['misc'] = {}
            self.data['misc']['size_total'] = total_size
            
            public_internal, public_external = self.get_member_count('public')
            self.data['misc']['internal_public_users_total'] = public_internal
            self.data['misc']['external_public_users_total'] = public_external
            self.data['misc']['public_users_total'] = public_internal + public_external

            self.data['misc']['revision_size'] = self.get_revision_size()
            self.data['misc']['trash_size'] = self.get_trash_size()
            
            research_group_members=[]
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
        except:
            logger.error('could not get collections and groups, probably an authentication error')
            handle_exception()
        return self.data


    def _get_session(self):
        try:
            env_file = os.environ['IRODS_ENVIRONMENT_FILE']
        except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
        ssl_settings = {'ssl_context': ssl_context}
        return iRODSSession(irods_env_file=env_file, **ssl_settings)

    def get_home_collections(self):
        collections = {}
        coll = self.session.collections.get(f'/{SURF_PRE["zone"]}/home')
        for col in coll.subcollections:
            collections[col.name] = {}
        return collections

    def get_member_count(self, group_name):
        internal = 0
        external = 0
        for user in self.session.user_groups.get(group_name).members:
            if ("@" in user.name) and ("@vu.nl" not in user.name):
                external += 1
            else:
                internal += 1
        return internal, external

    def get_revision_size(self):
        size, cnt = self.query_collection_stats(f'/{SURF_PRE["zone"]}/yoda/revisions')
        return size

    def get_trash_size(self):
        size, cnt = self.query_collection_stats(f'/{SURF_PRE["zone"]}/trash')
        return size

    def get_groups(self):
        groups = {}
        for path in self.data['collections']:
            if path.startswith('research-') or path.startswith('datamanager-'):
                groupname = path
                groups[groupname] = {}
                group_obj = self.session.user_groups.get(groupname)
                groups[groupname]['category'] = group_obj.metadata.get_one('category').value
                member_names = [user.name for user in group_obj.members]
                groups[groupname]['members'] = member_names
                groups[groupname]['read_members'] = []
                if path.startswith('research-'):
                    read_group_obj = self.session.user_groups.get(groupname.replace('research-', 'read-'))
                    read_member_names = [user.name for user in read_group_obj.members]
                    groups[groupname]['read_members'] = read_member_names
        return groups

    def query_collection_stats(self, full_path):
        query = self.session.query(DataObject.size).filter(Like(Collection.name, f'{full_path}%')).count(
            DataObject.id).sum(DataObject.size)
        result = next(iter(query))  # only one result
        return result[DataObject.size], result[DataObject.id]

    def get_stats(self, path):
        stats = {}
        stats['size'], stats['count'] = self.query_collection_stats(full_path=f'/{SURF_PRE["zone"]}/home/{path}')
        if path.startswith('vault-'):
            stats['datasets'] = {}
            coll = self.session.collections.get(f'/{SURF_PRE["zone"]}/home/{path}')
            for col in coll.subcollections:  # datasets
                dataset = col.name
                stats['datasets'][dataset] = {}
                stats['datasets'][dataset]['size'], stats['datasets'][dataset]['count'] = self.query_collection_stats(
                    full_path=f'/{SURF_PRE["zone"]}/home/{path}/{dataset}%')
                status = col.metadata.get_one('org_vault_status').value
                stats['datasets'][dataset]['status'] = status
                if status in ['PUBLISHED', 'DEPUBLISHED']:
                    stats['datasets'][dataset]['landingPageUrl'] = col.metadata.get_one(
                        'org_publication_landingPageUrl').value
        return stats
