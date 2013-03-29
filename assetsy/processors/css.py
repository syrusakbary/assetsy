from assetsy.processors import Processor, ExternalProcessor
from assetsy.exceptions import ResourceNotFoundError, BuildError
import os, subprocess
# import inspect
# import shlex
import tempfile
import re


class CSSMin(Processor):
    def setup(self):
        try:
            import cssmin
        except ImportError:
            raise EnvironmentError('The "cssmin" package is not installed.')
        else:
            self.cssmin = cssmin

    def process_single(self, asset):
        asset.content = self.cssmin.cssmin(asset.content)
        return asset

class CSSPrefixer(Processor):
    def setup(self):
        try:
            import cssprefixer
        except ImportError:
            raise EnvironmentError('The "cssprefixer" package is not installed.')
        else:
            self.cssprefixer = cssprefixer

    def process_single(self, asset):
        asset.content = self.cssprefixer.process(asset.content, False, False)
        return asset


class Stylus(ExternalProcessor):
    def process_single(self, asset, plugins=None):
        argv = ['stylus']
        if plugins:
            argv.append('-u')
            argv.append(', '.join(plugins))

        argv.append('-I')
        argv.append(asset.base_dir)
        # print asset.base_dir
        argv.append('--include-css')
        asset.content = self.subprocess(argv, asset.content)
        return asset


class AutoregisterURL(Processor):
    FILE_RE = re.compile(r'^([^\?|#]*)(.*)$')
    @classmethod
    def _rewrite(cls,m,asset):
        # Get the regex matches; note how we maintain the exact
        # whitespace around the actual url; we'll indeed only
        # replace the url itself.
        replace = False
        text_before = m.groups()[0]
        url = m.groups()[1]
        text_after = m.groups()[2]

        # normalize the url we got
        quotes_used = ''
        if url[:1] in '"\'':
            quotes_used = url[:1]
            url = url[1:]
        if url[-1:] in '"\'':
            url = url[:-1]

        # Replace mode: manually adjust the location of files
        m = re.match(cls.FILE_RE,url)
        extra = ''
        if m:
            url = m.group(1)
            extra = m.group(2)
        env = asset.environment
        
        from assetsy.assets import FileAsset
        # try:
        # raise Exception(asset_path)
        new_asset = env.single_asset(url,from_file=asset.source)
        new_asset.output = new_asset.path
        # except ResourceNotFoundError,e:
        #     return
        
        # env.register(new_asset)
        #env.register(resource)
        #print resource_path
        #print '%s-%s-%s'%(url,resource.output,resource_path)
        
        if replace is not False:
            for to_replace, sub in replace.items():
                #targeturl = urlparse.urljoin(source_url, url)
                targeturl = url
                if targeturl.startswith(to_replace):
                    url = "%s%s" % (sub, targeturl[len(to_replace):])
                    # Only apply the first match
                    break

        # Default mode: auto correct relative urls
        #else:
            # If path is an absolute one, keep it
            #if not url.startswith('/') and not (url.startswith('http://') or url.startswith('https://')):
                # rewritten url: relative path from new location (output)
                # to location of referenced file (source + current url)
                #url = urlpath.relpath(output_url,
                #                      urlparse.urljoin(source_url, url))
        new_url = url
        try:
            new_url = new_asset.url+extra
        except:
            raise BuildError(asset_path)
        result = 'url(%s%s%s%s%s)' % (
                    text_before, quotes_used, new_url, quotes_used, text_after)
        return result
    def setup(self):
    	import re
        self.urltag_re = re.compile(r"""
        url\(
          (\s*)                 # allow whitespace wrapping (and capture)
          (                     # capture actual url
            [^\)\\\r\n]*?           # don't allow newlines, closing paran, escape chars (1)
            (?:\\.                  # process all escapes here instead
                [^\)\\\r\n]*?           # proceed, with previous restrictions (1)
            )*                     # repeat until end
          )
          (\s*)                 # whitespace again (and capture)
        \)

        # (1) non-greedy to let the last whitespace group capture something
              # TODO: would it be faster to handle whitespace within _rewrite()?
        """, re.VERBOSE)

    def process_single(self, asset):
        asset.content = self.urltag_re.sub(lambda x: self._rewrite(x,asset), asset.content)
        return asset