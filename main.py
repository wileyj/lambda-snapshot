import logging
from lib.logger import Logger
from lib.instance import Instance
from lib.volume import Volume
from lib.snapshot import Snapshot
from lib.image import Image
from lib.aws_conn import conn
from lib.args import Args
from lib.config import Global
from datetime import timedelta
logger = logging.getLogger(__name__)
Logger()


# if __name__ == "__main__":
def handler(event, context):
    args = Args().args
    ec2_client = conn().boto3('ec2', args.region)
    cloudwatch_client = conn().boto3('cloudwatch', args.region)
    if args.volume and args.instance:
        logger.error("false. only one option is allowed")
        exit(1)
    if args.volume or args.instance:
        logger.info("Defaulting to type 'create-snapshot' with inclusiong of arg: %s %s" % (args.instance, args.volume))
        args.type = "create-snapshot"
    retention_day = timedelta(days=args.retention)
    start_date = Global.today - retention_day
    logger.info("*** Timing ***")
    logger.info("\tCurrent time: %i" % (Global.current_time))
    logger.info("\tRetention: %i" % (args.retention))
    logger.info("\tFull day in seconds: %i" % (Global.full_day))
    logger.info("\tToday: %s" % (str(Global.today)))
    logger.info("\tTomorrow: %s" % (str(Global.tomorrow)))
    logger.info("\tYesterday: %s" % (str(Global.yesterday)))
    logger.info("\t2 Weeks Ago: %s" % (str(Global.two_weeks)))
    logger.info("\t4 Weeks Ago: %s" % (str(Global.four_weeks)))
    logger.info("\t30 Days Ago: %s" % (str(Global.thirty_days)))
    logger.info("\tRetention Time: %s" % (str(retention_day)))
    logger.info("\tStart Date: %s" % (str(start_date)))
    logger.info("\tShort Date: %s" % (Global.short_date))
    logger.info("\tShort Hour: %s" % (Global.short_hour))
    logger.info("")
    logger.info("*** Defined Args ***")
    logger.info("\targs.verbosity: %s" % (args.verbosity))
    logger.info("\targs.type: %s" % (args.type))
    logger.info("\targs.env: %s" % (args.env))
    logger.info("\targs.volume: %s" % (args.volume))
    logger.info("\targs.instance: %s" % (args.instance))
    logger.info("\targs.retention: %s" % (args.retention))
    logger.info("\targs.dry_run: %s" % (args.dry_run))
    logger.info("\targs.region: %s" % (args.region))
    logger.info("\targs.account_id: %s" % (args.account_id))
    logger.info("\targs.rotation: %s" % (args.rotation))
    logger.info("\targs.hourly: %s" % (args.hourly))
    logger.info("\targs.persist: %s" % (args.persist))
    logger.info("\targs.method: %s" % (args.method))
    logger.info("\targs.include_ami: %s" % (args.include_ami))
    logger.info("")
    Instance(ec2_client, args.dry_run).find(args.env, '')
    Volume(ec2_client, args.dry_run).find(cloudwatch_client, args.instance, args.volume, args.hourly, args.persist)
    if args.type != "create-snapshot" or args.type != "create-snapshots":
        Snapshot(ec2_client, args.dry_run).find(args.account_id, args.env, args.method)
    if not args.volume and not args.instance:
        if args.type != "clean-snapshot" or args.type != "clean-snapshots" or args.type != "clean-volume" or args.type != "clean-volumes":
            Image(ec2_client, args.dry_run).find(args.env, args.account_id)
    if args.type == "all" or args.type == "clean-snapshot" or args.type == "clean-snapshots" or args.type == "clean":
        snapshot_count = 0
        logger.info("\n\n")
        logger.debug("Ignoring any env flag for cleanup: %s" % (args.env))
        logger.info("")
        logger.info("*** Cleaning Snapshots ***")
        logger.debug("\tsnapshot_data len: %i" % (len(Global.snapshot_data)))
        for snapshot in Global.snapshot_data:
            logger.info("Retrieved snapshot: %s" % (snapshot))
            if Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'] > 0:
                # if Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'] > args.rotation and not Global.snapshot_data[snapshot]['persist'] and not Global.snapshot_data[snapshot]['id'] in Global.image_data:
                logger.debug("")
                logger.debug("snapshot id: %s" % (Global.snapshot_data[snapshot]['id']))
                logger.debug("\tsnap_vol: %s" % (Global.snapshot_data[snapshot]['volume_id']))
                logger.debug("\tsnap_desc: %s" % (Global.snapshot_data[snapshot]['description']))
                logger.debug("\tsnap_date: %s" % (Global.snapshot_data[snapshot]['date']))
                logger.debug("\tsnap_ratio: %s" % (Global.snapshot_data[snapshot]['ratio']))
                logger.debug("\tsnap_age: %s" % (Global.snapshot_data[snapshot]['age']))
                logger.debug("\tsnap_persist: %s" % (Global.snapshot_data[snapshot]['persist']))
                logger.debug("\tsnap_method: %s" % (Global.snapshot_data[snapshot]['method']))
                logger.debug("\tsnap_count: %s" % (Global.snapshot_data[snapshot]['snap_count']))
                logger.debug("\tvolume_snapshot_count: %s" % (Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count']))
                logger.debug("\trotation_scheme: %i" % (args.rotation))
                logger.debug("\tDeleting %s - [ snap_count:%s, volume_count:%s, persist: %s ] [ vol: %s ]" % (Global.snapshot_data[snapshot]['id'], Global.snapshot_data[snapshot]['snap_count'], Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'], Global.snapshot_data[snapshot]['persist'], Global.snapshot_data[snapshot]['volume_id']))
                if Global.snapshot_data[snapshot]['volume_id'] not in Global.all_volumes:
                    logger.debug("\tvol: %s snap: %s snap_count: %s rotate: %i" % (Global.snapshot_data[snapshot]['volume_id'], Global.snapshot_data[snapshot]['id'], Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'], args.rotation))
                    ret_val = Snapshot(ec2_client, args.dry_run).delete(Global.snapshot_data[snapshot]['id'], '')
                    snapshot_count = snapshot_count + ret_val
                    Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'] = Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'] - ret_val
                else:
                    logger.debug("\tvol: %s snap: %s snap_count: %s rotate: %i" % (Global.snapshot_data[snapshot]['volume_id'], Global.snapshot_data[snapshot]['id'], Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'], args.rotation))
                    ret_val = Snapshot(ec2_client, args.dry_run).delete(Global.snapshot_data[snapshot]['id'], 'delete_snapshot')
                    snapshot_count = snapshot_count + ret_val
                    Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'] = Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'] - ret_val
            else:
                logger.warn("")
                logger.warn("\tIgnoring deletion of %s - [ snap_count:%s, volume_count:%s, persist: %s ]" % (Global.snapshot_data[snapshot]['id'], Global.snapshot_data[snapshot]['snap_count'], Global.volume_snapshot_count[Global.snapshot_data[snapshot]['volume_id']]['count'], Global.snapshot_data[snapshot]['persist']))
        logger.info("   *** Total Snapshots Deleted: %s" % (snapshot_count))

    if args.type == "all" or args.type == "clean-volume" or args.type == "clean-volumes" or args.type == "clean":
        volume_count = 0
        logger.info("\n\n")
        logger.debug("Ignoring any env flag for cleanup: %s" % (args.env))
        logger.info("*** Cleaning Volumes ***")
        logger.info("*** Note: this tags items with tag { 'Delete': 'True' } ***\n")
        for volume in Global.volume_data:
            logger.info("Retrieved Volume: %s" % (volume))
            volume_count = volume_count + 1
            logger.debug("")
            logger.debug("volume_id: %s" % (Global.volume_data[volume]['id']))
            logger.debug("\tvolume_instance_id: %s" % (Global.volume_data[volume]['instance_id']))
            logger.debug("\tvolume_date: %s" % (Global.volume_data[volume]['date']))
        logger.info("   *** Total Volumes To Delete: %s" % (volume_count))

    if args.type == "all" or args.type == "clean-ami" or args.type == "clean" or args.type == "clean-images":
        image_count = 0
        logger.info("\n\n")
        logger.debug("Ignoring any env flag for cleanup: %s" % (args.env))
        logger.info("*** Cleaning Images ***")
        # logger.info("Include_ami: %s" % (args.include_ami))
        logger.info("Images found: %i" % (len(Global.image_data)))
        for image in Global.image_data:
            image_count = image_count + 1
            logger.debug("")
            logger.debug("ami_id: %s" % (Global.image_data[image]['id']))
            logger.debug("\tami_name: %s" % (Global.image_data[image]['name']))
            logger.debug("\tami_attachment_id: %s" % (Global.image_data[image]['date']))
            logger.debug("\tami_snapshot_id: %s" % (Global.image_data[image]['snapshot_id']))
            logger.debug("\tami_persist: %s" % (Global.image_data[image]['persist']))
            logger.debug("\tami_build_method: %s" % (Global.image_data[image]['build_method']))
            # this is disabled for now until we're sure we want to auto delete AMI's
            if args.include_ami:
                if Global.image_data[image]['persist'] != "True":
                    logger.info("Deregistering AMI: %s" % (Global.image_data[image]['name']))
                    for ami_snapshot in Global.image_data[image]['snapshot_id']:
                        logger.info("\t deleting snapshot: %s" % (ami_snapshot))
                        Snapshot(ec2_client, args.dry_run).delete(ami_snapshot, 'delete_snapshot')
                        logger.info("\t deleting image: %s" % (Global.image_data[image]['id']))
                        Image(ec2_client, args.dry_run).delete(Global.image_data[image]['id'], Global.image_data[image]['name'])
                logger.info("   *** Total Images Deregistered: %s" % (image_count))

    if args.type == "all" or args.type == "create-snapshot" or args.type == "create-snapshots":
        snapshot_count = 0
        logger.info("\n\n")
        logger.info("*** Creating Snapshots ***")
        for s_volume in Global.snapshot_volumes:
            logger.debug("")
            logger.debug("\tsnapshot_volume['volume_id']: %s" % (Global.snapshot_volumes[s_volume]['id']))
            logger.debug("\tsnapshot_volume['instance_id']: %s" % (Global.snapshot_volumes[s_volume]['instance_id']))
            logger.debug("\tsnapshot_volume['date']: %s" % (Global.snapshot_volumes[s_volume]['date']))
            logger.debug("\tsnapshot_volume['desc']: %s" % (Global.snapshot_volumes[s_volume]['desc']))
            logger.debug("\tsnapshot_volume['old_desc']: %s" % (Global.snapshot_volumes[s_volume]['old_desc']))
            logger.debug("\tsnapshot_volume['persist']: %s" % (Global.snapshot_volumes[s_volume]['persist']))
            logger.debug("\tsnapshot_volume['hourly']: %s" % (Global.snapshot_volumes[s_volume]['hourly']))
            snapshot_count = snapshot_count + Snapshot(ec2_client, args.dry_run).create(args.region, Global.snapshot_volumes[s_volume]['id'], Global.snapshot_volumes[s_volume]['desc'], Global.snapshot_volumes[s_volume]['old_desc'], Global.snapshot_volumes[s_volume]['persist'])
        logger.info("   *** Total Volumes to Snapshot: %s" % (snapshot_count))
    return True
    # exit(0)
