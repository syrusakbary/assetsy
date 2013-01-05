from assetsy.processors import Processor
import os
from tempfile import NamedTemporaryFile
import subprocess
import StringIO

class OptiPNG(Processor):

    def process_single(self, asset,optimize=5):
        f = NamedTemporaryFile(delete=False)
        f.write(asset.content)
        # print asset.source
        f.close()
        os.spawnlp(os.P_WAIT, 'optipng','optipng','-o%d'%optimize, f.name)
        f = open(f.name,'r')
        # f.file.seek(0)
        asset.content = f.read()
        f.close()
        os.unlink(f.name)
        return asset

# def popen_results(args):
#     proc = subprocess.Popen(args, stdout=subprocess.PIPE)
#     return proc.communicate()[0]

class PNGCrush(Processor):

    def process_single(self, asset):
        f = NamedTemporaryFile(delete=False)
        print len(asset.content),asset.path
        f.write(asset.content)
        # print asset.source
        f.close()
        crushed_name = f.name+'.crushed'
        #print crushed_name
        os.spawnlp(os.P_WAIT, 'pngcrush','pngcrush','-reduce -rem alla -rem gAMA -rem cHRM -rem iCCP -rem sRGB', f.name,crushed_name)
        #args = '-rem alla -rem gAMA -rem cHRM -rem iCCP -rem sRGB'
        #args = '-reduce'
        #popen_results(['pngcrush', args, f.name, crushed_name])

        os.unlink(f.name)
        nf = open(crushed_name,'r')
        asset.content = nf.read()
        nf.close()
        # print 'new:', len(asset.content),asset.path
        os.unlink(crushed_name)
        return asset

class Convert(Processor):
    def setup(self):
        try:
            try:    
                from PIL import Image
            except:
                import Image
        except ImportError:
            raise EnvironmentError('The "PIL" package is not installed.')
        else:
            self.Image = Image
    def process_single(self, asset,to='JPEG',convert='RGB',quality='keep'):
        f = StringIO.StringIO(asset.content)
        img = self.Image.open(f)
        buf = StringIO.StringIO()
        img.convert(convert).save(buf, to, quality=90)
        asset.content = buf.getvalue()
        return asset

class Resize(Processor):
    def setup(self):
        try:
            try:    
                from PIL import Image
            except:
                import Image
        except ImportError:
            raise EnvironmentError('The "PIL" package is not installed.')
        else:
            self.Image = Image

    def process_single(self, asset, size):
        f= StringIO.StringIO(asset.content)
        img = self.Image.open(f)

        if isinstance(size,float):
            size = map(lambda x:int(x*size),img.size)

        img = img.resize(size, self.Image.ANTIALIAS)
        buf= StringIO.StringIO()
        img.save(buf, format= 'PNG')
        asset.content = buf.getvalue()
        return asset