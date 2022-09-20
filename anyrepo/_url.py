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
