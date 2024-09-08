import os
import sys

def attach_if_needed(argv):
    connect, token = None, None
    for i, v in enumerate(argv):
        if v.endswith('/debugpy'):
            sys.path.append(v + '/..')
        elif v == '--connect':
            connect = argv[i + 1]
        elif v == '--adapter-access-token':
            token = argv[i + 1]
    if not connect:
        return False

    import debugpy
    sp = connect.split(':')
    address = (sp[0], int(sp[1])) if len(sp) == 2 else ('127.0.0.1', int(connect))
    print('Debugger is connecting to', address, '...')
    debugpy.connect(address, access_token=token)
    print('Debugger is connected')
    return True

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    import io_scene_xray
    attach_if_needed(sys.argv)
    try:
        io_scene_xray.unregister()
    except ValueError as err:
        print('Oops, monkey see no evil in:', err)
    io_scene_xray.register()
