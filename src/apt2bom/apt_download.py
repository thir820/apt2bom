"""
Download APT metadata form HTTP(s) servers.
"""
import requests
import io
import gzip
import logging


logger = logging.getLogger('apt_data')


def read_gz_url(url: str) -> str:
    """
    Read a gz compressed file from an URL.
    """
    response = requests.get(url)

    if response.status_code != 200:
        logger.error('Reading %s failed!', url)
        return []
    else:
        logger.debug('Reading %s: %d', url, response.status_code)

    file_stream = io.BytesIO(response.content)
    with gzip.GzipFile(fileobj=file_stream) as f:
        content = bytes.decode(f.read())
        return content.split('\n')


def read_url(url: str) -> list[str]:
    """
    Read a file from an URL.
    """
    response = requests.get(url)
    text = bytes.decode(response.content)
    return text.split('\n')


def get_distro_url(base: str, distro: str, path: str) -> str:
    """
    Create an APT metadata URL.
    """
    if base[-1] != '/':
        base += '/'

    if path.startswith('/'):
        path = path[1:]

    return f'{base}dists/{distro}/{path}'
