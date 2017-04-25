USE_CYTHON = False

from cx_Freeze import Executable
from cx_Freeze import setup as cx_setup

packages = ["os","utils","struct","mschap","pytz","motor","aiohttp","asyncio","sms"] #,"pandas"]
excludes = ["tkinter","tornado","zope","twisted","xmlrpc","IPython","setuptools","sqlalchemy","curses","multidict._multidict"]

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

import os
if os.name == 'posix':
    build_exe_options['include_files'].extend(

        [
            '/usr/lib/libssl.so.1.0.0',
            '/usr/lib/libcrypto.so.1.0.0',
            '/usr/lib/libxslt.so.1',
            '/usr/lib/libxml2.so.2',
            '/usr/lib/liblzma.so.5',
            '/usr/lib/libz.so.1',
            '/usr/lib/libexslt.so.0'
        ]
    )


base = None
base_service = base
initScript="ConsoleSetLibPath"

if os.name == 'nt':
    build_exe_options['packages'].extend(['win32serviceutil'])
    build_exe_options['include_files'].extend(
        [
            'openssl.exe',
            'libeay32.dll',
            'ssleay32.dll'
        ]
    )
    initScript="Console"
    #base_service = 'Win32Service'

initScript="Console"

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
