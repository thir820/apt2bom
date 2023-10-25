"""
APT metadata parsing.
"""
import re
import logging
from .apt_data import AptRepository, Index, Component, Package, Source, SourceFile
from .apt_download import get_distro_url, read_gz_url, read_url


def parse_apt_repository(
        url: str,
        distribution: str,
        components: list[str] | None,
        content: list[str]) -> AptRepository:
    """
    Parse APT metadata from "Release" file.
    """
    repo = AptRepository()
    repo.url = url

    md5_list = False
    for line in content:
        if not md5_list:
            if line.startswith('Origin:'):
                repo.origin = line[7:].strip()
            elif line.startswith('Label:'):
                repo.label = line[6:].strip()
            elif line.startswith('Suite:'):
                repo.suite = line[6:].strip()
            elif line.startswith('Version:'):
                repo.version = line[8:].strip()
            elif line.startswith('Codename:'):
                repo.codename = line[9:].strip()
            elif line.startswith('Date:'):
                repo.date = line[5:].strip()
            elif line.startswith('Architectures:'):
                repo.architectures = line[14:].strip().split(' ')
            elif line.startswith('Components:'):
                repo.component_names = line[11:].strip().split(' ')
            elif line.startswith('Description:'):
                repo.description = line[12:].strip()
            elif line.startswith('MD5Sum:'):
                md5_list = True
        else:
            if not line.startswith(' '):
                break

            _, md5, size, path = re.split("\s+", line)
            if '/' in path:
                index = Index()
                index.checksum = md5
                index.size = int(size)
                index.url = get_distro_url(url, distribution, path)

                component = path.split('/')[0]

                if components is not None and component not in components:
                    continue

                if component not in repo.components:
                    repo.components[component] = Component()
                    repo.components[component].name = component
                    repo.components[component].indices = []
                
                repo.components[component].indices.append(index)

                logging.debug("%s %s", component, index)

    logging.debug("Repository: %s", repo)
    return repo


def parse_package_index(
        url: str, base_url: str, repo: AptRepository,
        component: Component) -> dict[str, Package]:
    """
    Read an binary package index "Packages.gz" file.
    """
    if base_url[-1] != '/':
        base_url += '/'

    packages: dict[str, Package] = {}

    lines = read_gz_url(url)

    package = Package(repo, component)
    for line in lines:
        if line.strip() == '':
            # packages are separated by empty lines
            package = Package(repo, component)
            continue
        
        if line.startswith('Package:'):
            package.package = line[8:].strip()
        elif line.startswith('Architecture:'):
            package.architecture = line[13:].strip()
        elif line.startswith('Version:'):
            package.version = line[8:].strip()
        elif line.startswith('Priority:'):
            package.priority = line[9:].strip()
        elif line.startswith('Section:'):
            package.section = line[8:].strip()
        elif line.startswith('Origin:'):
            package.origin = line[7:].strip()
        elif line.startswith('Maintainer:'):
            package.maintainer = line[11:].strip()
        elif line.startswith('Original-Maintainer:'):
            package.original_maintainer = line[20:].strip()
        elif line.startswith('Bugs:'):
            package.bugs = line[5:].strip()
        elif line.startswith('Installed-Size:'):
            package.installed_size = int(line[15:].strip())
        elif line.startswith('Depends:'):
            depends = line[8:].strip().split(',')
            for depend in depends:
                depend = depend.strip()
                if ' ' in depend:
                    name, version = depend.split(' ', maxsplit=1)
                    package.depends.append((name, version))
                elif depend.strip() != '':
                    package.depends.append((depend, ''))
        elif line.startswith('Recommends:'):
            package.recommends = line[11:].strip()
        elif line.startswith('Suggests:'):
            package.suggests = line[9:].strip()
        elif line.startswith('Filename:'):
            path = line[9:].strip()
            package.filename = f'{base_url}{path}'
        elif line.startswith('Size:'):
            package.size = int(line[5:].strip())
        elif line.startswith('MD5sum:'):
            package.md5 = line[7:].strip()
        elif line.startswith('SHA1:'):
            package.sha1 = line[4:].strip()
        elif line.startswith('SHA256:'):
            package.sha256 = line[7:].strip()
        elif line.startswith('SHA512:'):
            package.sha512 = line[7:].strip()
        elif line.startswith('Homepage:'):
            package.homepage = line[9:].strip()
        elif line.startswith('Description:'):
            package.description = line[12:].strip()
        elif line.startswith('Task:'):
            package.task = [task.strip() for task in line[5:].strip().split(',')]
        elif line.startswith('Description-md5:'):
            package.description_md5 = line[16:].strip()

        if package.package:
            packages[package.package] = package

    return packages


