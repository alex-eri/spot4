all:
	mkdir -p ../static/ht_docs/uam-forms/
	cp ./src/index.html ../static/ht_docs/uam.html
	cp -R ./src/forms/* ../static/ht_docs/uam-forms/
	../static/node_modules/uglify-js/bin/uglifyjs \
		./src/js/uam.js \
		> ../static/ht_docs/js/uam.js
