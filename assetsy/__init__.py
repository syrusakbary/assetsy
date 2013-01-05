"""
Assetsy
~~~~~~~~~~~

`Assetsy <http://github.com/syrusakbary/assetsy>` is a vitamined package for 
minify, merge, optimize and versioning your web resources in `Django <http://www.djangoproject.com/>`

Assetsy supports a variety of different filters including YUI, jsmin, jspacker, CSS tidy, and the
most important... can manage automatically sprites for you.
:copyright: 2011 by Syrus Akbary Nieto
:license: BSD, see LICENSE for more details.
"""

import os
#from assetsy.constants import DEFAULT_ALIAS, IF_DEBUG, IF_NOT_DEBUG
from assetsy.utils import loading
from assetsy.env import Environment

__all__ = ('__version__', '__build__', '__docformat__', 'get_revision','register','Environment')
__version__ = (1,0,0,'alpha')
__author__ = 'Syrus Akbary Nieto'
__docformat__ = 'restructuredtext en'


def _get_git_revision(path):
    revision_file = os.path.join(path, 'refs', 'heads', 'master')
    if not os.path.exists(revision_file):
        return None
    fh = open(revision_file, 'r')
    try:
        return fh.read()
    finally:
        fh.close()

def get_revision():
    """
    :returns: Revision number of this branch/checkout, if available. None if
        no revision number can be determined.
    """
    package_dir = os.path.dirname(__file__)
    checkout_dir = os.path.normpath(os.path.join(package_dir, '..'))
    path = os.path.join(checkout_dir, '.git')
    if os.path.exists(path):
        return _get_git_revision(path)
    return None

__build__ = get_revision()



# if not hasattr(settings, 'ASSETSY_STORAGES'):
#    raise ImproperlyConfigured('The ASSETSY_STORAGES setting is required.')
# if DEFAULT_ALIAS not in settings.ASSETSY_STORAGES:
#    raise ImproperlyConfigured("The default alias '%s' must be included in the ASSETSY_STORAGES setting." % DEFAULT_ALIAS)

# storages = loading.StorageHandler(settings.ASSETSY_STORAGES)

# from djinja.template import get_env as djinja_get_env

# djinja_get_env().assets_environment = get_env()
