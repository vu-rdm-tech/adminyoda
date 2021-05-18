import logging
import os
from datetime import datetime
import json
from irodsdata import irodsdata

today = datetime.now()
today_str = today.strftime('%Y%m%d')

def setup_logging():
    LOGFILE = 'adminyoda-tasks-%s.log' % (today_str)
    logger = logging.getLogger('irods_tasks')
    hdlr = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()
statsfile = f'collections-{today_str}.json'
irodsdata = irodsdata()
irodsdata.logger=logger
if not os.path.exists(statsfile):
    data=irodsdata.collect()
    with open(statsfile, 'w') as fp:
        json.dump(data, fp)
