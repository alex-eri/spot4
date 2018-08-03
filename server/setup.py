# -*- coding: utf-8 -*-
USE_CYTHON = False

from cx_Freeze import Executable
from cx_Freeze import setup as cx_setup

import sys
sys.path.insert(1,'lib/python3.6')
sys.path.insert(1,'lib/python36.zip')


packages = ["os","utils","struct","mschap","pytz","motor","aiohttp","asyncio","sms", "idna", "encodings","logging.handlers", 'utils.ServiceHandler','codecs'] #,"pandas"]
excludes = ["tkinter","tornado","zope","twisted","xmlrpc","IPython","setuptools","sqlalchemy","curses","Xmultidict._multidict"]

build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "includes": packages,
    'include_files': [],
    'zip_include_packages': "*",
    'zip_exclude_packages': None,
    'include_msvcr': True,
    'constants':{}
}




def find_libs():
    LIBS = [
            'ssl',
            'crypto',
            'xslt',
            'xml2',
            'lzma',
            'z',
            'exslt'
        ]
    from ctypes.util import find_library
    files =  [ find_library(x) for x in LIBS ]

    prefix = [
        "/usr/lib/x86_64-linux-gnu/", #deb
        "/lib/x86_64-linux-gnu/",
        "/usr/lib/", #arch
        "."
        ]

    for p in prefix:
        for f in files:
            if f:
                a = os.path.join(p,f)
            print(f)
            if os.path.isfile(a):
                yield a



import os
if os.name == 'posix':
    excludes.append('cx_Logging')
    build_exe_options['include_files'].extend(

        [ x for x in find_libs() ]
    )

print(build_exe_options['include_files'])

base = None
base_service = base
initScript="ConsoleSetLibPath"

if os.name == 'nt':
    packages.append('cx_Logging')
    p_path = os.path.dirname(sys.executable)


    build_exe_options['packages'].extend(['win32serviceutil'])
    build_exe_options['include_files'].extend(
        [
            #os.path.join(p_path,'libeay32.dll'),
            #os.path.join(p_path,'ssleay32.dll')
            "windows.dll/libcrypto-1_1-x64.dll",
            "windows.dll/libssl-1_1-x64.dll",
            ("windows.dll/libcrypto-1_1-x64.dll","libeay32.dll")
        ]
    )
    initScript="Console"
    #base_service = 'Win32Service'

#initScript="Console"

executables = [Executable(
    script="server.py",
    initScript=initScript,
    base=base_service,
    targetName='spot4.exe',
    copyright='Aleksandr Stepanov, eerie.su'
    ),
    Executable(
    "migrate.py",
    initScript=initScript,
    base=base,
    targetName='migrate.exe'
    )
    ]


if os.name == 'nt':
    executables.append(
        Executable('winservice.py', base='Win32Service',
               targetName='Spot4Service.exe')
    )

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
        data_files = []
        )
