"""
Write resolved data.
"""
import json
import os
from .apt_data import JsonSerializer
from .resolve_lists import PackageLists


def create_out_dir(config):
    os.makedirs(config['dir-out'], exist_ok=True)


def write_repos(config, repos):
    """
    Dump APT metadata.
    """
    if 'repositories-dump' not in config or config['repositories-dump'] == '':
        # no dump file configured, skip dumping APT metadata
        return

    create_out_dir(config)
    file = os.path.join(config['dir-out'], config['repositories-dump'])
    with open(file, 'w') as f:
        json.dump(repos, f, indent=4, cls=JsonSerializer)


def write_package_lists(config, lists: PackageLists):
    """
    Write resolve package lists.
    """
    create_out_dir(config)
    
    packages = [lists.ecu_packages[key] for key in lists.ecu_packages.keys()]
    file = os.path.join(config['dir-out'], config['ecu-json-out'])
    with open(file, 'w') as f:
        json.dump(packages, f, indent=4, cls=JsonSerializer)

    packages = [lists.sdk_packages[key] for key in lists.sdk_packages.keys()]
    file = os.path.join(config['dir-out'], config['sdk-json-out'])
    with open(file, 'w') as f:
        json.dump(packages, f, indent=4, cls=JsonSerializer)

    file = os.path.join(config['dir-out'], config['missing-out'])
    with open(config['missing-out'], 'w') as f:
        f.write('\n'.join(lists.missing_packages))
    
    file = os.path.join(config['dir-out'], config['broken-out'])
    with open(config['broken-out'], 'w') as f:
        f.write('\n'.join(lists.broken_packages))
