ASN = $$(cat ./${AS}-asn)

IPonAS:
	whois -h whois.radb.net -i origin -T route ${ASN} | grep route: | awk '{print $$2}' | aggregate > ./${AS}-ip
	cat ./${AS}-ip | awk '{print "/ip firewall address-list add list=${AS} address="$$1}' > ./${AS}-ip.rsc


