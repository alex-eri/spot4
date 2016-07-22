from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os","utils"],
    "excludes": ["tkinter","tornado","zope","twisted","xmlrpc","xml"],
    'include_files': ['/usr/lib/libssl.so.1.0.0','/usr/lib/libcrypto.so.1.0.0','config.json','dictionary'],
    'create_shared_zip': True, #не запускается если отключить library.zip
    'append_script_to_exe':True,
    #'include_in_shared_zip': True
}

base = None

executables = [Executable(
    "main.py",
    base=base,
    targetName='spot4.exe'
    )]


setup(  name = "spot4",
        version = "0.1",
        description = "Spot 4",
        options = {"build_exe": build_exe_options},
        executables = executables,
        data_files = ['config.json','dictionary']
        )
