__all__ = ('AssetError', 'BuildError', 'FilterError',)


class ResourceError(Exception):
    pass

class ResourceNotFoundError(ResourceError):
    pass


class BuildError(ResourceError):
    pass


class ProcessorError(BuildError):
    pass