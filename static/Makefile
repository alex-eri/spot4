all: clean ht_docs compress

bower_components:
	npm install

node_modules:
	npm install

ht_docs: bower_components
	install -d ./ht_docs/js
	install -d ./ht_docs/css
	install -d ./ht_docs/fonts
	install -d ./ht_docs/icons
	cp ./icons/* ./ht_docs/icons/
	install ./css/animations.css ./ht_docs/css/

	rm -rf ./ht_docs/static

	cp bower_components/bootstrap/dist/css/*.min* ./ht_docs/css/
	cp bower_components/nz-toggle/dist/nz-toggle.min.css ./ht_docs/css/
	cp bower_components/bootstrap/dist/fonts/* ./ht_docs/fonts/

	node_modules/uglify-js/bin/uglifyjs \
		bower_components/html5shiv/dist/html5shiv.min.js \
		bower_components/json2/json2.js \
		> ./ht_docs/js/compat.js

	node_modules/uglify-js/bin/uglifyjs \
		bower_components/es5-shim/es5-shim.js \
		bower_components/es5-shim/es5-sham.js \
		bower_components/angular/angular.js \
		bower_components/angular-route/angular-route.js \
		bower_components/angular-resource/angular-resource.js \
		bower_components/angular-cookies/angular-cookies.js \
		js/md5.js \
		> ./ht_docs/js/libuam.js

	node_modules/uglify-js/bin/uglifyjs \
		bower_components/jquery/dist/jquery.min.js \
		bower_components/moment/moment.js \
		bower_components/angular/angular.min.js \
		bower_components/angular-resource/angular-resource.min.js \
		bower_components/angular-animate/angular-animate.min.js \
		bower_components/angular-route/angular-route.min.js \
		bower_components/angular-i18n/angular-locale_ru.js \
		bower_components/angular-i18n/angular-locale_ru-ru.js \
		bower_components/bootstrap/dist/js/bootstrap.min.js \
		bower_components/nz-toggle/dist/nz-toggle.min.js \
		> ./ht_docs/js/libadmin.js

ht_docs/static:
	ln -s . ./ht_docs/static

clean:
	rm -rf ht_docs

fullclean:
	rm -rf bower_components node_modules

compress: ht_docs node_modules
	./node_modules/.bin/html-minifier --html5 --keep-closing-slash \
		--collapse-whitespace \
		--conservative-collapse \
		--collapse-inline-tag-whitespace \
		--remove-tag-whitespace \
		--sort-attributes --minify-css --file-ext html \
		--input-dir ./ht_docs/ --output-dir ./ht_docs/
