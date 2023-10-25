"""
apt2bom main
"""
import logging
from .conf import read_config, read_packages
from .apt_parsing import scan_repositories
from .resolve_lists import resolve_package_lists
from .output import write_package_lists, write_repos
from .log import config_logger


def run():
    print("apt2bom - package lists form APT metadata")
    print("Configuring loggers...")
    config_logger()
    logging.info("apt2bom - package lists form APT metadata")

    # read config and input
    logging.info('Read inputs...')
    config = read_config()
    prod, dev = read_packages(config)
    
    # read apt metadata
    logging.info('Scan apt repositories...')
    repos = scan_repositories(config)
    
    # dump APT metadata
    logging.info('Dump apt metadata...')
    write_repos(config, repos)
    
    # resolve packages
    logging.info('Resolve packages...')
    lists = resolve_package_lists(repos, prod, dev)
    
    # write package lists
    logging.info('Writing package lists...')
    write_package_lists(config, lists)
