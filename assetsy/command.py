from assetsy.env import Environment
from optparse import OptionParser
import time

import logging

def add_coloring_to_emit_ansi(fn):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if(levelno>=50):
            color = '\x1b[31m' # red
        elif(levelno>=40):
            color = '\x1b[31m' # red
        elif(levelno>=30):
            color = '\x1b[33m' # yellow
        elif(levelno>=20):
            color = '\x1b[32m' # green 
        elif(levelno>=10):
            color = '\x1b[35m' # pink
        else:
            color = '\x1b[0m' # normal
        args[1].msg = color + args[1].msg +  '\x1b[0m'  # normal
        #print "after"
        return fn(*args)
    return new

class CommandEnvironment(Environment):
    def on_build(self):
        self.compile(self.build_path)

    def build(self,*args,**kwargs):
        super(CommandEnvironment,self).build(*args,**kwargs)
        self.on_build()

def command():
    FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    logging.StreamHandler.emit = add_coloring_to_emit_ansi(logging.StreamHandler.emit)

    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-c", "--config", dest="config",
                    help="Config file", metavar="FILE")
    parser.add_option("-w", "--watch", dest="watch", default=False, action="store_true",
                    help="Watch paths and build automatically")
    parser.add_option("-s", "--serve", dest="serve", default=False,
                    help="Serve the build files in a basic HTTP server")

    options, args = parser.parse_args()
    e = CommandEnvironment()
    processors =  {
        'cssmin':'assetsy.processors.CSSMin',
        'cssprefixer':'assetsy.processors.CSSPrefixer',
        'concat':'assetsy.processors.Concat',
        'cssautoreg':'assetsy.processors.AutoregisterURL',
        'jsmin':'assetsy.processors.JsMin',
        'jsjinja':'assetsy.processors.JsJinja',
        'coffee':'assetsy.processors.CoffeeScript',
        'optipng':'assetsy.processors.OptiPNG',
        'pngcrush':'assetsy.processors.PNGCrush',
        'stylus':'assetsy.processors.Stylus',
    }
    for name, processor in processors.iteritems():
        e.processor_manager[name] = processor
    e.from_yaml('assets.yml')
    e.build()
    if options.watch:
        try:
            while True:
                time.sleep(.5)
        except KeyboardInterrupt:
            pass
    else:
        e.compile(e.build_path)
