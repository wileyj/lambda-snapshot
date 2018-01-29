from config import Global
import logging
from logger import Logger
logger = logging.getLogger(__name__)
Logger()


class Metrics(object):
    def __init__(self, client, dry_run):
        self.client = client
        self.dry_run = dry_run

    def is_active(self, instance_id):
        '''
            Determine if Volume is attached to running instance
        '''
        logger.info("\tChecking for disk usage on running host: %s" % (instance_id))
        if instance_id in Global.instance_data and Global.instance_data[instance_id]['state'] == 'running':
            return True
        return False

    def is_candidate(self, volume_id, instance_id):
        '''
            Make sure the volume is candidate for delete
        '''
        if Metrics(self.client, self.dry_run).is_active(instance_id):
            metrics = Metrics(self.client, self.dry_run).metrics(volume_id)
            if len(metrics) > 0:
                for metric in metrics:
                    if metric['Minimum'] < Global.volume_metric_mininum:
                        logger.info("\t [ INACTIVE VOLUME ] - Tagging Volume for deletion: (%i, %s)" % (metric['Minimum'], volume_id))
                        # logger.info("\t [ INACTIVE VOLUME ] - Tagging Volume for deletion: (%i, %s, %s, %s)" % (metric['Minimum'], Global.instance_data[instance_id]['name'], instance_id, volume_id))
                        return True
                    else:
                        logger.info("\t [ ACTIVE VOLUME ] - Ignoring for deletion: (%i, %s)" % (metric['Minimum'], volume_id))
                        # logger.info("\t [ ACTIVE VOLUME ] - Ignoring for deletion: (%i, %s, %s, %s)" % (metric['Minimum'], Global.instance_data[instance_id]['name'], instance_id, volume_id))
                        return False
            else:
                logger.error("Volume metrics not returned")
                return False
        else:
            logger.warn("%s not active on %s" % (volume_id, instance_id))
            return True

    def metrics(self, volume_id):
        '''
            Get volume idle time on an individual volume over `start_date` to today
        '''
        self.volume_metrics_data = self.client.get_metric_statistics(
            Namespace='AWS/EBS',
            MetricName='VolumeIdleTime',
            Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
            Period=3600,
            StartTime=Global.two_weeks,
            EndTime=Global.today,
            Statistics=['Minimum'],
            Unit='Seconds'
        )
        logger.debug("\t\tReturning datapoints: %s" % (self.volume_metrics_data['Datapoints'][0]['Minimum']))
        return self.volume_metrics_data['Datapoints']
