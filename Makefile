buildall:
	make -C ./server
	make -C ./static
	make -C ./uam
	make -C ./mikrotik
	mkdir -p ./build/{uam,static,admin}/ht_docs
	mkdir -p ./build/mikrotik
	rm -rf ./build/exe.*
	cp -R ./server/build/* ./build
	cp -R ./uam/config ./build/uam/
	cp -R ./static/ht_docs/* ./build/static/ht_docs/
	cp -R ./uam/theme ./build/uam/
	cp -R ./mikrotik/build/* ./build/mikrotik/


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
