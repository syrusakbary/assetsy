"""resources can be processed through one or multiple processors, modifying their
contents (think minification, compression).
"""
from assetsy.utils.managers import check_name
from assetsy.assets import AssetSingle, AssetCollection
from copy import copy
from assetsy.utils.loading import load_processor

__all__ = ('Processor', 'CallableProcessor')

from types import ClassType
from assetsy.exceptions import ProcessorError, BuildError

class ProcessorCollection (object):
    def __init__(self,*processors):
        self._processors = []
        for processor in processors:
            self.add(processor)

    def add (self,processor):
        self._processors.append(processor)

    def __add__(self, processor):
        collection = ProcessorCollection()
        collection._processors = self._processors + processor._processors
        return collection

    def process(self,asset):
        for processor in self._processors:
            asset = processor(asset)
        return asset

    def __repr__ (self):
        return "<ProcessorCollection processors=%s>"%(self._processors)


class ProcessorManager:
    
    def __init__(self,environment):
        self.environment = environment
        self._processors = {}
        self._processors_errors = {}

    def __getitem__ (self,name):
        if name in self._processors_errors:
            raise self._processors_errors[name]
        if name in self:
            return self._processors[name]
            # raise Exception('There is no "%s" processor.'%name)
        return name

    def __contains__ (self,name):
        return name in self._processors

    def __setitem__ (self,name,processor):
        check_name(name)
        if isinstance(processor, basestring):
            processor = load_processor(processor)
        self._processors[name] = processor(self.environment)

    def get(self, processor):
        if isinstance(processor, (Processor, ProcessorCollection)):
            return processor
        elif isinstance(processor, basestring):
            # print processor
            func = eval(processor,{},self)
            # print processor, func
            if isinstance(func, Processor): return func()
            else: return func
        elif isinstance(processor,(tuple,list)):
            return self.get_multiple(processor)
        elif type(processor)==ClassType or type(processor)==type:
            return processor()
        raise ProcessorError("%s must be a instance of Processor"%processor.__name__)

    def setup(self):
        for name, processor in self._processors.iteritems():
            try:
                processor.setup()
            except Exception, e:
                self._processors_errors[name] = e

    def get_multiple(self, processors):
        return ProcessorCollection(*[self.get(processor) for processor in processors])

class Processor(object):
    def __init__(self,environment=None):
        self.environment = environment

    @property
    def config(self):
        return self.environment.config

    def setup(self):
        pass

    def __call__(self,*args,**kwargs):
        # print args, kwargs
        def process(asset):
            return self.process(asset, *args, **kwargs)
        return process

    # @memoized
    def process (self, asset,*args,**kwargs):
        enabled = kwargs.pop('_enabled',True)
        if not enabled: return asset
        # asset = copy(asset)
        # try:
        if asset.single:
            return self.process_single(asset,*args,**kwargs)
        else:
            return self.process_collection(asset,*args,**kwargs)
        # except TypeError:
        #     raise Exception("The arguments of the process function in %s processor doesn't match"%self.__class__.__name__)

    def process_collection (self,assets,*args,**kwargs):
        """Return all the child resources or False, if there is no change"""
        new_assets = AssetCollection(environment=assets.environment,storage=assets.storage)
        for asset in assets:
            new_assets.add(self.process(asset,*args,**kwargs))
        return new_assets

    def process_single(self,asset,*args,**kwargs):
        """Process each resource in the bundle"""
        return asset


class ExternalProcessor(Processor):
    class tempfile_on_demand(object):
        def __repr__(self):
            if not hasattr(self, 'filename'):
                self.fd, self.filename = tempfile.mkstemp()
            return self.filename
        
        @property
        def created(self):
            return hasattr(self, 'filename')

    @classmethod
    def subprocess(cls, argv, data=None):

        # Replace input and output placeholders
        input_file = cls.tempfile_on_demand()
        output_file = cls.tempfile_on_demand()
        if hasattr(str, 'format'):   # Support Python 2.5 without the feature
            argv = map(lambda item:
                item.format(input=input_file, output=output_file), argv)

        out = None
        try:
            if input_file.created:
                if not data:
                    raise ValueError(
                        '{input} placeholder given, but no data passed')
                with os.fdopen(input_file.fd, 'wb') as f:
                    f.write(data.read() if hasattr(data, 'read') else data)
                    # No longer pass to stdin
                    data = None

            # print argv
            proc = subprocess.Popen(
                argv,
                # we cannot use the in/out streams directly, as they might be
                # StringIO objects (which are not supported by subprocess)
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(
                data.read() if hasattr(data, 'read') else data)
            if proc.returncode:
                raise BuildError(
                    '%s: subprocess returned a non-success result code: '
                    '%s, stdout=%s, stderr=%s' % (
                        cls.__name__, proc.returncode, stdout, stderr))
            else:
                if output_file.created:
                    with os.fdopen(output_file.fd, 'rb') as f:
                        out = f.read()
                else:
                    out = stdout
        finally:
            pass
            # if output_file.created:
            #     os.unlink(output_file.filename)
            # if input_file.created:
            #     os.unlink(input_file.filename)

        return out

class CallableProcessor(Processor):
    """Helper class that create a simple processor wrapping around
    callable.
    """

    def __init__(self, _callable):
        super(CallableProcessor, self).__init__()
        self.callable = _callable

    def process(self, asset):
        return self.callable(asset)
        
from assetsy.processors.utils import *
from assetsy.processors.css import *
from assetsy.processors.js import *
from assetsy.processors.images import *
