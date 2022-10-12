# Copyright 2022 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Set of URL Helper Functions."""
from urllib import parse


def urljoin(base, url):
    """
    Resolve a `url` relative to `base`.

    Other than `urllib.parse.urljoin` this function supports relative URLs on SSH.

    >>> urljoin('https://domain.com/base/repo1.git', 'https://domain.com/base/repo2.git')
    'https://domain.com/base/repo2.git'
    >>> urljoin('https://domain.com/base/repo1.git/', 'repo2.git')
    'https://domain.com/base/repo1.git/repo2.git'
    >>> urljoin('https://domain.com/base/repo1.git', '../repo2.git')
    'https://domain.com/base/repo2.git'

    >>> urljoin('ssh://domain.com/base/repo1.git', 'ssh://domain.com/base/repo2.git')
    'ssh://domain.com/base/repo2.git'
    >>> urljoin('ssh://domain.com/base/repo1.git/', 'repo2.git')
    'ssh://domain.com/base/repo1.git/repo2.git'
    >>> urljoin('ssh://domain.com/base/repo1.git', '../repo2.git')
    'ssh://domain.com/base/repo2.git'

    >>> urljoin(None, 'repo2.git')
    'repo2.git'
    >>> urljoin(None, '../repo2.git')
    '../repo2.git'
    """
    if not base:
        return url

    urlparsed = parse.urlparse(url)
    if urlparsed.scheme:
        return url

    if not base.endswith("/"):
        base = f"{base}/"
    baseparsed = parse.urlparse(base)
    httpbase = parse.urlunparse(("http",) + baseparsed[1:])
    joined = parse.urljoin(httpbase, url)
    joinedparsed = parse.urlparse(joined)
    return parse.urlunparse((baseparsed.scheme,) + joinedparsed[1:])


def urlsub(base, name):
    """
    Create sub-url for `name` with suffix of `base`.

    >>> urlsub('https://domain.com/base/repo1', 'repo2')
    'repo2'
    >>> urlsub('https://domain.com/base/repo1.git', 'repo2')
    'repo2.git'
    >>> urlsub('https://domain.com/base/repo1.suffix', 'repo2')
    'repo2.suffix'
    >>> urlsub('https://domain.com/base/repo1.first.second', 'repo2')
    'repo2.second'
    >>> urlsub(None, 'repo2')
    'repo2'
    >>> urlsub(None, 'repo2.git')
    'repo2.git'
    """
    if not base:
        return name
    bpath = parse.urlparse(base).path
    bname = bpath.rsplit("/", 1)[1]
    try:
        _, bsuffix = bname.rsplit(".", 1)
    except ValueError:
        return name
    return f"{name}.{bsuffix}"
