import os
import ssl
from irods.column import Like
from irods.models import Collection, DataObject
from irods.session import iRODSSession
import irods.exception
from config import YODATEST, AIMMS, SURF, SURF_PRE, MAIL_TO, MAIL_FROM, SMTP_HOST
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
            self.data['misc']['users_total'] = self.get_user_count()
            self.data['misc']['revision_size'] = self.get_revision_size()
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

    def get_user_count(self):
        return len(self.session.user_groups.get('public').members)

    def get_revision_size(self):
        size, cnt = self.query_collection_stats(f'/{SURF_PRE["zone"]}/yoda/revisions')
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
