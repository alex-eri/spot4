CURRENT_YM := $(shell date +"%y%m")
CURRENT_COMMIT := $(shell git rev-parse --short HEAD)

all: ../static/admin-forms ../static/admin.html ../static/js/admin.js

../static/admin-forms: ./src/forms
	install -d ../static/admin-forms/
	cp -R ./src/forms/* ../static/admin-forms/

../static/admin.html: src/index.html
	install ./src/index.html ../static/admin.html

../static/js:
	install -d ../static/js

../static/js/admin.js: src/js/admin.js ../static/js
	cat src/js/admin.js  | \
		sed -e s/%VERSION%/$(CURRENT_YM)/g -e s/%COMMIT%/$(CURRENT_COMMIT)/g | \
		../frontend/node_modules/uglify-js/bin/uglifyjs \
		> ../static/js/admin.js
