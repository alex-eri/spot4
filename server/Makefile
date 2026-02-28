all: ../build/bin

clean:
	rm -rf build/*

venv: ../build/.venv

../build/.venv:
	mkdir -p ../pip-cache/
	python3 -m venv ../build/.venv
	../build/.venv/bin/python3 -m pip install -r ../requrements.txt --cache-dir ../pip-cache/

../build/bin: ../build/.venv *.py **/*.py
	rm -rf ../build/bin
	../build/.venv/bin/python3 setup.py install_exe -d ../build/bin

copy:
	[ -x ./build/lib* ] && cp -r ./build/$(shell (ls build | grep lib))/* ./build/$(shell (ls build | grep exe))/ || true
