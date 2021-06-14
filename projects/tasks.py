import json
import os
import shutil
from datetime import datetime
import logging
from projects.models import ResearchFolder, VaultFolder, VaultDataset, VaultStats, ResearchStats, Person, Datamanager, \
    MiscStats

DATADIR = '/home/peter/adminyoda/scripts/data'
logger = logging.getLogger(__name__)


def process_irods_stats():
    files = sorted(os.listdir(DATADIR))
    logger.info(f'listing of datadir: [{", ".join(files)}]')
    cnt = 0
    for file in files:
        if file.startswith('yodastats-'):
            cnt = cnt + 1
            logger.info(f'processing {file}')
            filedate_str = os.path.splitext(file)[0].split('-')[1]
            filedate = datetime.strptime(filedate_str, '%Y%m%d').date()
            with open(f'{DATADIR}/{file}', 'r') as fp:
                data = json.load(fp)
                MiscStats.objects.update_or_create(collected=filedate, defaults={
                    'size_total': data['misc']['size_total'],
                    'users_total': data['misc']['users_total'],
                    'internal_users_total': data['misc']['internal_users_total'],
                    'external_users_total': data['misc']['external_users_total'],
                    'revision_size': data['misc']['revision_size'],
                })
                for group in data['groups']:
                    if group.startswith('research-'):
                        logger.info(f'processing group {group} in {file}')
                        researchfolder, created = ResearchFolder.objects.get_or_create(yoda_name=group)
                        researchfolder.category = data['groups'][group]['category']
                        researchfolder.save()
                        vaultfolder, created = VaultFolder.objects.get_or_create(research_folder=researchfolder)
                        if created:
                            vaultfolder.yoda_name = researchfolder.yoda_name.replace('research-', 'vault-', 1)
                            vaultfolder.save()
                        for set in data['collections'][vaultfolder.yoda_name]['datasets']:
                            dataset, created = VaultDataset.objects.get_or_create(yoda_name=set,
                                                                                  vault_folder=vaultfolder)
                            dataset.status = data['collections'][vaultfolder.yoda_name]['datasets'][set]['status']
                            dataset.save()
                        vaultsize = data['collections'][vaultfolder.yoda_name]['size']
                        if vaultsize is None:
                            vaultsize = 0
                        researchsize = data['collections'][researchfolder.yoda_name]['size']
                        if researchsize is None:
                            researchsize = 0
                        VaultStats.objects.update_or_create(
                            vault_folder=vaultfolder,
                            collected=filedate,
                            defaults={'size': vaultsize})
                        print(f'{group} | {filedate} | {researchfolder.id} | {researchfolder.yoda_name}')
                        ResearchStats.objects.update_or_create(
                            research_folder=researchfolder,
                            collected=filedate,
                            defaults={'size': researchsize})
                    elif group.startswith('datamanager-'):
                        logger.info(f'processing datamanager group {group} in {file}')
                        for m in data['groups'][group]['members']:
                            if len(m) == 6:
                                u, created = Person.objects.get_or_create(vunetid=m)
                                u.save()
                                d, created = Datamanager.objects.get_or_create(user=u, yoda_name=group)
                                d.category = data['groups'][group]['category']
                                d.save()
            logger.info(f'move {file} to archived')
            shutil.move(f'{DATADIR}/{file}', f'{DATADIR}/archived/{file}')
    logger.info(f'{cnt} files processed')

process_irods_stats()