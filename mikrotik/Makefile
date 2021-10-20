IP ?= 192.168.236.34
PORT ?= 8080
PROTO ?= http

all: clean build

clean:
	rm -rf build
build:
	install -d build
	install -d build/$(PROTO).$(IP).$(PORT)/
	cp -R orig/* build/$(PROTO).$(IP).$(PORT)/
	install src/hotspot.rsc build/$(PROTO).$(IP).$(PORT)/hotspot.rsc
	install src/rlogin.html build/$(PROTO).$(IP).$(PORT)/login.html
	install src/rlogin.html build/$(PROTO).$(IP).$(PORT)/status.html
	install src/rlogin.html build/$(PROTO).$(IP).$(PORT)/error.html
	install src/rlogin.html build/$(PROTO).$(IP).$(PORT)/logout.html
	install -d build/$(PROTO).$(IP).$(PORT)/jsonp
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/login.html
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/flogin.html
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/logout.html
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/flogout.html
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/alogin.html
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/status.html
	install src/jsonp/login.html build/$(PROTO).$(IP).$(PORT)/jsonp/fstatus.html
	sed -i -- 's/{IP}/$(IP)/g'  build/$(PROTO).$(IP).$(PORT)/*.*
	sed -i -- 's/{PORT}/$(PORT)/g'  build/$(PROTO).$(IP).$(PORT)/*.*
	sed -i -- 's/{PROTO}/$(PROTO)/g'  build/$(PROTO).$(IP).$(PORT)/*.*
