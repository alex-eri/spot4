IP ?= 192.168.236.34
PORT ?= 8080

all:
	rm -rf build
	install -d build
	install src/rlogin.html build/rlogin.html
	install src/rlogin.html build/login.html
	install src/rlogin.html build/falogin.html
	install src/rlogin.html build/fstatus.html
	install src/rlogin.html build/flogout.html
	install src/rlogin.html build/logout.html
	install -d build/jsonp
	install src/jsonp/login.html build/jsonp/login.html
	install src/jsonp/login.html build/jsonp/alogin.html
	install src/jsonp/login.html build/jsonp/status.html
	install src/jsonp/login.html build/jsonp/fstatus.html
	sed -i -- 's/{IP}/$(IP)/g'  build/*.html
	sed -i -- 's/{PORT}/$(PORT)/g'  build/*.html
