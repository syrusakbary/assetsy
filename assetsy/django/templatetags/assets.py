from djinja import template

register = template.Library()
#from mediagenerator import utils
from jinja2 import environmentfunction
from assetsy.django.env import get_env

# env = get_env()
@environmentfunction
def asset_url(environment,path):
	env = environment.assetsy_env
	return env[path].url

@environmentfunction
def asset_content(environment,path):
	env = environment.assetsy_env
	return env[path].content

@environmentfunction
def asset(environment,path):
	env = environment.assetsy_env
	return env[path]

register.tag(asset_url)
register.tag(asset_content)
register.tag(asset)