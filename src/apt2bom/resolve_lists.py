"""
Generate package lists from APT metadata.
"""
import logging
from .apt_data import AptRepository, Package


logger = logging.getLogger('resolve_lists')

class PackageLists:
    """
    Data class for all resolved package lists.
    """
    def __init__(self):
        self.ecu_packages: dict[str, dict[str, Package]] = {}
        self.sdk_packages: dict[str, dict[str, Package]] = {}
        self.missing_packages: dict[str, set[str]] = {}
        self.broken_packages: dict[str, set[str]] = {}


def resolve_package(repos: list[AptRepository], pkg: str, arch: str) -> Package | None:
    """
    Search a given package in the given APT repositories.
    """
    if not pkg or pkg == '':
        logger.info('Invalid package name: |%s|', pkg)
        return
    
    if ':' in pkg:
        pkg = pkg.split(':', maxsplit=1)[0]

    # TODO: repo priorities
    for repo in repos:
        for component_name in repo.components.keys():
            component = repo.components[component_name]
            if pkg in component.packages:
                if arch in component.packages[pkg].keys():
                    if component.packages[pkg][arch]:
                        logger.debug('Package %s (%s) found in %s %s.',
                                    pkg, arch, repo, component)
                        # TODO: criteria for "right" package
                        return component.packages[pkg][arch][0]

    logger.error('Package %s not found!', pkg)
    return None


def resolve_rt_dependencies_recursive(repos: list[AptRepository],
                                 packages: dict[str, Package],
                                 missing_packages: set[str],
                                 package_name: str,
                                 arch: str):
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

        dep_package = resolve_package(repos, dep, arch)
        if dep_package:
            if dep_package.pkg_type is None:
                dep_package.pkg_type = dep_type
            packages[dep] = dep_package
            #recursive resolve dependencies
            for (dep, _) in dep_package.depends:
                if dep not in packages:
                    dep_dep_package = resolve_package(repos, dep, arch)
                    if dep_dep_package:
                        if dep_dep_package.pkg_type is None:
                            dep_dep_package.pkg_type = dep_type
                        packages[dep] = dep_dep_package
                        packages, missing_packages = resolve_rt_dependencies_recursive(
                            repos, packages, missing_packages, dep, arch)
                    else:
                        logger.debug('Package %s not found!', package_name)
                        missing_packages.add(package_name)
        else:
            logger.error('Package %s (%s) not found!', dep, package.pkg_type)
            missing_packages.add(package_name)

    return packages, missing_packages


def resolve_runtime_dependencies(repos: list[AptRepository],
                                 packages: dict[str, Package],
                                 missing_packages: set[str],
                                 package_names: list[str],
                                 arch: str):
    """
    Add all runtime dependencies
    """
    for pkg in package_names:
        package = packages[pkg]
        logger.debug('Resolving %d runtime depends of %s: %s',
                     len(package.depends), pkg,
                     [name for name, _ in package.depends])
        
        packages, missing_packages = resolve_rt_dependencies_recursive(
            repos, packages, missing_packages, pkg, arch)

    logger.info('Found %d packages', len(packages))

    return packages, missing_packages


def resolve_build_time_dependencies(repos: list[AptRepository],
                                 ecu_packages: dict[str, Package],
                                 missing_packages: set[str],
                                 arch: str):
    """
    Add all build-time dependencies
    """
    sdk_packages: dict[str, Package] = {}
    broken_packages: set[str] = set()

    package_names = []
    for pkg in ecu_packages.keys():
        package = ecu_packages[pkg]
        root_type = package.pkg_type.split('_')[0]
        if not root_type.endswith('SDK'):
            dep_type = f'{root_type}SDK'
        else:
            dep_type = root_type

        if not package.source:
            logger.error('No source metadata for %s!', pkg)
            broken_packages.add(pkg)
            continue

        # find build-time dependencies of ECU packages
        for (dep, _) in package.source.build_depends:
            dep_package = resolve_package(repos, dep, arch)
            if dep_package:
                if dep_package.pkg_type is None:
                    dep_package.pkg_type = dep_type
                sdk_packages[dep] = dep_package
                package_names.append(dep)
            else:
                logger.error('Missing SDK package %s (%s)!', dep, dep_type)
                missing_packages.add(dep)
                continue
    
    logger.debug('Found %d root SDK packages. %d', len(sdk_packages), len(package_names))

    # get runtime dependencies of SDK packages
    sdk_packages, missing_packages = resolve_runtime_dependencies(
        repos, sdk_packages, missing_packages, package_names, arch)
    
    return sdk_packages, missing_packages, broken_packages


