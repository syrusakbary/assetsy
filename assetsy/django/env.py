
# Finally, we'd like to autoload the ``assets`` module of each Django.
import imp
from django.conf import settings
from assetsy.env import Environment
DEFAULT_PROCESSORS = {
    'cssmin':'assetsy.processors.CSSMin',
    'output':'assetsy.processors.Output',
    'merge':'assetsy.processors.Merge',
    'cssautoreg':'assetsy.processors.AutoregisterURL'
}

env = None

def get_env():
    global env
    if env is None:
        env = Environment(basepath=settings.ASSETSY_PATH)
        for name,processor in DEFAULT_PROCESSORS.iteritems():
            env.processor_manager[name] = processor

        autoload()
    return env

def reset():
    global env
    env = None

def register(*a, **kw):
    return get_env().register(*a, **kw)

def asset(*a, **kw):
    return get_env().asset(*a, **kw)


try:
    from django.utils import importlib
except ImportError:
    from assetsy.utils import importlib


_ASSETS_LOADED = False

def autoload():
    """Find assets by looking for an ``assets`` module within each
    installed application, similar to how, e.g., the admin autodiscover
    process works. This is were this code has been adapted from, too.

    Only runs once.

    TOOD: Not thread-safe!
    TODO: Bring back to status output via callbacks?
    """
    global _ASSETS_LOADED
    if _ASSETS_LOADED:
        return False

    # Import this locally, so that we don't have a global Django
    # dependency.
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for an assets.py inside that
        # app's package. We can't use os.path here -- recall that
        # modules may be imported different ways (think zip files) --
        # so we need to get the app's __path__ and look for
        # admin.py on that path.
        #if options.get('verbosity') > 1:
        #    print "\t%s..." % app,

        # Step 1: find out the app's __path__ Import errors here will
        # (and should) bubble up, but a missing __path__ (which is
        # legal, but weird) fails silently -- apps that do weird things
        # with __path__ might need to roll their own registration.
        try:
            app_path = importlib.import_module(app).__path__
        except AttributeError:
            #if options.get('verbosity') > 1:
            #    print "cannot inspect app"
            continue

        # Step 2: use imp.find_module to find the app's assets.py.
        # For some reason imp.find_module raises ImportError if the
        # app can't be found but doesn't actually try to import the
        # module. So skip this app if its assetse.py doesn't exist
        try:
            imp.find_module('assets', app_path)
        except ImportError:
            #if options.get('verbosity') > 1:
            #    print "no assets module"
            continue

        # Step 3: import the app's assets file. If this has errors we
        # want them to bubble up.
        importlib.import_module("%s.assets" % app)
        #if options.get('verbosity') > 1:
        #    print "assets module loaded"

    # Look for an assets.py at the project level
    try:
        importlib.import_module('assets')
    except ImportError:
        # not found, just ignore
        pass

    _ASSETS_LOADED = True
