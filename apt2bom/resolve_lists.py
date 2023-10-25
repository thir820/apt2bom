"""
Generate package lists from APT metadata.
"""
import logging
from .apt_data import AptRepository, Package


class PackageLists:
    """
    Data class for all resolved package lists.
    """
    def __init__(self):
        self.ecu_packages: dict[str, Package] = {}
        self.sdk_packages: dict[str, Package] = {}
        self.missing_packages: list[str] = []
        self.broken_packages: list[str] = []


def resolve_package(repos: list[AptRepository], pkg: str):
    """
    Search a given package in the given APT repositories.
    """
    if not pkg or pkg == '':
        logging.info('Invalid package name: |%s|', pkg)
        return

    for repo in repos:
        for component_name in repo.components.keys():
            component = repo.components[component_name]
            if pkg in component.packages:
                logging.debug("Package %s found in %s %s.", pkg, repo, component)
                return component.packages[pkg]
    
    logging.error('Package %s not found!', pkg)
    return None


def resolve_rt_dependencies_recursive(repos: list[AptRepository],
                                 packages: dict[str, Package],
                                 missing_packages: list[str],
                                 package_name: str):
    """
    Recursive resolve runtime dependencies.
    """
    package = packages[package_name]
    root_type = package.pkg_type.split('_')[0]
    dep_type = f'{root_type}_DEP'
    
    for (dep, _) in package.depends:
        if dep in packages:
            # package was already resolved or is root package
            continue

        dep_package = resolve_package(repos, dep)
        if dep_package:
            dep_package.pkg_type = dep_type
            packages[dep] = dep_package
            #recursive resolve dependencies
            for (dep, _) in dep_package.depends:
                if dep not in packages:
                    dep_dep_package = resolve_package(repos, dep)
                    if dep_dep_package:
                        dep_dep_package.pkg_type = dep_type
                        packages[dep] = dep_dep_package
                        packages, missing_packages = resolve_rt_dependencies_recursive(
                            repos, packages, missing_packages, dep)
                    else:
                        logging.error('Package %s not found!', package_name)
                        missing_packages.append(package_name)
        else:
            logging.error('Package %s (%s) not found!', dep, package.pkg_type)
            missing_packages.append(package_name)

    return packages, missing_packages


def resolve_runtime_dependencies(repos: list[AptRepository],
                                 packages: dict[str, Package],
                                 missing_packages: list[str],
                                 package_names: list[str]):
    """
    Add all runtime dependencies
    """
    for pkg in package_names:
        package = packages[pkg]
        logging.debug('Resolving %d runtime depends of %s: %s',
                     len(package.depends), pkg,
                     [name for name, _ in package.depends])
        
        packages, missing_packages = resolve_rt_dependencies_recursive(
            repos, packages, missing_packages, pkg)

    logging.info('Found %d ECU packages', len(packages))

    return packages, missing_packages


def resolve_build_time_dependencies(repos: list[AptRepository],
                                 ecu_packages: dict[str, Package],
                                 missing_packages: list[str]):
    """
    Add all build-time dependencies
    """
    sdk_packages: dict[str, Package] = {}
    broken_packages: list[str] = []

    package_names = []
    for pkg in ecu_packages.keys():
        package = ecu_packages[pkg]
        root_type = package.pkg_type.split('_')[0]
        dep_type = f'{root_type}SDK'

        if not package.source:
            logging.error('No source metadata for %s!', pkg)
            broken_packages.append(pkg)
            continue

        # find build-time dependencies of ECU packages
        for (dep, _) in package.source.build_depends:
            dep_package = resolve_package(repos, dep)
            if dep_package:
                dep_package.pkg_type = dep_type
                sdk_packages[dep] = dep_package
                package_names.append(dep)
            else:
                logging.error('Missing SDK package %s (%s)!', dep, dep_type)
                missing_packages.append(dep)
                continue
    
    logging.debug('Found %d root SDK packages. %d', len(sdk_packages), len(package_names))

    # get runtime dependencies of SDK packages
    sdk_packages, missing_packages = resolve_runtime_dependencies(
        repos, sdk_packages, missing_packages, package_names)
    
    return sdk_packages, missing_packages, broken_packages


def resolve_package_lists(repos: list[AptRepository], 
                          prod: list[str],
                          dev: list[str]) -> PackageLists:
    """
    Search the metadata for the root packages,
    and all runtime and build-time dependencies.
    """
    ecu_packages: dict[str, Package] = {}
    
    # join package name with package type
    packages = [(pkg, 'PROD') for pkg in prod] + [(pkg, 'DEV') for pkg in dev]

    found_packages = []
    missing_packages = []
    for pkg, pkg_type in packages:
        package = resolve_package(repos, pkg)
        if package:
            package.pkg_type = pkg_type
            ecu_packages[pkg] = package
            found_packages.append(pkg)
        else:
            logging.error('Package %s (%s) not found!', pkg, pkg_type)
            missing_packages.append(pkg)

    logging.info("Resolved %d packages.", len(packages))

    ecu_packages, missing_packages = resolve_runtime_dependencies(
        repos, ecu_packages, missing_packages, found_packages)
    
    sdk_packages, missing_packages, broken_packages = resolve_build_time_dependencies(
        repos, ecu_packages, missing_packages)

    logging.info('Resolved %d ECU packages, %d SDK packages.',
                len(ecu_packages), len(sdk_packages))
    logging.info('Missing packages: %s', missing_packages)
    logging.info('Broken packages: %s', broken_packages)

    lists = PackageLists()
    lists.ecu_packages = ecu_packages
    lists.sdk_packages = sdk_packages
    lists.broken_packages = broken_packages
    lists.missing_packages = missing_packages

    return lists
