all: clean buildall config

buildall:
	make -C ./server
	make -C ./static
	make -C ./uam
	make -C ./mikrotik
	make -C ./admin
	mkdir -p ./build/{uam,static,admin}/ht_docs
	cp -R ./server/build/exe* ./build
	mkdir -p ./build/mikrotik
	cp -R ./uam/config ./build/uam/
	cp -R ./static/ht_docs/* ./build/static/ht_docs/
	cp -R ./uam/theme ./build/uam/
	cp -R ./mikrotik/build/* ./build/mikrotik/

config:
	mkdir -p ./build/{config,systemd}/
	cp ./systemd/spot.service ./build/systemd/
	install ./server/config.json ./build/config/config.json
	ln -s ../config/config.json ./build/$(shell (ls ./build/ |grep exe))/config.json
	ln -s ../uam/config/ ./build/config/uam


clean:
	rm -rf ./build/*

start:
	cd ./build/exe.* ; ./spot4.exe


netns:
	ip netns add TESTA
	ip link add name ve0a type veth peer name ve0b
	ip link set dev ve0b netns TESTA
	brctl addif virbr1 ve0a
	ip link set dev ve0a up
	ip netns exec TESTA ip link set dev ve0b up
	ip netns exec TESTA dhclient ve0b
	ip netns exec TESTA ip a l


opera:
	resolvconf -u
	ip netns exec TESTA su eri -c "DISPLAY=$(DISPLAY) opera --user-data-dir=/home/eri/.opera_test/"
