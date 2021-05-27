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

logger = setup_logging()
statsfile = f'/home/peter/adminyoda/scripts/data/yodastats-{today_str}.json'
irodsdata = IrodsData()
irodsdata.logger=logger
logger.info('start script irods_tasks.py')
if not os.path.exists(statsfile):
    logger.info(f'collect data in {statsfile}')
    data=irodsdata.collect()
    with open(statsfile, 'w') as fp:
        json.dump(data, fp)
else:
    logger.info(f'stats already collected in {statsfile}')
logger.info('script finished')