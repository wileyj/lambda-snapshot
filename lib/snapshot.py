from config import Global
from difflib import SequenceMatcher
import logging
from logger import Logger
logger = logging.getLogger(__name__)
Logger()


class Snapshot(object):
    def __init__(self, client, dry_run):
        self.client = client
        self.dry_run = dry_run

    def find(self, account_id, env, ami_method):
        '''
            find_snapshots function
        '''
        logger.info("*** Retrieving snapshots")
        count_deleted = 0
        my_snapshots = sorted(
            self.client.describe_snapshots(
                Filters=[{
                    'Name': 'owner-id',
                    'Values': [account_id]
                }, {
                    'Name': 'tag:Environment',
                    'Values': [env]
                }]
            )['Snapshots'],
            key=lambda x: (
                x['VolumeId'],
                x['StartTime']
            ),
            reverse=True
        )
        logger.info("Discovered Snapshots: %i" % (len(my_snapshots)))
        for item in my_snapshots:
            method = "undefined"
            try:
                if Global.snapshot_existing[item['VolumeId']]:
                    logger.debug("Found existing key for in snapshot_existing for %s" % (item['VolumeId']))
                    pass
            except Exception:
                logger.debug("\tInitializing empty key/val for %s" % (item['VolumeId']))
                Global.snapshot_existing[item['VolumeId']] = {'snapshots': []}
            try:
                Global.volume_snapshot_count[item['VolumeId']] = {'count': Global.volume_snapshot_count[item['VolumeId']]['count'] + 1}
                logger.debug("incrementing count value +1 for disk (%s)" % (Global.volume_snapshot_count[item['VolumeId']]))
            except:
                Global.volume_snapshot_count[item['VolumeId']] = {'count': 1}
                logger.debug("setting count value = 1 for disk (%s)" % (Global.volume_snapshot_count[item['VolumeId']]))
            epoch = int(item['StartTime'].strftime("%s"))
            diff = Global.current_time - epoch
            age = diff / Global.full_day
            snap_timestamp = "null"
            snap_persist = False
            try:
                for t in item['Tags']:
                    if t['Key'] == "BuildMethod":
                        method = t['Value']
                    if t['Key'] == "Timestamp":
                        snap_timestamp = t['Value']
                    if t['Key'] == "Persist":
                        snap_persist = t['Value']
            except:
                pass
            match_ratio = SequenceMatcher(
                lambda item:
                item == " ",
                "Created by CreateImage(i-",
                item['Description']
            ).ratio()
            logger.debug("MatchRatio ('Created by CreateImage(i-'): %i" % (match_ratio))
            if match_ratio < 0.53 or match_ratio > 0.54:
                logger.debug("checking for method: %s" % (ami_method))
                # not a snapshot created by an ami
                # if age > args.retention and method != "Packer":
                if method != ami_method:
                    count_deleted = count_deleted + 1
                    try:
                        logger.info("\t*** appending %s to  snapshot_exsting[ %s ]" % (item['SnapshotId'], item['VolumeId']))
                        Global.snapshot_existing[item['VolumeId']]['snapshots'].append(item['SnapshotId'])
                    except Exception:
                        logger.error("*** Problem appending %s to  snapshot_exsting[ %s ]" % (item['SnapshotId'], item['VolumeId']))
                        pass
                    Global.snapshot_data[item['SnapshotId']] = {
                        'id': item['SnapshotId'],
                        'volume_id': item['VolumeId'],
                        'description': item['Description'],
                        'date': item['StartTime'],
                        'ratio': match_ratio,
                        'age': age,
                        'method': method,
                        'persist': snap_persist,
                        'timestamp': snap_timestamp,
                        'snap_count': Global.volume_snapshot_count[item['VolumeId']]['count']
                    }
                    logger.info("\tAdded snapshot (%s) to snapshot_data dict" % (item['SnapshotId']))
                else:
                    logger.warn("Found %s snapshot: %s" % (ami_method, item['SnapshotId']))
            else:
                # snapshot created by an AMI (generically, don't delete these, except in the case of clean-images)
                logger.info("AMI snapshot")
                Global.image_snapshot[item['SnapshotId']] = {
                    'id': item['SnapshotId'],
                    'volume_id': item['VolumeId'],
                    'description': item['Description'],
                    'date': item['StartTime'],
                    'ratio': match_ratio,
                    'age': age,
                    'method': method,
                    'persist': snap_persist,
                    'timestamp': snap_timestamp,
                    'snap_count': Global.volume_snapshot_count[item['VolumeId']]['count']
                }
                logger.info("\t\tAdded snap(%s) to image_snapshot dict" % (item['SnapshotId']))

        logger.info("\tTotal snapshots: %i" % (len(my_snapshots)))
        logger.info("\tTotal snapshots to retain: %i" % (len(my_snapshots) - len(Global.snapshot_data)))
        logger.info("\tTotal snapshots tagged for rotation: %i" % (len(Global.snapshot_data)))
        return True

    def create(self, region, volume_id, description, old_description, persist):
        '''
            Create snapshot of volume
            need to augment so that the tags are reflections from the host the volume comes from
            application = tag.Application
            role = tag.Role
            ...
        '''
        logger.info("*** Creating Snapshots")
        try:
            if Global.instance_data[Global.all_volumes[volume_id]['instance_id']]['environment']:
                logger.warn("Instance: %s" % (Global.all_volumes[volume_id]['instance_id']))
                logger.warn("Environment: %s" % (Global.instance_data[Global.all_volumes[volume_id]['instance_id']]['environment']))
                if Global.instance_data[Global.all_volumes[volume_id]['instance_id']]['state'] == "running":
                    logger.info("\tCreating Snapshot of %s with Description: %s " % (volume_id, description))
                    logger.debug("\tCreating tags:")
                    logger.debug("\t\tName: %s" % (description))
                    logger.debug("\t\tVolume: %s" % (volume_id))
                    logger.debug("\t\tDepartpment: %s" % ("ops"))
                    logger.debug("\t\tInstanceId: %s" % (Global.all_volumes[volume_id]['instance_id']))
                    logger.debug("\t\tEnvironment: %s" % (Global.instance_data[Global.all_volumes[volume_id]['instance_id']]['environment']))
                    logger.debug("\t\tRegion: %s" % (region))
                    logger.debug("\t\tApplication: %s" % ("shared"))
                    logger.debug("\t\tRole: %s" % ("ec2"))
                    logger.debug("\t\tService: %s" % ("ebs"))
                    logger.debug("\t\tPersist: %s" % (persist))
                    logger.debug("\t\tCategory: %s" % ("snapshot"))
                    if not self.dry_run:
                        create_snap = self.client.create_snapshot(
                            # DryRun=True,
                            VolumeId=volume_id,
                            Description=description
                        )
                        logger.info("\t\t Snapshot created: %s" % (create_snap['SnapshotId']))
                        self.client.create_tags(
                            # DryRun=True,
                            Resources=[create_snap['SnapshotId']],
                            Tags=[{
                                'Key': 'Name',
                                'Value': description
                            }, {
                                'Key': 'Volume',
                                'Value': volume_id
                            }, {
                                'Key': 'Department',
                                'Value': 'Ops'
                            }, {
                                'Key': 'Instance',
                                'Value': Global.all_volumes[volume_id]['instance_id']
                            }, {
                                'Key': 'Environment',
                                'Value': Global.instance_data[Global.all_volumes[volume_id]['instance_id']]['environment']
                            }, {
                                'Key': 'Region',
                                'Value': region
                            }, {
                                'Key': 'Application',
                                'Value': 'shared'
                            }, {
                                'Key': 'Role',
                                'Value': 'ebs'
                            }, {
                                'Key': 'Service',
                                'Value': 'ec2'
                            }, {
                                'Key': 'Category',
                                'Value': 'snapshot'
                            }]
                        )
                        logger.debug("\t\t Snapshot %s tags created" % (create_snap['SnapshotId']))
                        return 1
                    else:
                        logger.info("\t(dry-run) Creating Snapshot of %s with Description: %s " % (volume_id, description))
                        return 1
        except:
            pass
        return 0

    def delete(self, snapshot_id, referrer):
        '''
            delete_snapshot
        '''

        if not self.dry_run:
            # logger.info("\tDeleting snapshot %s (count:%s :: persist:%s)" % (snapshot_id, Global.volume_snapshot_count[Global.snapshot_data[snapshot_id]['volume_id']]['count'], Global.snapshot_data[snapshot_id]['persist']))
            logger.info("\t Deleting snapshot %s" % (snapshot_id))
            Global.volume_snapshot_count[Global.snapshot_data[snapshot_id]['volume_id']] = {'count': Global.volume_snapshot_count[Global.snapshot_data[snapshot_id]['volume_id']]['count'] - 1}
            self.client.delete_snapshot(
                # DryRun=True,
                SnapshotId=snapshot_id
            )
        else:
            # logger.info("\t (dry-run) Deleting snapshot %s (count:%s :: persist:%s)" % (snapshot_id, Global.volume_snapshot_count[Global.snapshot_data[snapshot_id]['volume_id']]['count'], Global.snapshot_data[snapshot_id]['persist']))
            logger.info("\t (dry-run) Deleting snapshot %s" % (snapshot_id))
        return 1