def parse_source_index(
        url: str, base_url: str, repo: AptRepository,
        component: Component) -> dict[str, Package]:
    """
    Read package source index.
    """
    if base_url[-1] != '/':
        base_url += '/'

    sources: dict[str, Package] = {}

    lines = read_gz_url(url)
    source = Source(repo, component)
    package_list = False
    files_list = False
    checksum: str = 'md5'
    for line in lines:
        if line.strip() == '':
            source = Source(repo, component)
            continue
        
        if line.startswith(' ') and (package_list or files_list):
            if package_list:
                 parts = re.split("\s+", line.strip())
                 source.package_list.append((parts[0], parts[1:]))

            elif files_list:
                _, check, size, filename = re.split("\s+", line)
                
                if filename not in source.files:
                    file = SourceFile()
                    file.name = f'{base_url}{source.directory}/{filename}'
                    file.size = int(size)
                    source.files[filename] = file
                
                if checksum == 'md5':
                    source.files[filename].md5 = check
                elif checksum == 'Sha1':
                    source.files[filename].sha1 = check
                elif checksum == 'Sha256':
                    source.files[filename].sha256 = check
                elif checksum == 'Sha512':
                    source.files[filename].sha512 = check
                else:
                    logging.warning("Unknown checksum type %s", checksum)

        else:
            package_list = False
            files_list = False

            if line.startswith('Package:'):
                source.package = line[8:].strip()
            elif line.startswith('Format:'):
                source.format = line[7:].strip()
            elif line.startswith('Binary:'):
                source.binaries = [binary.strip() for binary in line[7:].strip().split(',')]
            elif line.startswith('Architecture:'):
                source.architecture = line[13:].strip()
            elif line.startswith('Version:'):
                source.version = line[8:].strip()
            elif line.startswith('Priority:'):
                source.priority = line[9:].strip()
            elif line.startswith('Section:'):
                source.section = line[8:].strip()
            elif line.startswith('Maintainer:'):
                source.maintainer = line[11:].strip()
            elif line.startswith('Standards-Version:'):
                source.standards_version = line[18:].strip()
            elif line.startswith('Build-Depends:'):
                depends: list[(str, str)] = []
                for depend in line[14:].strip().split(','):
                    depend = depend.strip()
                    if ' ' in depend:
                        name, version = depend.split(' ', maxsplit=1)
                        depends.append((name, version))
                    elif depend.strip != '':
                        depends.append((depend, ''))
                source.build_depends = depends
            elif line.startswith('Homepage:'):
                source.homepage = line[9:].strip()
            elif line.startswith('Vcs-Browser:'):
                source.vcs_browser = line[12:].strip()
            elif line.startswith('Vcs-Git:'):
                source.vcs_git = line[8:].strip()
            elif line.startswith('Directory:'):
                source.directory = line[10:].strip()
            elif line.startswith('Package-List:'):
                package_list = True
            elif line.startswith('Files:'):
                files_list = True
            elif line.startswith('Checksums-'):
                files_list = True
                checksum = line.strip()[10:-1]

        if source.package:
            sources[source.package] = source

    return sources


def scan_apt_repository(
        url: str,
        distribution: str,
        architectures: list[str] | None = ['amd64', 'arm64'],
        components: list[str] | None = ['main', 'universe']
    ) -> AptRepository:
    """
    Read all packages and sources from the given APT repository.
    """
    logging.info('Parsing repository %s %s %s %s',
                url, distribution, architectures, components)
    
    release = get_distro_url(url, distribution, 'Release')
    
    content = read_url(release)
    repo = parse_apt_repository(url, distribution, components, content)

    if components is None or components == []:
        components = repo.component_names
    
    if architectures is None or architectures == []:
        architectures = repo.architectures
    
    for component in components:
        if not component in repo.components:
            logging.warning("Component %s not found in repository %s", component, repo)
            continue

        comp = repo.components[component]

        for arch in architectures:
            index_folder = f'binary-{arch}'

            for index in comp.indices:
                if index_folder in index.url and 'Packages.gz' in index.url:
                    logging.debug("Parsing %s", index)
                    packages = parse_package_index(index.url, url, repo, component)
                    for package in packages.keys():
                        if comp.packages.get(package) is not None:
                            logging.warning("Duplicate package %s in %s", package, index.url)
                        else:
                            comp.packages[package] = packages[package]

        repo.components[component] = comp

        for index in comp.indices:
            if 'source' in index.url and 'Sources.gz' in index.url:
                logging.debug("Parsing %s", index)
                sources = parse_source_index(index.url, url, repo, component)
                for source in sources.keys():
                    if comp.sources.get(source) is not None:
                        logging.warning("Duplicate source %s in %s", package, index.url)
                    else:
                        comp.sources[source] = sources[source]

        repo.components[component] = comp

        for package in comp.packages.keys():
            for source_name in comp.sources.keys():
                source = comp.sources[source_name]
                if package in source.binaries:
                    comp.packages[package].source = source
                    break

        repo.components[component] = comp

        logging.info("Component %s: %d packages, %d sources.", comp.name, len(comp.packages), len(comp.sources))
    
    return repo


def scan_repositories(config) -> list[AptRepository]:
    """
    Read all packages and sources from all given APT repositories.
    """
    repos: list[AptRepository] = []
    for repository in config['repositories']:
        architectures = ['amd64', 'arm64']
        components = ['main', 'universe']
        
        if 'architectures' in repository:
            architectures =  repository['architectures']

        if 'components' in repository:
            components = repository['components']
        
        logging.debug('Scanning apt repository %s', repository['url'])

        repo = scan_apt_repository(
            url=repository['url'],
            distribution=repository['distribution'],
            architectures=architectures,
            components=components
        )
        repos.append(repo)
    
    return repos
