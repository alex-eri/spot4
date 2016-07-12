from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os"],
    "excludes": ["tkinter","tornado"]
}

base = None
setup(  name = "spot4",
        version = "0.1",
        description = "Spot 4",
        options = {"build_exe": build_exe_options},
        executables = [Executable("main.py", base=base)])
