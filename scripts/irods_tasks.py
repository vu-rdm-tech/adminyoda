import logging
import os
from datetime import datetime
import json
from irodsdata import IrodsData

today = datetime.now()
today_str = today.strftime('%Y%m%d')
year = today.strftime('%Y')
week = today.strftime('%U')

def setup_logging():
    LOGFILE = f'/home/peter/adminyoda/scripts/log/adminyoda-tasks_{today.year}{today.strftime("%m")}.log'
    logger = logging.getLogger('irods_tasks')
    hdlr = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger

def collect():
    datadir = '/home/peter/adminyoda/scripts/data'
    filename = f'yodastats-{year}{week}.json'

    stats_file = f'{datadir}/{filename}'
    archived_stats_file = f'{datadir}/archived/{filename}'

    logger.info(f'start script {os.path.realpath(__file__)}')
    if os.path.exists(stats_file):
        logger.info(f'stats already collected in {stats_file}')
    elif os.path.exists(archived_stats_file):
        logger.info(f'stats already collected and processed from {archived_stats_file}')
    else:
        irodsdata = IrodsData()
        irodsdata.logger=logger
        logger.info('start data collection')
        data=irodsdata.collect()
        data['collected'] = today_str
        logger.info(f'write stats to {stats_file}')
        with open(stats_file, 'w') as fp:
            json.dump(data, fp)
    logger.info('script finished')

logger = setup_logging()
collect()