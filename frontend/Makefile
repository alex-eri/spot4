all: ../static ../static/js/libuam.js ../static/js/libadmin.js ../static/js/compat.js

node_modules: package.json
	npm install
	touch node_modules

../static: node_modules
	install -d ../static/css
	install -d ../static/fonts
	install -d ../static/icons
	cp ./icons/* ../static/icons/
	install ./css/animations.css ../static/css/

	cp node_modules/bootstrap/dist/css/*.min* ../static/css/
	cp node_modules/nz-toggle/dist/nz-toggle.min.css ../static/css/
	cp node_modules/bootstrap/dist/fonts/* ../static/fonts/


../static/js/compat.js: node_modules
	node_modules/uglify-js/bin/uglifyjs \
		node_modules/html5shiv/dist/html5shiv.min.js \
		node_modules/json2/lib/JSON2/static/json2.js \
		> ../static/js/compat.js

../static/js:
	install -d ../static/js

../static/js/libuam.js: ../static/js node_modules
	node_modules/uglify-js/bin/uglifyjs \
		node_modules/jquery/dist/jquery.min.js \
		node_modules/es5-shim/es5-shim.js \
		node_modules/es5-shim/es5-sham.js \
		node_modules/angular/angular.js \
		node_modules/angular-route/angular-route.js \
		node_modules/angular-resource/angular-resource.js \
		node_modules/angular-cookies/angular-cookies.js \
		js/md5.js \
		> ../static/js/libuam.js


../static/js/libadmin.js: ../static/js node_modules
	node_modules/uglify-js/bin/uglifyjs \
		node_modules/jquery/dist/jquery.min.js \
		node_modules/moment/moment.js \
		node_modules/angular/angular.min.js \
		node_modules/angular-resource/angular-resource.min.js \
		node_modules/angular-animate/angular-animate.min.js \
		node_modules/angular-route/angular-route.min.js \
		node_modules/angular-i18n/angular-locale_ru.js \
		node_modules/angular-i18n/angular-locale_ru-ru.js \
		node_modules/bootstrap/dist/js/bootstrap.min.js \
		node_modules/nz-toggle/dist/nz-toggle.min.js \
		node_modules/angular-sanitize/angular-sanitize.min.js \
		node_modules/ng-csv/build/ng-csv.min.js \
		> ../static/js/libadmin.js

clean:
	rm -rf ../static

fullclean: clean
	rm -rf bower_components node_modules

compress: ../static node_modules
	./node_modules/.bin/html-minifier  --keep-closing-slash \
		--collapse-whitespace \
		--conservative-collapse \
		--collapse-inline-tag-whitespace \
		--remove-tag-whitespace \
		--sort-attributes --minify-css --file-ext html \
		--input-dir ../static/ --output-dir ../static
	gzip -9 --keep -r -f ../static/
