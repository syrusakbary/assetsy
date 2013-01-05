def check_name (name):
	if not name.replace('_','').isalnum():
		raise Exception('The name "%s" is not valid.'%name)
