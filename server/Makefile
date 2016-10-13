all: clean build_exe copy

clean:
	rm -rf build/*

build_exe:
	python setup.py build
 
copy:
	[ -x ./build/lib* ] && cp -r ./build/$(shell (ls build | grep lib))/* ./build/$(shell (ls build | grep exe))/
