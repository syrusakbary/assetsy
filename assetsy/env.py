from os import path, makedirs
from assetsy.assets import FileAsset, GlobAsset, AssetCollection
from glob import has_magic
from assetsy.processors import ProcessorManager
from assetsy.exceptions import BuildError
import types

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from time import time
import logging
import re

def to_list(items):
    if isinstance(items, types.StringTypes):
        return [items]
    return items

def reference (name):
    import re
    m = re.match(r'^@(\w+)$',name)
    is_reference = m!=None
    name = m.group(1) if m else None
    return is_reference, name

class Environment(object):
    def __init__ (self,base=None,instant_reload=True):
        self.instant_reload = instant_reload
        self.reload_handler = ReloadEventHandler(self)
        if base:
            self.base = base
        self.before = []
        self.paths = {}
        self._outputs = []
        self.outputs = {}
        self._references = {}
        self._anon_references = []
        self.processor_manager = ProcessorManager(self)

    def __getitem__(self, name):
        return self.single_asset(name)

    def abspath(self, filename):
        """Create an absolute path based on the directory.
        """
        if path.isabs(filename):
            return filename
        return path.abspath(path.join(self.base, filename))

    def relpath(self,filename1,filename2):
        return path.normpath(path.dirname(filename1)+'/'+filename2)
    
    # def outputs (self):
    #     return self._outputs

    # def resolve_processor (self,processor):
    #     if isinstance(processor, basestring):
    #         return self.processors.get(processor,load_processor(processor))
    #     else:
    #         return processor
    # def register_processor (self,name,processor):
    #     self.processors[name] = self.resolve_processor(processor)

    def compile(self,dir,force=False):
        # outputs = self.build()
        # self.process() #hack
        for outputfile,asset in self.outputs.iteritems():
            complete_path = path.join(dir,outputfile)
            pathname = path.dirname(complete_path)
            if not path.isdir(pathname):
                makedirs(pathname)
            if path.isfile(complete_path):
                mtime = path.getmtime(complete_path)
                if not force and mtime>=asset.last_modified: continue   
            f = open(complete_path,'w+')
            f.write(str(asset.content))
            f.close()

    def before_processors (self, filename):
        for regex, processor in self.before:
            if regex.match(filename): yield processor

    def single_asset (self,name,**kwargs):
        kwargs['environment'] = self
        try:
            is_reference, reference_name = reference(name)
        except:
            raise Exception(name)
        if is_reference:
            return self._references.get(reference_name)
        # elif self._outputs.has_key(name):
        #     return self._outputs[name]
        elif has_magic(name):
            return GlobAsset(name,**kwargs)
        else:
            return FileAsset(name,**kwargs)

    def asset (self, output=None, src=[], **kwargs):
        # print output, src, kwargs
        kwargs['environment'] = self
        name = kwargs.pop('name',None)
        if len(src)>1:
            pre = kwargs.pop('pre')
            asset = AssetCollection(**kwargs)
            kwargs.pop('processors')
            for _asset in src:
                if isinstance(_asset,basestring): _asset = self.asset(src=[_asset],pre=pre, **kwargs)
                asset.add(_asset)
        else:
            if not src and not name: 
                src = [output]
                output = '{path}{filename}'
            asset = self.single_asset(*src,**kwargs)

        if output:
            self.output(output,asset)
        if name:
            self._references[name] = asset
        return asset

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self,base):
        self._base = base
        self.add_path('default',base)

    def add_path(self,name, path):
        if name=='default': self._base = path
        self.paths[name] = path
        if self.instant_reload:
            observer = Observer()
            observer.schedule(self.reload_handler, path=path, recursive=True)
            observer.start()

    def settings(self, settings):
        self.config = {}
        self.paths = {}
        if 'base' in settings:
            self.base = settings['base']
        if 'build' in settings:
            self.build_path = settings['build']
        if 'config' in settings:
            self.config = settings['config']

        if 'paths' in settings:
            for name, path in settings['paths'].iteritems():
                self.add_path(name, path)

        self.before = []
        if 'before' in settings:
            for regex, processor in settings['before'].iteritems():
                # print regex, type(regex)
                formatted_re = re.compile(regex)
                self.before.append((formatted_re, processor))

        self.processor_manager.setup()

        assets = settings.get('assets',[])
        for asset in assets:
            output = asset.get('file',None)
            path = asset.get('path','default')
            name = asset.get('name',None)
            src = asset.get('src',[])
            processors = asset.get('processors',[])
            self.asset(output=output,src=to_list(src),name=name, processors=to_list(processors),pre=self.get_path(path))

    def from_yaml(self,filename):
        import yaml
        stream = open(filename, 'r')
        settings = yaml.load(stream)
        self.settings(settings)

    def get_path(self,path):
        if path not in self.paths:
            raise Exception("Path %s is not defined"%path)
        return self.paths[path]
    def output (self,path,asset):
        self._outputs.append((path,asset))

    def url(self,asset):
        return asset._source+asset._extra

    def asset_name(self,asset,name):
        return name.format(**asset.output), asset

    @property
    def iter_assets(self):
        for name, asset in self._outputs:
            try:
                asset.load()
                dumped = asset.dump()
                if isinstance(dumped,AssetCollection):
                    for _asset in dumped.flatten:
                        yield self.asset_name(_asset,name)
                else:
                    yield self.asset_name(dumped,name)
            except BuildError:
                logging.exception('Cannot build asset "%s" '%name)
    def build(self):
        init = time()
        self.outputs = dict(list(self.iter_assets))
        total = time()-init
        logging.info('Build complete in %.1f seconds', total)
        return self.outputs

    # def outputs(self):
    #     return dict(list(self.assets))


class ReloadEventHandler(FileSystemEventHandler):
  def __init__(self,env):
    self.env = env

  def reload (self):
    self.env.build()

  def on_moved(self, event):
    super(ReloadEventHandler, self).on_moved(event)
    self.reload()

  def on_created(self, event):
    super(ReloadEventHandler, self).on_created(event)
    if not event.is_directory:
        self.reload()

  def on_deleted(self, event):
    super(ReloadEventHandler, self).on_deleted(event)
    self.reload()

  def on_modified(self, event):
    super(ReloadEventHandler, self).on_modified(event)
    self.reload()

