from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os","utils"],
    "excludes": ["tkinter","tornado","zope","twisted","xmlrpc","xml"],
    'include_files': ['/usr/lib/libssl.so.1.0.0','/usr/lib/libcrypto.so.1.0.0','config.json','dictionary']
}

base = None
setup(  name = "spot4",
        version = "0.1",
        description = "Spot 4",
        options = {"build_exe": build_exe_options},
        executables = [Executable("main.py", base=base,targetName='spot4.exe')],
        data_files = ['config.json','dictionary']
        )
