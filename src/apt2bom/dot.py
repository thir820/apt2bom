"""
Export ECU packages as dot graph.
"""
import os
from .resolve_lists import PackageLists
from .apt_data import Package

def write_ecu_runtime_dot_graph(config, lists: PackageLists):
    """
    Write package lists as Excel file.
    """
    for arch in config['packages']['architectures']:
        content = "digraph {\n"

        if arch in lists.ecu_packages:
            for name in lists.ecu_packages[arch]:
                package = lists.ecu_packages[arch][name]
                depends = ' '.join([f'"{name}"' for name, _ in package.depends])
                content += f'    "{package.package}" -> {{{depends}}}\n'
        
        content += '}'

        file = os.path.join(
            config['output']['directory'],
            f'runtime_deps_{arch}.dot')
        with open(file, 'w') as f:
            f.write(content)
    
        os.system(f'dot -Tsvg {file} > {file}.svg')


def write_ecu_build_time_dot_graph(config, lists: PackageLists):
    """
    Write package lists as Excel file.
    """
    for arch in config['packages']['architectures']:
        content = "digraph {\n"

        if arch in lists.ecu_packages:
            for name in lists.ecu_packages[arch]:
                package = lists.ecu_packages[arch][name]
                if package.source:
                    build_depends = ' '.join(
                        [f'"{name}"' for name, _ in package.source.build_depends])
                    content += f'    "{package.package}" -> {{{build_depends}}}\n'
        
        content += '}'

        file = os.path.join(
            config['output']['directory'],
            f'build_time_deps_{arch}.dot')
        with open(file, 'w') as f:
            f.write(content)
        
        os.system(f'dot -Tsvg {file} > {file}.svg')
