from __future__ import absolute_import

import warnings
import jinja2
from jinja2.ext import Extension
from jinja2 import nodes
# from assetsy.django import asset
# from assetsy.django.env import get_env

__all__ = ('AssetsyExtension',)


class AssetsyExtension(Extension):
    """
    As opposed to the Django tag, this tag is slightly more capable due
    to the expressive powers inherited from Jinja. For example:

        {% assets "src1.js", "src2.js", get_src3(),
                  filter=("jsmin", "gzip"), output=get_output() %}
        {% endassets %}
    """

    tags = set(['assets'])

    def _make_compat(self):
        try:
            self.environment.jade_env.code_tags += ('assets',)
            self.environment.jade_env.auto_close_tags['assets'] = 'endassets'
        except:
            pass
    def __init__(self, environment):
        super(AssetsyExtension, self).__init__(environment)
        # from assetsy.django.env import get_env
        # add the defaults to the environment
        environment.extend(
            assetsy_env=None, #get_env()
        )
        self._make_compat()

    def parse(self, parser):
        lineno = parser.stream.next().lineno

        resources = []
        using = nodes.Const(None)
        processors = nodes.Const(None)

        # parse the arguments
        first = True
        while parser.stream.current.type is not 'block_end':
            if not first:
                parser.stream.expect('comma')
            first = False

            # lookahead to see if this is an assignment (an option)
            if parser.stream.current.test('name') and parser.stream.look().test('assign'):
                name = parser.stream.next().value
                parser.stream.skip()
                value = parser.parse_expression()
                print name
                if name == 'processors':
                    processors = value
                #elif name == 'using':
                #    using = value
                else:
                    parser.fail('Invalid keyword argument: %s' % name)
            # otherwise assume a source file is given, which may
            # be any expression, except note that strings are handled
            # separately above
            else:
                resources.append(parser.parse_expression())

        # parse the contents of this tag, and return a block
        body = parser.parse_statements(['name:endassets'], drop_needle=True)
        return nodes.CallBlock(
                self.call_method('_render_assets',
                                 args=[processors, using, nodes.List(resources)]),
                [nodes.Name('ASSET', 'store')], [], body).\
                    set_lineno(lineno)

    @classmethod
    def resolve_contents(self, contents, env):
        """Resolve bundle names."""
        result = []
        for f in contents:
            try:
                result.append(env[f])
            except KeyError:
                result.append(f)
        return result

    def _render_assets(self, processors, using, resources, caller=None):
        env = self.environment.assetsy_env
        if env is None:
            raise RuntimeError('No assets environment configured in '+
                               'Jinja2 environment')
        if processors is None:
            processors = []
        result = u""
        #print resources, self.resolve_contents(resources, env)
        resources = env.asset(*resources,
                                **{
                                   'processors': processors})
        r = resources.dump()
        #resources.process(env=env)
        if r.is_single():
            return caller(r)
        else:
            for f in r:
                result += caller(f)
            return result