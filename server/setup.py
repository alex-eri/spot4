USE_CYTHON = False

from cx_Freeze import Executable
from cx_Freeze import setup as cx_setup

packages = ["os","utils","struct","mschap","pytz","motor","aiohttp","asyncio","pandas"]
excludes = ["tkinter","tornado","zope","twisted","xmlrpc","IPython","setuptools","sqlalchemy","curses"]

build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "includes": packages,
    'include_files': [],
    'zip_include_packages': "*",
    'zip_exclude_packages': None,
    'include_msvcr': True
}

import os
if os.name == 'posix':
    build_exe_options['include_files'].extend(

        [
            '/usr/lib/libssl.so.1.0.0',
            '/usr/lib/libcrypto.so.1.0.0'
        ]
    )

base = None
base_service = base

#if os.name == 'nt':
#    base_service = 'Win32Service'

executables = [Executable(
    script="server.py",
    initScript="ConsoleSetLibPath",
    base=base_service,
    targetName='spot4.exe'
    ),
    Executable(
    "migrate.py",
    base=base,
    targetName='migrate.exe'
    ),
    Executable(
    "demo.py",
    base=base_service,
    targetName='spot4demo.exe'
    ),
    ]



if USE_CYTHON:
    from distutils.extension import Extension
    from distutils.core import setup
    from Cython.Build import cythonize

    build_exe_options['excludes'].extend([
        'literadius','radius','zte',"netflow"
    ]) #Убираем из ZIP и подсунем .SO

    #build_exe_options['includes'].append('literadius')


    files = [
        "main",
        "zte",
        "radius",
        "netflow",
        "literadius/__init__",
        "literadius/packet",
        "literadius/constants",
        "literadius/decoders",
        "literadius/protocol",
        ]


    extensions = []

    for f in files:
        extensions.append(
        Extension(f.replace(os.pathsep,'.'), [
            f+".py"],
            include_dirs=['.'],
            extra_compile_args = ["-O0", "-Wall"],
            extra_link_args = ['-g'],),
        )

    setup(
        ext_modules = cythonize(extensions)
    )


cx_setup(  name = "spot4",
        version = "0.1",
        description = "Spot 4",
        options = {"build_exe": build_exe_options},
        executables = executables,
        data_files = ['config.json']
        )
