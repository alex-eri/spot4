all: ../static/admin-forms ../static/admin.html ../static/js/admin.js

../static/admin-forms:
	install -d ../static/admin-forms/
	cp -R ./src/forms/* ../static/admin-forms/

../static/admin.html:
	install ./src/index.html ../static/admin.html

../static/js/admin.js:
	../frontend/node_modules/uglify-js/bin/uglifyjs \
		./src/js/admin.js \
		> ../static/js/admin.js
