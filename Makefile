all: clean buildall config

dist:
	mkdir -p ./dist/
	cd ./build; tar cz -f ../dist/spot4-$(shell (ls ./build/ |grep exe)).tar.gz ./

buildall:
	make -C ./server
	make -C ./static
	make -C ./uam
	make -C ./mikrotik
	make -C ./admin
	mkdir -p ./build/static/ht_docs
	cp -R ./server/build/exe* ./build
	mkdir -p ./build/mikrotik
	mkdir -p ./build/uam/{config,theme}/
	cp -R ./uam/config/* ./build/uam/config/
	cp -R ./static/ht_docs/* ./build/static/ht_docs/
	cp -R ./uam/theme/* ./build/uam/theme/
	cp -R ./mikrotik/* ./build/mikrotik/

config:
	mkdir -p ./build/{config,systemd}/
	cp ./systemd/spot.service ./build/systemd/
	install ./server/config.json ./build/config/config.json
	ln -s ../config/config.json ./build/$(shell (ls ./build/ |grep exe))/config.json
	ln -s ../uam/config/ ./build/config/uam


clean:
	rm -rf ./build/*
	rm -rf ./dist

start:
	cd ./build/exe.* ; ./spot4.exe


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
	whois -h whois.radb.net -i origin -T route `cat $$AS-asn` | grep route: | awk '{print $2}' | aggregate > /home/eri/Projects/Spot4/$$AS-ip

