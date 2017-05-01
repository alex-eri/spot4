all: clean ../static

bower_components:
	npm install

node_modules:
	npm install

../static: bower_components
	install -d ../static/js
	install -d ../static/css
	install -d ../static/fonts
	install -d ../static/icons
	cp ./icons/* ../static/icons/
	install ./css/animations.css ../static/css/

	cp bower_components/bootstrap/dist/css/*.min* ../static/css/
	cp bower_components/nz-toggle/dist/nz-toggle.min.css ../static/css/
	cp bower_components/bootstrap/dist/fonts/* ../static/fonts/

	node_modules/uglify-js/bin/uglifyjs \
		bower_components/html5shiv/dist/html5shiv.min.js \
		bower_components/json2/json2.js \
		> ../static/js/compat.js

	node_modules/uglify-js/bin/uglifyjs \
		bower_components/es5-shim/es5-shim.js \
		bower_components/es5-shim/es5-sham.js \
		bower_components/angular/angular.js \
		bower_components/angular-route/angular-route.js \
		bower_components/angular-resource/angular-resource.js \
		bower_components/angular-cookies/angular-cookies.js \
		js/md5.js \
		> ../static/js/libuam.js

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
		> ../static/js/libadmin.js

clean:
	rm -rf ../static

fullclean:
	rm -rf bower_components node_modules

compress: ../static node_modules
	./node_modules/.bin/html-minifier --html5 --keep-closing-slash \
		--collapse-whitespace \
		--conservative-collapse \
		--collapse-inline-tag-whitespace \
		--remove-tag-whitespace \
		--sort-attributes --minify-css --file-ext html \
		--input-dir ../static/ --output-dir ../static
	gzip -9 --keep -r -f ../static/
