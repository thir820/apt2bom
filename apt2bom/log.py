"""
Logging configuration.
"""
from logging.config import dictConfig
import logging


def config_logger(level=logging.DEBUG, logfile='apt2bom.log'):
    """
    Config Python logging.
    """
    logging_config = dict(
        version = 1,
        formatters = {
            'f': {'format':
                '%(asctime)s %(levelname)-8s %(message)s'}
            },
        handlers = {
            'h': {'class': 'logging.StreamHandler',
                'formatter': 'f',
                'level': level},
            'f': {
                'level': level,
                'formatter': 'f',
                'class': 'logging.FileHandler',
                'filename': logfile,
                'mode': 'a'}
            },
        root = {
            'handlers': ['h', 'f'],
            'level': level,
            },
    )
    dictConfig(logging_config)

    logging.log(level, 'Using log level: %s', level)
