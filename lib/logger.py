from os import path, remove
import logging
import logging.config
import json
import os
from args import Args


class Logger():
    args = Args().args
    cwd = os.getcwd()
    with open(cwd + "/logging.json", 'r') as logging_configuration_file:
        config_dict = json.load(logging_configuration_file)
    if 'console' in config_dict['handlers']:
        config_dict['handlers']['console']['level'] = args.verbosity
        config_dict['handlers']['console']['formatter'] = args.verbosity
    # if 'level' in config_dict['root']:
    #     config_dict['root']['level'] = args.verbosity
    for handler in config_dict['handlers']:
        # config_dict['handlers'][handler]['formatter'] = args.verbosity
        if 'filename' in config_dict['handlers'][handler]:
            if path.isfile(config_dict['handlers'][handler]['filename']):
                print "Deleting logfile %s" % (config_dict['handlers'][handler]['filename'])
                remove(config_dict['handlers'][handler]['filename'])

    logging.config.dictConfig(config_dict)
    logger = logging.getLogger(__name__)
    logger.info("Logger Initialized")
    logger.debug("DEBUG Logger Initialized")
