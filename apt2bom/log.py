"""
Logging configuration.
"""
import logging
import requests # needed for urllib log level config
from logging.config import dictConfig


log_level = logging.DEBUG


def config_logger(level=logging.DEBUG, logfile='apt2bom.log'):
    """
    Config Python logging.
    """
    global log_level

    logging_config = dict(
        version = 1,
        formatters = {
            'f': {'format':
                '%(asctime)s %(levelname)-15s %(name)-8s %(message)s'}
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

    log_level = level

    root = logging.getLogger()
    root.setLevel(level)
    root.log(level, 'Using log level: %s', level)

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        if 'urllib' in logger.name:
            logger.setLevel(logging.WARNING)
            continue

        logger.setLevel(level)
        logger.log(level, 'Using log level: %s', level)
