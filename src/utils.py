import re


_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')

def camel2snake(s):
    subbed = _underscorer1.sub(r'\1_\2', s)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def snake2camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def convert(obj, convert_func):
    if not isinstance(obj, dict):
        return obj
    new = {}
    for k, v in obj.items():
        new_v = v
        if isinstance(v, dict):
            new_v = convert(v, convert_func)
        elif isinstance(v, list):
            new_v = [convert(x, convert_func) for x in v]
        new[convert_func(k)] = new_v
    return new
