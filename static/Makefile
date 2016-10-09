all: clean build

build:
	install -d ./ht_docs/js
	install -d ./ht_docs/css
	install -d ./ht_docs/fonts
	install -d ./ht_docs/icons
	cp ./icons/* ./ht_docs/icons/
	install ./css/animations.css ./ht_docs/css/

	cp bower_components/bootstrap/dist/css/*.min* ./ht_docs/css/
	cp bower_components/bootstrap/dist/fonts/* ./ht_docs/fonts/

	npm install
	node_modules/uglify-js/bin/uglifyjs \
		bower_components/angular/angular.min.js \
		bower_components/angular-route/angular-route.min.js \
		bower_components/angular-resource/angular-resource.min.js \
		bower_components/angular-cookies/angular-cookies.js \
		js/md5.js \
		> ./ht_docs/js/libuam.js
	node_modules/uglify-js/bin/uglifyjs \
		bower_components/jquery/dist/jquery.min.js \
		bower_components/angular/angular.min.js \
		bower_components/angular-resource/angular-resource.min.js \
		bower_components/angular-animate/angular-animate.min.js \
		bower_components/angular-route/angular-route.min.js \
		bower_components/angular-i18n/angular-locale_ru.js \
		bower_components/angular-i18n/angular-locale_ru-ru.js \
		bower_components/bootstrap/dist/js/bootstrap.min.js \
		> ./ht_docs/js/libadmin.js

clean:
	rm -rf ht_docs/*

fullclean:
	rm -rf bower_components node_modules

