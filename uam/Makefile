all:
	mkdir -p ../static/uam-forms/
	cp ./src/index.html ../static/uam.html
	cp -R ./src/forms/* ../static/uam-forms/
	../frontend/node_modules/uglify-js/bin/uglifyjs \
		./src/js/uam.js \
		> ../static/js/uam.js
