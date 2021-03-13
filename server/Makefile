all: ../build/bin

clean:
	rm -rf build/*

../build/bin: *.py **/*.py
	python3 -m pip install -r ../requrements.txt
	rm -rf ../build/bin
	python3 setup.py install_exe -d ../build/bin

copy:
	[ -x ./build/lib* ] && cp -r ./build/$(shell (ls build | grep lib))/* ./build/$(shell (ls build | grep exe))/ || true
