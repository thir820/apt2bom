# setup loggers
from apt2bom.log import config_logger
import logging
config_logger(level=logging.INFO)

import argparse
parser = argparse.ArgumentParser(
    prog='apt2bom',
    description='WGenerate SBoM from apt metadata.')
parser.add_argument('-c', '--config')
args = parser.parse_args()

# run tool
from apt2bom.apt2bom import run
run(config=args.config)