def resolve_package_lists(repos: list[AptRepository],
                          architectures: list[str],
                          prod: list[str],
                          dev: list[str],
                          sdk: list[str]) -> PackageLists:
    """
    Search the metadata for the root packages,
    and all runtime and build-time dependencies.
    """
    ecu_arch_packages: dict[str, dict[str, Package]] = {}
    sdk_arch_packages: dict[str, dict[str, Package]] = {}
    missing_arch_packages: dict[str, set[str]] = {}
    broken_arch_packages: dict[str, set[str]] = {}

    # join package name with package type
    packages = [(pkg, 'PROD') for pkg in prod]
    packages += [(pkg, 'DEV') for pkg in dev]
    
    for arch in architectures:
        missing_packages = set()
        found_packages = []
        ecu_packages: dict[str, Package] = {}
        for pkg, pkg_type in packages:
            package = resolve_package(repos, pkg, arch)
            if package:
                if package.pkg_type is None:
                    package.pkg_type = pkg_type
                ecu_packages[pkg] = package
                found_packages.append(pkg)
            else:
                logger.error('Package %s (%s) not found!', pkg, pkg_type)
                missing_packages.add(pkg)

        logger.info('Resolved %d packages.', len(packages))

        ecu_packages, missing_packages = resolve_runtime_dependencies(
            repos, ecu_packages, missing_packages, found_packages, arch)
        
        sdk_packages, missing_packages, broken_packages = resolve_build_time_dependencies(
            repos, ecu_packages, missing_packages, arch)

        logger.info('Resolved %d ECU packages, %d SDK packages.',
                    len(ecu_packages), len(sdk_packages))
        logger.info('Missing packages: %s', missing_packages)
        logger.info('Broken packages: %s', broken_packages)

        ecu_arch_packages[arch] = ecu_packages
        sdk_arch_packages[arch] = sdk_packages
        missing_arch_packages[arch] = missing_packages
        broken_arch_packages[arch] = broken_packages

    # resolve SDK packages
    packages = [(pkg, 'SDK') for pkg in sdk]
    for arch in architectures:
        missing_packages = set()
        found_packages = []
        sdk_packages: dict[str, Package] = {}
        for pkg, pkg_type in packages:
            package = resolve_package(repos, pkg, arch)
            if package:
                if package.pkg_type is None:
                    package.pkg_type = pkg_type
                sdk_packages[pkg] = package
                found_packages.append(pkg)
            else:
                logger.error('Package %s (%s) not found!', pkg, pkg_type)
                missing_packages.add(pkg)

        logger.info('Resolved %d packages.', len(packages))

        sdk_packages, missing_packages = resolve_runtime_dependencies(
            repos, sdk_packages, missing_packages, found_packages, arch)

        logger.info('Resolved %d SDK packages.', len(sdk_packages))
        logger.info('Missing %d packages.', len(missing_packages))
        logger.info('Broken %d packages.', len(broken_packages))

        sdk_arch_packages[arch].update(sdk_packages)

        missing_arch_packages[arch].update(missing_packages)
        broken_arch_packages[arch].update(broken_packages)

    lists = PackageLists()
    lists.ecu_packages = ecu_arch_packages
    lists.sdk_packages = sdk_arch_packages
    lists.broken_packages = broken_arch_packages
    lists.missing_packages = missing_arch_packages

    return lists
