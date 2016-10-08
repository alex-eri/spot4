all:
	cp ./src/index.html ../static/ht_docs/admin.html
	cp -R ./src/forms/* ../static/ht_docs/admin-forms/
	../static/node_modules/uglify-js/bin/uglifyjs \
		./src/js/admin.js \
		> ../static/ht_docs/js/admin.js
