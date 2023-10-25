"""
apt2bom config handling.
"""
import json
import logging


def read_config(file: str = 'config.json') -> dict:
    """
    Read configuration file.
    """
    logging.debug('Reading config from %s ...', file)

    config = None
    with open(file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config


def read_packages(config) -> (list[str], list[str]):
    """
    Read PROD and DEV root packages.
    """
    logging.debug('Reading productive packages from %s ...', config['prod-packages'])
    prod = None
    with open(config['prod-packages'], 'r', encoding='utf-8') as f:
        prod = [line.split(' ')[0].strip() for line in f.readlines()]

    logging.debug('Reading development packages from %s ...', config['dev-packages'])
    dev = None
    with open(config['dev-packages'], 'r', encoding='utf-8') as f:
        dev = [line.split(' ')[0].strip() for line in f.readlines()]
    
    if not prod and not dev:
        logging.error('No root packages defined!')
        exit(1)
    else:
        logging.info('Found %d prod packages and %d dev packages.', len(prod), len(dev))
    
    return prod, dev
