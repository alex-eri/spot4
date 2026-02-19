all: clean build build/config build/bin

deb:
	dpkg-buildpackage -B -d --no-sign

dist: build/bin
	mkdir -p ./dist/
	cd ./build; tar cz  --transform "flags=r;s|^|opt/spot4/|"  -f ../dist/spot4-$(shell git rev-list --all --count).tar.gz ./

build/bin: build server
	make -C ./server

build/data: build
	mkdir -p ./build/data/
	mkdir -p ./data

build: frontend uam mikrotik admin
	make -C ./frontend all
	make -C ./uam
	make -C ./mikrotik
	make -C ./admin
	make -C ./frontend compress
	mkdir -p ./build/static/
	mkdir -p ./build/mikrotik
	mkdir -p ./build/uam/theme/
	cp -R ./static/* ./build/static/
	cp -R ./uam/theme/* ./build/uam/theme/
	cp -R ./mikrotik/* ./build/mikrotik/

build/config:
	mkdir -p ./build/data/
	mkdir -p ./build/config/
	mkdir -p ./build/etc/systemd/
	mkdir -p ./build/etc/firewalld/services/

	install -m 664 ./systemd/spot.service ./build/etc/systemd/
	ln -s etc/systemd/ ./build/systemd
	install -m 664 ./systemd/firewalld-services-spot.xml ./build/etc/firewalld/services/
	install -m 664 ./config/config.json.example ./build/config/config.json.example


clean:
	rm -rf ./server/build
	rm -rf ./build
	rm -rf ./dist
	make -C ./frontend clean

start:
	cd ./build/bin* ; ./spot4.exe

run:
	cd ./server/; python3 server.py


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
	ip link add link enp5s0 name enp5s0.3 type vlan id 3
	ip link set dev enp5s0.3 netns TESTA


netns:
	ip netns add TESTA

veth:
	ip link add name ve0a type veth peer name ve0b
	ip link set dev ve0b netns TESTA
	brctl addif virbr1 ve0a
	ip link set dev ve0a up

dhclient1:
	ip netns exec TESTA ip link set dev ve0b up
	ip netns exec TESTA dhcpcd ve0b
	ip netns exec TESTA ip a l

dhclient2:
	ip netns exec TESTA ip link set dev enp5s0.3 up
	ip netns exec TESTA dhcpcd enp5s0.3
	ip netns exec TESTA ip a l



opera:
	ip netns exec TESTA su eri -c "DISPLAY=$(DISPLAY) opera --user-data-dir=/home/eri/.opera_test/"


operaonmikrotik: netns mikrobr dhclient2 opera

IPonAS:
	whois -h whois.radb.net -i origin -T route `cat $$AS-asn` | grep route: | awk '{print $2}' > ./$$AS-ip

setupNetNS:
	ip netns add TESTA
	ip link add name ve0a type veth peer name ve0b
	ip link set dev ve0b netns TESTA
	brctl addif bridge2 ve0a
	ip link set dev ve0a up
	ip netns exec TESTA ip link set dev ve0b up
	ip netns exec TESTA dhcpcd ve0b
	ip netns exec TESTA ip a l

testNetNS:
	ip netns exec TESTA ip a l
	ip netns exec TESTA /usr/bin/nslookup ya.ru
	ip netns exec TESTA curl http://ifconfig.me

chromeNetNS:
	ip netns exec TESTA su eri -c "DISPLAY=$(DISPLAY) google-chrome --user-data-dir=/home/eri/.config/chromeNetNS --profile-directory=TestProfile  --new-window http://ya.ru"
