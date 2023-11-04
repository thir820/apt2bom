# setup loggers
from apt2bom.log import config_logger
import logging
config_logger(level=logging.INFO)

# run tool
from apt2bom.apt2bom import run
run()
