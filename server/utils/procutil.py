import os
if os.name == "posix":
    import ctypes
    from ctypes.util import find_library
    libc = ctypes.CDLL(find_library('c'))

    PR_SET_NAME = 15
    PR_GET_NAME = 16

    def set_proc_name(name):
        name = name.encode('ascii')
        libc.prctl(PR_SET_NAME, ctypes.c_char_p(name), 0, 0, 0)

    def get_proc_name():
        name = ctypes.create_string_buffer(16)
        libc.prctl(PR_GET_NAME, name, 0, 0, 0)
        return name.value
else:
    def set_proc_name(name): return
    def get_proc_name(): return "spot_process"

def chdir(f):
    try:
        os.chdir(os.path.abspath(f))
    except FileNotFoundError as e:
        raise e
        exit(1)
