import logging
import os
from datetime import datetime
import json
from irodsdata import IrodsData

today = datetime.now()
today_str = today.strftime('%Y%m%d')

def setup_logging():
    LOGFILE = '/home/peter/adminyoda/scripts/log/adminyoda-tasks.log'
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
    filename = f'yodastats-{today_str}.json'

    stats_file = f'{datadir}/{filename}'
    archived_stats_file = f'{datadir}/archived/{filename}'

    irodsdata = IrodsData()
    irodsdata.logger=logger
    logger.info(f'start script {os.path.realpath(__file__)}')
    if os.path.exists(stats_file):
        logger.info(f'stats already collected in {stats_file}')
    elif os.path.exists(archived_stats_file):
        logger.info(f'stats already collected and processed from {archived_stats_file}')
    else:
        logger.info('start data collection')
        data=irodsdata.collect()
        logger.info(f'write stats to {stats_file}')
        with open(stats_file, 'w') as fp:
            json.dump(data, fp)
    logger.info('script finished')

logger = setup_logging()
collect()