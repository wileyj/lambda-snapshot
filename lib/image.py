from config import Global
import logging
from logger import Logger
logger = logging.getLogger(__name__)
Logger()


class Image(object):
    def __init__(self, client, dry_run):
        self.client = client
        self.dry_run = dry_run

    def find(self, env, account_id):
        '''
            find_images function
        '''
        logger.info("")
        logger.info("*** Retrieving images")
        logger.debug("*** Using account_id: %s" % (account_id))
        if env is not "*":
            logger.info("\t Discarding env arg for image retrieval")
        count_images = 0
        my_images = sorted(
            self.client.describe_images(
                Owners=[account_id]
            )['Images'],
            key=lambda x: (
                x['Name'],
                x['CreationDate']
            ),
            reverse=True
        )
        for x in my_images:
            count_images = count_images + 1
            # set_buildmethod = False
            set_persist = False
            set_buildmethod = "undefined"
            logger.warn("Checking image: %s" % (x['Name']))
            try:
                for t in x['Tags']:
                    if t['Key'] == "Persist":
                        if t['Value'] is '':
                            set_persist = "False"
                        else:
                            set_persist = t['Value']
                            logger.warn("\tFound Persist Tag (%s) in image (%s)" % (set_persist, x['ImageId']))
                    if t['Key'] == "BuildMethod":
                        set_buildmethod = t['Value']
            except:
                set_persist = "False"
                set_buildmethod = "undefined"
            logger.debug("*** \tset_persist:%s:" % (set_persist))
            if set_persist != "True":
                ami_snapshot_existing = []
                for index, this in enumerate(x['BlockDeviceMappings'], start=0):
                    if 'Ebs' in this and 'SnapshotId' in this['Ebs']:
                        # the following 4 lines make it so that ami snapshots are ignored
                        logger.info("*** Found AMI snapshot: %s" % (this['Ebs']['SnapshotId']))
                        if this['Ebs']['SnapshotId'] in Global.snapshot_data:
                            print "\tRemoving AMI snapshot from snapshot_data - %s:%s" % (x['ImageId'], this['Ebs']['SnapshotId'])
                            del Global.snapshot_data[this['Ebs']['SnapshotId']]
                        ami_snapshot_existing.append(this['Ebs']['SnapshotId'])
                if not x['ImageId'] in Global.map_images:
                    logger.debug("[ INACTIVE ] -  %s ( %s )" % (x['ImageId'], x['Name']))
                    Global.image_data[x['ImageId']] = {
                        'id': x['ImageId'],
                        'name': x['Name'],
                        'active': False,
                        'date': x['CreationDate'],
                        'persist': set_persist,
                        'build_method': set_buildmethod,
                        'snapshot_id': ami_snapshot_existing
                    }
                else:
                    logger.debug("[ ACTIVE ]   %s ( %s )" % (x['ImageId'], x['Name']))
            # else:
            #     logger.info("###\t set_persist not matching True")
        logger.info("\tTotal Images Found: %i" % (count_images))
        logger.info("\tTotal Images tagged for deletion: %i" % (len(Global.image_data)))
        return True

    def delete(self, ami_id, ami_name):
        '''
            deregister_image
        '''
        if not self.dry_run:
            logger.info("\t ( disabled ) - Deregistering Image: %s %s" % (ami_id, ami_name))
            self.client.deregister_image(
                # DryRun=True,
                ImageId=ami_id
            )
        else:
            logger.info("\t (dry run) ( disabled ) - Deregistering Image: %s %s" % (ami_id, ami_name))
        return True
