import sys

import bpy

_REGISTERED_THINGS = dict()


def requires(*things):
    def decorator(thing):
        _process_and_set_requires(thing, things)
        return thing
    return decorator


def module_requires(name, things):
    module = sys.modules[name]
    _process_and_set_requires(module, things)


def module_thing(thing):
    module_requires(thing.__dict__['__module__'], [thing])
    return thing


def _default_user():
    pass
    # import inspect
    # curframe = inspect.currentframe()
    # calframe = inspect.getouterframes(curframe, 10)[9]
    # return '%s(%s:%d)' % (calframe.function, calframe.filename, calframe.lineno)


def register_thing(thing, user=_default_user()):
    users = _REGISTERED_THINGS.get(thing)
    if users is None:
        _REGISTERED_THINGS[thing] = users = list()
        required = getattr(thing, '__required_things', [])
        for req in required:
            register_thing(req, thing)
        try:
            bpy.utils.register_class(thing)
        except ValueError as err:
            call = getattr(thing, 'register', None)
            if callable(call):
                call()
            elif required == []:
                raise Exception('Unsupported thing %s' % thing, err, user)
            
    users.append(user)


def unregister_thing(thing, user=_default_user()):
    users = _REGISTERED_THINGS.get(thing)
    if users is None:
        raise Exception('Thing %s is not registered' % thing)
    try:
        users.remove(user)
    except ValueError as ex:
        if user not in users:
            raise Exception('Thing %s is not registered for user %s' % (thing, user))
        raise ex
    if users == []:
        required = getattr(thing, '__required_things', [])
        for req in reversed(required):
            unregister_thing(req, thing)
        try:
            bpy.utils.unregister_class(thing)
        except ValueError:
            call = getattr(thing, 'unregister', None)
            if callable(call):
                call()
            elif required == []:
                raise Exception('Unsupported thing %s' % thing)
        del _REGISTERED_THINGS[thing]


def dump():
    for thing, required_by in _REGISTERED_THINGS.items():
        print(thing, required_by)


def _process_and_set_requires(thing, things):
    values = [getattr(thing, c) if isinstance(c, str) else c for c in things]

    required = getattr(thing, '__required_things', None)
    if required is None:
        required = []
        setattr(thing, '__required_things', required)
    required.extend(values)
