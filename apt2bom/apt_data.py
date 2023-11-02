"""
APT metadata related classes.
"""
from __future__ import annotations

import json
import logging


logger = logging.getLogger('apt_data')

class SourceFile:
    """
    A source file is part of a Debian source package (dsc).

    One example are the tar-ball files containing the sources.
    """
    def __init__(self):
        self.name: str = None
        self.size: int = -1
        self.md5: str = None
        self.sha1: str = None
        self.sha256: str = None
        self.sha512: str = None

    def __repr__(self) -> str:
        return f'SourceFile({self.name})'


class Source:
    """
    A source represents the metadata of an APT source package.
    """
    def __init__(self, repository: AptRepository, component: Component):
        self.package: str = None
        self.format: str = None
        self.binaries: list[str] = []
        self.architecture: str = None
        self.version: str = None
        self.priority: str = None
        self.section: str = None
        self.maintainer: str = None
        self.standards_version: str = None
        self.build_depends: list[tuple[str, str]] = []
        self.homepage: str = None
        self.vcs_browser: str = None
        self.vcs_git: str = None
        self.directory: str = None
        self.package_list: list[tuple[str, list[str]]] = []
        self.files: dict[str, SourceFile] = {}
        self.repository: AptRepository = repository
        self.component: Component = component

    def to_record(self) -> dict[str, str]:
        data = self.__dict__.copy()
        data['binaries'] = ', '.join(self.binaries)
        data['build_depends'] = ', '.join([f'{name} {version}' for name, version in self.build_depends])
        data['package_list'] = ', '.join([name for name, _ in self.package_list])
        data['files'] = ', '.join(self.files.keys())

        del data['repository']
        
        for key, value in self.repository.to_data_non_recursive().items():
            if key not in data:
                data[key] = value
        
        data['repository_version'] = self.repository.version
        
        del data['component']

        data['component'] = self.component.name

        return data
        

    def __repr__(self) -> str:
        return f'Source({self.package})'
    
    def to_data(self) -> dict:
        data = self.__dict__.copy()
        data['files'] = [self.files[key] for key in self.files.keys()]
        del data['repository']
        del data['component']
        return data


class Package:
    """
    A package represents the metadata of an APT binary package.
    """
    def __init__(self, repository: AptRepository, component: Component):
        self.package: str = None
        self.architecture: str = None
        self.version: str = None
        self.priority: str = None
        self.section: str = None
        self.origin: str = None
        self.maintainer: str = None
        self.original_maintainer: str = None
        self.bugs: str = None
        self.installed_size: int = -1
        self.depends: list[tuple[str, str]] = []
        self.recommends: str = None
        self.suggests: str = None
        self.filename: str = None
        self.size: int = -1
        self.md5: str = None
        self.sha1: str = None
        self.sha256: str = None
        self.sha512: str = None
        self.homepage: str = None
        self.description: str = None
        self.task: list[str] = []
        self.description_md5: str = None
        self.source: Source = None
        self.pkg_type: str = None
        self.repository: AptRepository = repository
        self.component: Component = component

    def to_record(self) -> dict[str, str]:
        data = self.__dict__.copy()
        data['depends'] = ', '.join([f'{name} {version}' for name, version in self.depends])
        data['task'] = ', '.join(self.task)

        if self.source:
            del data['source']

            for key, value in self.source.to_record().items():
                data[f'source_{key}'] = value

        del data['repository']
        
        for key, value in self.repository.to_data_non_recursive().items():
            if key not in data:
                data[key] = value
        
        data['repository_version'] = self.repository.version
        data['repository_description'] = self.repository.description
        
        del data['component']

        data['component'] = self.component.name

        return data


    def __repr__(self) -> str:
        return f'Package({self.package}, {self.filename})'
    
    def to_data(self) -> dict:
        data = self.__dict__.copy()
        if self.source:
            data['source'] = self.source.to_data()
        data['repository'] = self.repository.to_data_non_recursive()
        data['component'] = self.component.to_data_non_recursive()
        return data


class Index:
    def __init__(self):
        self.url: str = None
        self.size: int = -1
        self.checksum: str = None

    def __repr__(self) -> str:
        return f'Index({self.url})'


class Component:
    def __init__(self):
        self.name: str = None
        self.indices: list[Index] = []
        self.packages: dict[str, dict[str, list[Package]]] = {}
        self.sources: dict[str, Source] = {}

    def __repr__(self) -> str:
        return f'Component({self.name}, {len(self.indices)} indices)'
    
    def to_data(self) -> dict:
        data = self.__dict__.copy()
        data['packages'] = [self.packages[key] for key in self.packages.keys()]
        return data
    
    def to_data_non_recursive(self) -> dict:
        """
        Convert class to non-recursive data object.
        """
        data = self.to_data()
        del data['packages']
        del data['sources']
        del data['indices']
        return data


class AptRepository:
    def __init__(self):
        self.url: str = None
        self.origin: str = None
        self.label: str = None
        self.suite: str = None
        self.version: str = None
        self.codename: str = None
        self.date: str = None
        self.architectures: list[str] = []
        self.component_names: list[str] = []
        self.description: str = None
        self.components: dict[str, Component] = {}

    def __repr__(self) -> str:
        return f'AptRepository({self.url}, {self.origin}, {self.suite}, {self.version})'
    
    def to_data(self) -> dict:
        data = self.__dict__.copy()
        data['components'] = [self.components[key] for key in self.components.keys()]
        return data
    
    def to_data_non_recursive(self) -> dict:
        """
        Convert class to non-recursive data object.
        """
        data = self.to_data()
        del data['components']
        del data['architectures']
        del data['component_names']
        return data


class JsonSerializer(json.JSONEncoder):
    def default(self, o):
        to_data = getattr(o, 'to_data', None)
        if callable(to_data):
            return o.to_data()

        if o.__dict__:
            return o.__dict__

        logger.error('No serialization for %s (%s)!', type(o), str(o)[30:])
        return None
