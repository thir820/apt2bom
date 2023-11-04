"""
apt2bom config handling.
"""
import os
import json
import logging


logger = logging.getLogger('conf')


def read_config(file: str = 'config.json') -> dict:
    """
    Read configuration file.
    """
    logger.debug('Reading config from %s ...', file)

    config = None
    with open(file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config


def read_packages(config) -> (list[str], list[str]):
    """
    Read PROD and DEV root packages.
    """
    prod = None
    file = config['packages']['ecu_productive']
    if os.path.exists(file):
        logger.debug('Reading productive packages from %s ...', file)
        with open(file, 'r', encoding='utf-8') as f:
            prod = [line.split(' ')[0].strip() for line in f.readlines()]

    dev = None
    file = config['packages']['ecu_development']
    if os.path.exists(file):
        logger.debug('Reading development packages from %s ...', file)
        with open(file, 'r', encoding='utf-8') as f:
            dev = [line.split(' ')[0].strip() for line in f.readlines()]

    sdk = None
    file = config['packages']['sdk']
    if os.path.exists(file):
        logger.debug('Reading SDK packages from %s ...', file)
        with open(file, 'r', encoding='utf-8') as f:
            sdk = [line.split(' ')[0].strip() for line in f.readlines()]
    
    if not prod and not dev and not sdk:
        logger.error('No root packages defined!')
        exit(1)
    elif 'architectures' not in config['packages'] or not config['packages']['architectures']:
        logger.error('No architectures defined!')
        exit(1)
    else:
        logger.info('Found %d prod packages and %d dev packages.', len(prod), len(dev))
    
    return prod, dev, sdk
