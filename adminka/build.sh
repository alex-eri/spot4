TARGET=`pwd`/build/adminka
mkdir -p ${TARGET}
install -d ${TARGET}/js
install -d ${TARGET}/style
install -d ${TARGET}/style/css
install -d ${TARGET}/style/fonts
install -d ${TARGET}/partials
install -d ${TARGET}/templates
install -d ${TARGET}/json

install bower_components/bootstrap/dist/fonts/* ${TARGET}/style/fonts/
install bower_components/bootstrap/dist/css/bootstrap.min.css ${TARGET}/style/css/

pushd adminka/
install index.html ${TARGET}
install config.json ${TARGET}
install style/*.css ${TARGET}/style/
install templates/*.html ${TARGET}/templates/
install partials/*.html ${TARGET}/partials/

install *favicon* ${TARGET}/

popd


node_modules/uglify-js/bin/uglifyjs adminka/js/app.js -o ${TARGET}/js/app.js -c
node_modules/uglify-js/bin/uglifyjs \
    bower_components/jquery/dist/jquery.min.js \
    bower_components/angular/angular.min.js \
    bower_components/angular-resource/angular-resource.min.js \
    bower_components/angular-animate/angular-animate.min.js \
    bower_components/angular-route/angular-route.min.js \
    > ${TARGET}/js/library.js
