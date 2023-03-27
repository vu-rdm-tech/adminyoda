from config import DATA_DIR
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
    LOGFILE = f'{DATA_DIR}log/adminyoda-tasks_{today.year}{today.strftime("%m")}.log'
    logger = logging.getLogger('irods_tasks')
    hdlr = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger

def collect():
    filename = f'yodastats-{year}{week}.json'
    stats_file = f'{DATA_DIR}data/{filename}'
    archived_stats_file = f'{DATA_DIR}data/archived/{filename}'
    irodsdata = IrodsData()
    logger.info(f'start script {os.path.realpath(__file__)}')
    irodsdata.logger = logger
    irodsdata.get_session()
    if os.path.exists(stats_file):
        logger.info(f'stats already collected in {stats_file}')
    elif os.path.exists(archived_stats_file):
        logger.info(f'stats already collected and processed from {archived_stats_file}')
    else:
        logger.info('start data collection')
        data=irodsdata.collect()
        data['collected'] = today_str
        logger.info(f'write stats to {stats_file}')
        with open(stats_file, 'w') as fp:
            json.dump(data, fp)
    irodsdata.close_session()
    logger.info('script finished')

logger = setup_logging()
collect()
