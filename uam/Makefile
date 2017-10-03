all: ../static/js/uam.js ../static/uam-forms/ ../static/uam.html


../static/js:
	install -d ../static/js

../static/uam-forms/: src/forms/*
	mkdir -p ../static/uam-forms/
	cp -R ./src/forms/* ../static/uam-forms/

../static/uam.html: src/index.html
	cp ./src/index.html ../static/uam.html

../static/js/uam.js: ../static/js
	../frontend/node_modules/uglify-js/bin/uglifyjs \
		./src/js/uam.js \
		> ../static/js/uam.js
