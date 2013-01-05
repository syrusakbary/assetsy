from assetsy.env import Environment
from os import path
import mimetypes
# FlaskEnvironment(Environment):
#     def url(self,asset):
from werkzeug.exceptions import NotFound
from zlib import adler32
import os
from time import time


class FlaskEnvironment(Environment):
    def init_app(self, app, base=None):
        self.app = app
        if not base:
            base = get_static_folder(app)
            base = os.path.normpath(base)
        self.base = base
    def url(self,asset):
        return self.app.config.get('ASSETSY_URL',lambda x:'/_assetsy/%s'%x)(asset.path)

class Assetsy():
    cache_timeout = 60 * 60 * 12
    add_etags=True
    def __init__(self, app=None):
        self.app = app
        self.reload_handler = None
        self.env = FlaskEnvironment()
        # if app:
        if app:
            self.init_app(app)

    def _init_processors (self):
        assetsy_processors = self.app.config.get('ASSETSY_PROCESSORS',{})
        for name,processor in assetsy_processors.iteritems():
            self.env.processor_manager[name] = processor

    def serve(self,filename):
        outputs = self.env.outputs or self.env.build()
        try:
            asset = outputs[filename]
            mimetype = mimetypes.guess_type(filename)[0]
            mtime = asset.last_modified
            rv = self.app.response_class(asset.content, mimetype=mimetype,
                                    direct_passthrough=True)
            if mtime is not None:
                rv.last_modified = int(mtime)

            rv.cache_control.public = True
            if self.cache_timeout:
                rv.cache_control.max_age = self.cache_timeout
                rv.expires = int(time() + self.cache_timeout)

            if self.add_etags and filename is not None:
                rv.set_etag('assetsy-%d-%s-%s' % (
                    mtime,
                    len(asset.content),
                    adler32(
                        filename.encode('utf8') if isinstance(filename, unicode)
                        else filename
                    ) & 0xffffffff
                ))

            return rv
        except KeyError:
            raise NotFound()


    def init_app(self, app):
        self.env.init_app(app)
        self._init_processors()
        app.jinja_env.add_extension('assetsy.ext.jinja2.AssetsyExtension')
        app.jinja_env.assetsy_env = self.env
        self.instant_reload = app.config.get('ASSETSY_INSTANT',True)
        if app.debug: app.add_url_rule('/_assetsy/<path:filename>', 'assetsy', self.serve)

    def add(self,*args,**kwargs):
        name = kwargs.pop('name',None)
        asset = self.env.asset(*args,**kwargs)
        return asset

def get_static_folder(app_or_blueprint):
    """Return the static folder of the given Flask app
    instance, or module/blueprint.

    In newer Flask versions this can be customized, in older
    ones (<=0.6) the folder is fixed.
    """
    if hasattr(app_or_blueprint, 'static_folder'):
        return app_or_blueprint.static_folder
    return path.join(app_or_blueprint.root_path, 'static')

try:
    from flaskext import script
except ImportError:
    pass
else:
    class ManageAssetsy(script.Command):
        # option_list = (
        #     script.Option('--force', '-f', dest='force',default=False,type=bool),
        # )

        def __init__(self, app, dir='assetsy',env=None):
            self.app = app
            self.env = env or self.app.jinja_env.assetsy_env
            self.dir = dir if os.path.isabs(dir)\
                else os.path.join(self.app.root_path,dir)
        def run(self,force=False):
            # print force
            self.env.compile(self.dir,bool(force))
