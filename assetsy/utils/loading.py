# from django.core.exceptions import ImproperlyConfigured

try:
    from django.utils import importlib
except ImportError:
    from assetsy.utils import importlib


def import_class(path):
    path_bits = path.split('.')
    # Cut off the class name at the end.
    class_name = path_bits.pop()
    module_path = '.'.join(path_bits)
    module_itself = importlib.import_module(module_path)

    if not hasattr(module_itself, class_name):
        raise ImportError("The Python module '%s' has no '%s' class." % (module_path, class_name))

    return getattr(module_itself, class_name)


# Load the search backend.
def load_backend(full_backend_path):
    """
    Loads a backend for storing assets.
    """
    path_bits = full_backend_path.split('.')

    if len(path_bits) < 2:
        raise Exception("The provided backend '%s' is not a complete Python path to a BaseEngine subclass." % full_backend_path)

    return import_class(full_backend_path)

def load_processor(full_processor_path):
    """
    Loads a backend for storing assets.
    """
    path_bits = full_processor_path.split('.')

    if len(path_bits) < 2:
        raise Exception("The provided processor '%s' is not a complete Python path to a Processor subclass." % full_processor_path)

    return import_class(full_processor_path)


class StorageHandler(object):
    def __init__(self, storages_info):
        self.storages_info = storages_info
        self._storages = {}
        self._index = None

    def ensure_defaults(self, alias):
        try:
            conn = self.storages_info[alias]
        except KeyError:
            raise Exception("The key '%s' isn't an available connection." % alias)

        if not conn.get('ENGINE'):
            conn['ENGINE'] = 'superassets.backends.local_backend.LocalEngine'

    def __getitem__(self, key):
        if key in self._storages:
            return self._storages[key]

        self.ensure_defaults(key)
        self._storages[key] = load_backend(self.storages_info[key]['ENGINE'])(using=key)
        return self._storages[key]

    def all(self):
        return [self[alias] for alias in self._storages]
