from config import Global
from logger import Logger
import logging
logger = logging.getLogger(__name__)
Logger()


class Instance():
    def __init__(self, client, dry_run):
        self.client = client
        self.dry_run = dry_run

    def find(self, env, instance):
        '''
            find_instances function
        '''
        logger.info("")
        logger.info("*** Retrieving VPC instances")
        logger.debug("env: %s" % (env))
        logger.debug("instance: %s" % (instance))
        Global.instances_vpc = sorted(
            self.client.describe_instances(
                Filters=[{
                    'Name': 'vpc-id',
                    'Values': ['*']
                }, {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'stopped']
                }, {
                    'Name': 'tag:Environment',
                    'Values': [env]
                }]
            )['Reservations'],
            key=lambda x: (
                x['Instances'][0]['LaunchTime'],
                x['Instances'][0]['InstanceId']
            ),
            reverse=True
        )
        logger.info("Total vpc instances: %i" % (len(Global.instances_vpc)))
        if not instance:
            logger.debug("*** Retrieving EC2 instances")
            instances_all = sorted(
                self.client.describe_instances(
                    Filters=[{
                        'Name': 'instance-state-name',
                        'Values': ['running', 'stopped']
                    }, {
                        'Name': 'tag:Environment',
                        'Values': [env]
                    }]
                )['Reservations'],
                key=lambda x: (
                    x['Instances'][0]['LaunchTime'],
                    x['Instances'][0]['InstanceId']
                ),
                reverse=True
            )
        else:
            logger.debug("*** Retrieving specified instance %s" % (instance))
            instances_all = sorted(
                self.client.describe_instances(
                    Filters=[{
                        'Name': 'instance-state-name',
                        'Values': ['running', 'stopped']
                    }, {
                        'Name': 'instance-id',
                        'Values': [instance]
                    }]
                )['Reservations'],
                key=lambda x: (
                    x['Instances'][0]['LaunchTime'],
                    x['Instances'][0]['InstanceId']
                ),
                reverse=True
            )
        logger.debug("Total count of instances retrieved: %i" % (len(instances_all)))
        try:
            if len(instances_all) < 1:
                logger.error("instances returned zero results... (%i)" % (len(instances_all)))
                logger.error(instances_all)
        except:
            pass
        list_vpc = [item for item in Global.instances_vpc]
        list_all = [item for item in instances_all]
        instance_without_vpc = [item for item in instances_all if item not in list_vpc]
        running_count = 0
        stopped_count = 0
        for item in instances_all:
            logger.debug("Retrieving data for instance: %s" % (item['Instances'][0]['InstanceId']))
            t_name = ""
            t_env = ""
            t_vpc = ""
            platform = ""
            t_app = ""
            t_role = ""
            try:
                for tag in item['Instances'][0]['Tags']:
                    if tag['Key'] == "Name":
                        t_name = tag['Value']
                    if tag['Key'] == "Environment":
                        t_env = tag['Value']
                    if tag['Key'] == "Application":
                        t_app = tag['Value']
                    if tag['Key'] == "Role":
                        t_app = tag['Value']
            except:
                t_name = item['Instances'][0]['InstanceId']
            try:
                t_vpc = item['Instances'][0]['VpcId']
            except:
                t_vpc = "None"
            try:
                if item['Instances'][0]['Platform']:
                    platform = item['Instances'][0]['Platform']
            except:
                platform = "Linux"
            try:
                if item['Instances'][0]['PrivateIpAddress']:
                    private_ip_address = item['Instances'][0]['PrivateIpAddress']
            except:
                private_ip_address = "Undefined"
            try:
                if item['Instances'][0]['SubnetId']:
                    subnet_id = item['Instances'][0]['SubnetId']
            except:
                subnet_id = "Undefined"
            logger.debug("\t Name: %s" % (t_name))
            logger.debug("\t Environment: %s" % (t_env))
            logger.debug("\t VPC: %s" % (t_vpc))
            logger.debug("\t Platform: %s" % (platform))
            logger.debug("\t IP: %s" % (private_ip_address))
            logger.debug("\t Subnet: %s" % (subnet_id))
            Global.instance_data[item['Instances'][0]['InstanceId']] = {
                'id': item['Instances'][0]['InstanceId'],
                'state': item['Instances'][0]['State']['Name'],
                'type': item['Instances'][0]['InstanceType'],
                'private_dns': item['Instances'][0]['PrivateDnsName'],
                'private_ip': private_ip_address,
                'launch_time': item['Instances'][0]['LaunchTime'],
                'image_id': item['Instances'][0]['ImageId'],
                'platform': platform,
                'subnet_id': subnet_id,
                'virt': item['Instances'][0]['VirtualizationType'],
                'name': t_name,
                'vpc': t_vpc,
                'environment': t_env,
                'application': t_app,
                'role': t_role,
                'volumes': []
            }
            if item['Instances'][0]['State']['Name'] == 'running':
                running_count = running_count + 1
            else:
                stopped_count = stopped_count + 1
                if not self.dry_run:
                    self.client.create_tags(
                        # DryRun=True,
                        Resources=[item['Instances'][0]['InstanceId']],
                        Tags=[{
                            'Key': 'Delete',
                            'Value': 'True'
                        }]
                    )
            for volume in item['Instances'][0]['BlockDeviceMappings']:
                Global.instance_data[item['Instances'][0]['InstanceId']]['volumes'].append(volume['Ebs']['VolumeId'])
            try:
                Global.map_images[item['Instances'][0]['ImageId']] = {
                    'imaged_id': item['Instances'][0]['ImageId'],
                    'instance_id': [item['Instances'][0]['InstanceId']],
                }
            except:
                Global.map_images[item['Instances'][0]['ImageId']]['instance_id'].append(item['Instances'][0]['InstanceId'])
        logger.info("\t Total VPC Instances: %s" % (len(list_vpc)))
        logger.info("\t Total Instances: %s" % (len(list_all)))
        logger.info("\t Total Classic Instances: %i" % (len(instance_without_vpc)))
        logger.info("\t Total Running Instances: %i" % (running_count))
        logger.info("\t Total Stopped Instances: %i" % (stopped_count))
        logger.info("\t Total Mapped Instances: %i" % (len(Global.map_images)))
        logger.info("\t Items in instance_data dict: %i" % (len(Global.instance_data)))
        return True
