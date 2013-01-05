import os, subprocess
from assetsy.processors import Processor
from assetsy.assets import StringAsset

class JsMin(Processor):
    def setup(self):
        try:
            import jsmin
        except ImportError:
            raise EnvironmentError('The "jsmin" package is not installed.')
        else:
            self.jsmin = jsmin

    def process_single(self, asset):
        asset.content = self.jsmin.jsmin(asset.content)
        return asset

class CoffeeScript(Processor):
    def process_single(self, asset, no_bare=False):
        binary = 'coffee'
        args = "-sp" + ("" if no_bare else 'b')
        proc = subprocess.Popen([binary, args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(asset.content)
        if proc.returncode != 0:
            raise Exception(('coffeescript: subprocess had error: stderr=%s, '+
                               'stdout=%s, returncode=%s') % (
                stderr, stdout, proc.returncode))
        elif stderr:
            print "coffeescript filter has warnings:", stderr
        asset.content = stdout
        return asset

class JsJinja(Processor):
    def setup(self):
        try:
            from jsjinja import JsJinja
        except ImportError:
            raise EnvironmentError('The "jsjinja" package is not installed.')
        else:
            env = self.config['jsjinja']['env']
            self.jsjinja = JsJinja(env)

    def process (self, asset, lib=False, minified=True):
        processed = super(JsJinja, self).process(asset)
        if lib:
            lib_content = self.jsjinja.lib(minified)
            if asset.single:
                processed.content = lib_content + processed.content
            else:
                processed._assets = [StringAsset(lib_content)] + processed._assets
        return processed

    def process_single(self, asset):
        # print  '***********', asset, asset.content, '***********'
        asset.content = self.jsjinja.generate_source(asset.content)
        return asset
