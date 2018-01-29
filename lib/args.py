import argparse
import os
from boto3 import client
# from config import Global
# import logging
# from logger import Logger
# logger = logging.getLogger(__name__)
# Logger()

# class VAction(argparse.Action):
#     """ docstring """
#     def __call__(self, argparser, cmdargs, values, option_string=None):
#         if values is None:
#             values = '1'
#         try:
#             values = int(values)
#         except ValueError:
#             values = values.count('v') + 1
#         setattr(cmdargs, self.dest, values)


class Args:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--type',
            choices=[
                "clean-ami",
                "clean-snapshot",
                "clean-snapshots",
                "clean-volume",
                "clean-volumes",
                "clean",
                "clean-images",
                "create-snapshot",
                "create-snapshots",
                "all"
            ],
            nargs='?',
            metavar='',
            default=os.getenv('TYPE', 'all'),
            help="type",
            # required=True
        )
        parser.add_argument(
            '--region',
            choices=[
                "us-east-1",
                "us-west-1",
                "us-west-2",
                "ap-southeast-1"
                # etc
            ],
            nargs='?',
            metavar='',
            default=os.getenv('REGION', 'us-west-2'),
            help="region",
            # required=True
        )
        parser.add_argument(
            '--account_id',
            nargs='?',
            metavar='',
            default=os.getenv('ACCOUNT_ID', client('sts').get_caller_identity().get('Account')),
            # required=True,
            help="account_id"
        )
        # parser.add_argument(
        #     '-v',
        #     dest='verbose',
        #     default=os.getenv('VERBOSE', 'true'),
        #     nargs='?'
        # )
        parser.add_argument(
            '--verbosity',
            '-v',
            choices=[
                "INFO",
                "ERROR",
                "CRITICAL",
                "WARNING",
                "DEBUG"
            ],
            nargs='?',
            default=os.getenv('VERBOSITY', 'INFO'),
            help="Verbosity Level"
        )
        parser.add_argument(
            '--volume',
            nargs='?',
            default=os.getenv('VOLUME', ''),
            help="VolumeID"
        )
        parser.add_argument(
            '--instance',
            nargs='?',
            default=os.getenv('INSTANCE_ID', ''),
            help="InstanceID"
        )
        parser.add_argument(
            '--method',
            nargs='?',
            default=os.getenv('AMI_CREATION_METHOD', 'Packer'),
            help="AMI Creation Method (Packer, etc)"
        )
        parser.add_argument(
            '--retention',
            nargs='?',
            default=os.getenv('RETENTION', 7),
            type=int,
            help="Retention"
        )
        parser.add_argument(
            '--rotation',
            nargs='?',
            default=os.getenv('ROTATION', 7),
            type=int,
            help="Rotation"
        )
        parser.add_argument(
            '--hourly',
            action='store_true',
            default=os.getenv('HOURLY', ''),
            help="Hourly"
        )
        parser.add_argument(
            '--persist',
            action='store_true',
            default=os.getenv('PERSIST', ''),
            help="Persist"
        )
        parser.add_argument(
            '--env',
            choices=[
                "dev",
                "staging",
                "stg",
                "production",
                "prod",
                "prd"
            ],
            nargs='?',
            metavar='',
            default=os.getenv('ENVIRONMENT', '*'),
            help="Environment"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=os.getenv('DRY_RUN', 'true'),
            help="DryRun"
        )
        parser.add_argument(
            '--include-ami',
            action='store_true',
            default=os.getenv('INCLUDE_AMI', 'false'),
            help="Include unused and old AMI's in cleanup. This *WILL* delete old AMI's"
        )
        self.args = parser.parse_args()
        if not self.args.type or not self.args.account_id:
            print parser.print_help()
            exit(3)
        # check if events json is present. if yes, overwrite the args above.

    def __repr__(self):
        return repr((self.args))
