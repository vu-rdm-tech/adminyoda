import json
import os
import shutil
from datetime import datetime, timedelta
import logging
from projects.models import ResearchFolder, VaultFolder, VaultDataset, VaultStats, ResearchStats, Person, Datamanager, \
    MiscStats
from django.utils.timezone import now, make_aware

DATADIR = '/home/peter/adminyoda/scripts/data'
logger = logging.getLogger(__name__)

# don't forget to 'sudo systemctl restart qcluster' when code here is changed

def cleanup():
    days=2
    last_update = MiscStats.objects.order_by('collected').last().collected
    cutoff=make_aware(datetime.combine(last_update, datetime.min.time())) - timedelta(days=days)
    logger.info(f'Mark folders and datasets last updated before {cutoff} as deleted.')
    ResearchFolder.objects.filter(updated__lte=cutoff).update(deleted=now())
    VaultFolder.objects.filter(updated__lte=cutoff).update(deleted=now())
    VaultDataset.objects.filter(updated__lte=cutoff).update(deleted=now())


def process_irods_stats():
    files = sorted(os.listdir(DATADIR))
    logger.info(f'listing of datadir: [{", ".join(files)}]')
    cnt = 0
    for file in files:
        if file.startswith('yodastats-'):
            cnt = cnt + 1
            logger.info(f'processing {file}')
            with open(f'{DATADIR}/{file}', 'r') as fp:
                data = json.load(fp)
                if data['collected'] is None:
                    # old style
                    filedate_str = os.path.splitext(file)[0].split('-')[1]
                else:
                    filedate_str = data['collected']
                filedate = datetime.strptime(filedate_str, '%Y%m%d').date()
                researchgroup_cnt = 0
                dataset_cnt = 0
                published_cnt = 0
                research_size_total = 0
                vault_size_total = 0
                for group in data['groups']:
                    if group.startswith('research-'):
                        logger.info(f'processing group {group} in {file}')
                        researchgroup_cnt += 1
                        researchfolder, created = ResearchFolder.objects.get_or_create(yoda_name=group)
                        researchfolder.category = data['groups'][group]['category']
                        researchfolder.save()

                        vaultfolder, created = VaultFolder.objects.get_or_create(research_folder=researchfolder)
                        if created:
                            vaultfolder.yoda_name = researchfolder.yoda_name.replace('research-', 'vault-', 1)
                            vaultfolder.save()

                        for set in data['collections'][vaultfolder.yoda_name]['datasets']:
                            dataset_cnt += 1
                            dataset, created = VaultDataset.objects.get_or_create(yoda_name=set,
                                                                                  vault_folder=vaultfolder)
                            dataset.status = data['collections'][vaultfolder.yoda_name]['datasets'][set]['status']
                            if dataset.status == 'PUBLISHED':
                                published_cnt += 1
                            dataset.save()

                        researchsize = data['collections'][researchfolder.yoda_name]['size']
                        ResearchStats.objects.update_or_create(
                            research_folder=researchfolder,
                            collected=filedate,
                            defaults={'size': researchsize})
                        research_size_total += researchsize

                        vaultsize = data['collections'][vaultfolder.yoda_name]['size']
                        VaultStats.objects.update_or_create(
                            vault_folder=vaultfolder,
                            collected=filedate,
                            defaults={'size': vaultsize})
                        vault_size_total += vaultsize

                    elif group.startswith('datamanager-'):
                        logger.info(f'processing datamanager group {group} in {file}')
                        for m in data['groups'][group]['members']:
                            if len(m) == 6:
                                u, created = Person.objects.get_or_create(vunetid=m)
                                u.save()
                                d, created = Datamanager.objects.get_or_create(user=u, yoda_name=group)
                                d.category = data['groups'][group]['category']
                                d.save()

                MiscStats.objects.update_or_create(collected=filedate, defaults={
                    'size_total': data['misc']['size_total'],
                    'size_research': research_size_total,
                    'size_vault': vault_size_total,
                    'users_total': data['misc']['users_total'],
                    'internal_users_total': data['misc']['internal_users_total'],
                    'external_users_total': data['misc']['external_users_total'],
                    'revision_size': data['misc']['revision_size'],
                    'trash_size': data['misc']['trash_size'],
                    'groups_total': researchgroup_cnt,
                    'datasets_total': dataset_cnt,
                    'published_total': published_cnt,
                })

            logger.info(f'move {file} to archived')
            shutil.move(f'{DATADIR}/{file}', f'{DATADIR}/archived/{file}')

    logger.info(f'{cnt} files processed')

# process_irods_stats()
# cleanup()
