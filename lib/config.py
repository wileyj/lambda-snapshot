# from args import Args
import time
from datetime import datetime, timedelta
import logging
from logger import Logger
logger = logging.getLogger(__name__)
Logger()


class Global(object):
    logger.info("*** Defining Global variables")
    env_map = {
        'prd': 'prod',
        'prod': 'prod',
        'production': 'prod',
        'live': 'prod',
        'dev': 'dev',
        'development': 'dev',
        'qa': 'qa',
        'stg': 'staging',
        'staging': 'staging',
        'stage': 'staging',
        '*': '*'
    }
    volume_metric_mininum = 150
    instance_data = {}
    image_data = {}
    map_images = {}
    image_snapshot = {}
    ignored_images = []
    snapshot_data = {}
    snapshot_existing = {}
    volume_data = {}
    all_volumes = {}
    snapshot_volumes = {}
    volume_snapshot_count = {}
    current_time = int(round(time.time()))
    full_day = 86400
    today = datetime.now()
    tomorrow = datetime.now() + timedelta(days=1)
    yesterday = datetime.now() - timedelta(days=1)
    two_weeks = datetime.now() - timedelta(days=14)
    four_weeks = datetime.now() - timedelta(days=28)
    thirty_days = datetime.now() - timedelta(days=30)
    short_date = str('{:04d}'.format(today.year)) + str('{:02d}'.format(today.month)) + str('{:02d}'.format(today.day))
    short_hour = str('{:04d}'.format(today.year)) + str('{:02d}'.format(today.month)) + str('{:02d}'.format(today.day)) + "_" + str(current_time)
