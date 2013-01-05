import glob2 as glob
#import glob

import os
#from django.core.files.storage import default_storage

from assetsy.exceptions import ResourceNotFoundError
from assetsy.utils.managers import check_name
from abc import ABCMeta, abstractmethod, abstractproperty
from copy import copy


class BaseAsset:
    __metaclass__ = ABCMeta
    
    def __init__(self, processors=[],environment=None,storage=None):
        self.environment = environment
        self.processors = processors
        self.storage = storage

    @property
    def processors(self):
        return self._processors

    @processors.setter
    def processors(self,value):
        self._processors = self.environment.processor_manager.get(value)

    def process(self):
        # print 'PROCESSING, %r'%self
        processor = copy(self.processors)
        processor = self.processors
        return processor.process(self)


class AssetSingle(BaseAsset):
    #@abstractmethod
    #def last_modified(self): pass
    single = True
    _content = None
    _last_modified = None

    def __init__(self,*args,**kwargs):
        super(AssetSingle,self).__init__(*args,**kwargs)
        self.output = {}

    def load(self): pass

    #NO deberia estar aqui
    @property
    def url(self):
        return self.environment.url(self)
    
    @property
    def last_modified(self):
        return self._last_modified

    @last_modified.setter
    def last_modified(self,value):
        self._last_modified = value

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self,value):
        self._content = value

    def __hash__(self):
        return hash((self._content,
                     self.last_modified,
                     self.environment))

    def dump (self):
        return self.process()

    def __repr__ (self):
        return "<%s processors=%s environment=%s>"%(self.__class__.__name__,self.processors,self.environment)

class AssetManager:
    _assets = {}
    def __getitem__ (self,name):
        if not name in self:
            raise Exception('There is no "%s" asset.'%name)
        return self.assets[name]
    def __contains__ (self,name):
        return name in self._assets
    def __setitem__ (self,name,asset):
        check_name(name)
        if not isinstance(asset,BaseAsset):
            raise Exception('The asset "%s" must be an instance of BaseAsset'%asset)
        self._assets[name] = asset

class StringAsset(AssetSingle):
    def __init__(self,content,**kwargs):
        BaseAsset.__init__(self,**kwargs)
        self._content_string = content
    def load(self):
        self._content = self._content_string

class FileAsset(AssetSingle):
    def __init__(self,source,from_file=None,processors=[],environment=None,**kwargs):
        processors = list(environment.before_processors(source)) + processors
        super(FileAsset,self).__init__(processors=processors,environment=environment,**kwargs)
        if from_file:
            self.path = self.environment.relpath(from_file,source)
        else:
            self.path = source
        extra = ''
        self._filename = self._exists(source,from_file)
        # except ResourceNotFoundError:
        #     m = re.match(self.FILE_RE,source)
        #     if m:
        #         source = m.group(1)
        #         extra = m.group(2)
        #         self._filename = self._exists(source,from_file)
    
        self._extra = extra
        self.source = source

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self,value):
        self._source = value
        head,filename,name,ext = self.split_source()
        self.output.update(dict(path=head+'/',filename=filename,name=name,ext=ext))

    @property
    def base_dir(self):
        return os.path.dirname(self.environment.abspath(self.source))

    def split_source(self):
        head,filename = os.path.split(self.source)
        name,ext = os.path.splitext(filename)
        return head,filename,name,ext
    
    def _exists (self,source,from_file=None):
        if from_file: source = self.environment.relpath(from_file,source)
        filename = self.environment.abspath(source)
        if not os.path.isfile(filename):
            raise ResourceNotFoundError('The resource "%s" do not exists' % filename)
        return filename

    @property
    def last_modified(self):
        return os.path.getmtime(self._filename)
    
    def load(self):
        self._content = open(self._filename).read()
    
    def __repr__ (self):
        return '<FileAsset "%s">'%(self._source+self._extra)
    
    def __hash__(self):
        return hash((self._source,
                     self._extra,
                     self.last_modified,
                     self.environment))

class AssetCollection (BaseAsset):
    single = False
    def __init__(self,*args, **kwargs):
        super(AssetCollection,self).__init__(**kwargs)
        self._assets = []
        for asset in args:
            self.add(asset)
    def __iter__(self):
        return self._assets.__iter__()

    @property
    def flatten(self):
        p = []
        for a in self._assets:
            if isinstance(a, AssetCollection): p += a.flatten
            else: p.append(a)
        return p

    def add (self,asset):
        if not isinstance(asset,BaseAsset):
            raise Exception('The asset "%s" must be an instance of BaseAsset'%asset)
        self._assets.append(asset)

    def __getitem__(self,item):
        return self._assets.__getitem__(item)

    def load(self):
        for asset in self._assets:
            asset.load()

    def dump(self):
        assets = AssetCollection(environment=self.environment,storage=self.storage)
        # assets.processors = self.processors
        for asset in self._assets:
            assets.add(asset.dump())
        return assets.process()

    def __hash__(self):
        return hash((tuple(self._assets),
                     self.environment))
    
    # def apply_processors (self,env):
    #     self.flatten()
    #     self.processors.apply(self,env=env)
    #     #for f in self.processors:
    #     #   f.apply(self,env=env)

    # def process (self,env):
    #     self.resolve(env=env)
    #     for resource in self:
    #         resource.process(env=env)
    #     self.apply_processors(env=env)

    # def flatten (self):
    #     plain = []
    #     for resource in self:
    #         if isinstance(resource,Resource):
    #             plain += resource.all()
    #         else:
    #             plain.append(resource)
    #     self.clear()
    #     self.add(plain)
    # def add(self,resources):
    #     if isinstance(resources, list):
    #         self._resources += resources
    #     else:
    #         self._resources.append(resources)
    # def clear (self):
    #     self._resources = []
    #     self.contents = []

    # def resolve (self,env):
    #     if len(self._resources)>0: return
    #     #print self.contents
    #     for resource in self.contents:
    #         if isinstance(resource, basestring):
    #             self.add(env.resolve(resource))
    #         else:
    #             self.add(resource)

    def all (self):
        self.load()
        return self._assets

    def __repr__ (self):
        return "<AssetCollection assets=%s processors=%s environment=%s>"%(self._assets,self.processors,self.environment)

class AssetCache (BaseAsset):
    def __init__(self,asset,**kwargs):
        super(AssetCache,self).__init__(self,**kwargs)
        self.asset = asset
        self._load_hash = None
        self._dump_hash = None
    def load(self):
        asset_hash = hash(self.asset)
        if self._load_hash != asset_hash:
            self.asset.load()
            self._load_hash = asset_hash
    def dump(self):
        asset_hash = hash(self.asset)
        if self._dump_hash != asset_hash:
            self.dumped_assed = self.asset.dump()
            self._dump_hash = asset_hash
        return self.dumped_assed

class GlobAsset (AssetCollection):
    def __init__(self,path, **kwargs):
        super(GlobAsset,self).__init__(**kwargs)
        self._path = path
        self._initialized = False
    def load(self):
        self._assets = []
        gl_path =  glob.glob(self.environment.abspath(self._path))
        for _file in gl_path:
            self.add(FileAsset(_file[len(self.environment.abspath('./'))+1:], environment=self.environment, storage=self.storage))
        return super(GlobAsset,self).load()

from assetsy.processors import ProcessorCollection