all: clean build build/config

dist: build
	mkdir -p ./dist/
	cd ./build; tar cz  --transform "flags=r;s|^|opt/spot4/|"  -f ../dist/spot4-$(shell (ls ./server/build/ |grep exe)).tar.gz ./

server/build:
	make -C ./server

build: server/build
	make -C ./frontend
	make -C ./uam
	make -C ./mikrotik
	make -C ./admin
	make -C ./frontend compress
	mkdir -p ./build/static/
	cp -R ./server/build/exe* ./build/bin
	mkdir -p ./build/mikrotik
	mkdir -p ./build/uam/theme/
	cp -R ./static/* ./build/static/
	cp -R ./uam/theme/* ./build/uam/theme/
	cp -R ./mikrotik/* ./build/mikrotik/

build/config:
	mkdir -p ./build/config/
	mkdir -p ./build/systemd/
	install -m 664 ./systemd/spot.service ./build/systemd/
	install -m 664 ./config/config.json ./build/config/config.json.example


clean:
	rm -rf ./server/build
	rm -rf ./build
	rm -rf ./dist
	make -C ./frontend clean

start:
	cd ./build/bin* ; ./spot4.exe



submodule:
	git submodule init
	git submodule update --remote


ctypescrypto: submodule

ctypescrypto/build: ctypescrypto
	cd ./ctypescrypto && python setup.py build
	cd ./ctypescrypto && python setup.py install --user

numpy: submodule

numpy/build: numpy
	cd ./numpy && BLAS=None python setup.py build
	cd ./numpy && python setup.py install --user



mikrobr:
	ip link add link net1 name net1.3 type vlan id 3
	ip link set dev net1.3 netns TESTA


netns:
	ip netns add TESTA
	ip link add name ve0a type veth peer name ve0b
	ip link set dev ve0b netns TESTA
	brctl addif virbr1 ve0a
	ip link set dev ve0a up

dhclient1:
	ip netns exec TESTA ip link set dev ve0b up
	ip netns exec TESTA dhclient ve0b
	ip netns exec TESTA ip a l

dhclient2:
	ip netns exec TESTA ip link set dev net1.3 up
	ip netns exec TESTA dhclient net1.3
	ip netns exec TESTA ip a l



opera:
	ip netns exec TESTA su eri -c "DISPLAY=$(DISPLAY) opera --user-data-dir=/home/eri/.opera_test/"


IPonAS:
	whois -h whois.radb.net -i origin -T route `cat $$AS-asn` | grep route: | awk '{print $2}' | aggregate > ./$$AS-ip

