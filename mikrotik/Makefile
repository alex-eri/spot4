IP ?= 192.168.236.34
PORT ?= 8080

all: clean build

clean:
	rm -rf build
build:
	install -d build
	install -d build/$(IP)
	install src/rlogin.html build/$(IP)/rlogin.html
	install src/rlogin.html build/$(IP)/login.html
	install src/rlogin.html build/$(IP)/falogin.html
	install src/rlogin.html build/$(IP)/fstatus.html
	install src/rlogin.html build/$(IP)/flogout.html
	install src/rlogin.html build/$(IP)/logout.html
	install -d build/$(IP)/jsonp
	install src/jsonp/login.html build/$(IP)/jsonp/login.html
	install src/jsonp/login.html build/$(IP)/jsonp/flogin.html
	install src/jsonp/login.html build/$(IP)/jsonp/logout.html
	install src/jsonp/login.html build/$(IP)/jsonp/flogout.html
	install src/jsonp/login.html build/$(IP)/jsonp/alogin.html
	install src/jsonp/login.html build/$(IP)/jsonp/status.html
	install src/jsonp/login.html build/$(IP)/jsonp/fstatus.html
	sed -i -- 's/{IP}/$(IP)/g'  build/$(IP)/*.html
	sed -i -- 's/{PORT}/$(PORT)/g'  build/$(IP)/*.html
