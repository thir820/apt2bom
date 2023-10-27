"""
Write resolved data.
"""
import json
import os
import logging
from .apt_data import JsonSerializer
from .resolve_lists import PackageLists


logger = logging.getLogger('output')

def create_out_dir(config):
    os.makedirs(config['output']['directory'], exist_ok=True)


def write_repos(config, repos):
    """
    Dump APT metadata.
    """
    if 'apt_data_dump' not in config['output'] or config['output']['apt_data_dump'] == '':
        # no dump file configured, skip dumping APT metadata
        return

    create_out_dir(config)
    file = os.path.join(config['output']['directory'], config['output']['apt_data_dump'])
    logger.debug('Writing apt data dump to %s ...', file)
    with open(file, 'w') as f:
        json.dump(repos, f, indent=4, cls=JsonSerializer)


def write_package_lists(config, lists: PackageLists):
    """
    Write resolve package lists.
    """
    create_out_dir(config)
    
    packages = [lists.ecu_packages[key] for key in lists.ecu_packages.keys()]
    file = os.path.join(config['output']['directory'], config['output']['ecu_json'])
    with open(file, 'w') as f:
        json.dump(packages, f, indent=4, cls=JsonSerializer)

    packages = [lists.sdk_packages[key] for key in lists.sdk_packages.keys()]
    file = os.path.join(config['output']['directory'], config['output']['sdk_json'])
    with open(file, 'w') as f:
        json.dump(packages, f, indent=4, cls=JsonSerializer)

    file = os.path.join(config['output']['directory'], config['output']['missing'])
    with open(file, 'w') as f:
        s = ""
        for a in lists.missing_packages.keys():
            for p in lists.missing_packages[a]:
                s += f'{p} ({a})\n'
        f.write(s)
    
    file = os.path.join(config['output']['directory'], config['output']['broken'])
    with open(file, 'w') as f:
        s = ""
        for a in lists.broken_packages.keys():
            for p in lists.broken_packages[a]:
                s += f'{p} ({a})\n'
        f.write(s)
