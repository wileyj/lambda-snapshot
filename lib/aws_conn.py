import boto3
from logger import Logger
import logging
logger = logging.getLogger(__name__)
Logger()


class conn():
    def boto3(self, service, region):
        logger.info("Initializing AWS connection to %s in region(%s)" % (service, region))
        ec2_client = boto3.client(service, region_name=region)
        return ec2_client
