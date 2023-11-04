"""
apt2bom main
"""
import logging
from .conf import read_config, read_packages
from .apt_parsing import scan_repositories
from .resolve_lists import resolve_package_lists
from .output import write_package_lists, write_repos
from .excel import write_excel_package_list


logger = logging.getLogger('apt2bom')


def run(config: str ='config.yaml'):
    print('apt2bom - package lists form APT metadata')
    print('Configuring loggers...')
    logger.info('apt2bom - package lists form APT metadata')

    # read config and input
    logger.info('Read inputs...')
    config = read_config(file=config)
    prod, dev, sdk = read_packages(config)

    # read apt metadata
    logger.info('Scan apt repositories...')
    repos = scan_repositories(config)
    
    # dump APT metadata
    logger.info('Dump apt metadata...')
    write_repos(config, repos)

    # resolve packages
    logger.info('Resolve packages...')
    architectures = config['packages']['architectures']
    lists = resolve_package_lists(repos, architectures, prod, dev, sdk)
    
    # write package lists
    logger.info('Writing package lists...')
    write_package_lists(config, lists)

    # write excel list
    logger.info('Writing excel list...')
    write_excel_package_list(config, lists)
