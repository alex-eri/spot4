from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os","utils","struct"],
    "excludes": ["tkinter","tornado","zope","twisted","xmlrpc","xml"],
    'include_files': ['config.json','dictionary'],
    'create_shared_zip': True, #не запускается если отключить library.zip
    'append_script_to_exe':True,
    #'include_in_shared_zip': True
}

import os
if os.name == 'posix':
    build_exe_options['include_files'].extend(

        ['/usr/lib/libssl.so.1.0.0','/usr/lib/libcrypto.so.1.0.0','spot4.service']
    )

base = None
base_service = base

#if os.name == 'nt':
#    base_service = 'Win32Service'

executables = [Executable(
    "main.py",
    base=base_service,
    targetName='spot4.exe'
    ),
    Executable(
    "migrate.py",
    base=base,
    targetName='migrate.exe'
    ),
    ]


setup(  name = "spot4",
        version = "0.1",
        description = "Spot 4",
        options = {"build_exe": build_exe_options},
        executables = executables,
        data_files = ['config.json','dictionary']
        )
