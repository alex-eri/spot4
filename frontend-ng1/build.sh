TARGET=`pwd`/build/mikrotik
mkdir -p ${TARGET}
install -d ${TARGET}/js
install -d ${TARGET}/style
install -d ${TARGET}/style/css
install -d ${TARGET}/style/fonts
install -d ${TARGET}/partials
install -d ${TARGET}/templates
install -d ${TARGET}/json
pushd mikrotik/
install *.html ${TARGET}

install index.html ${TARGET}/login.html
install index.html ${TARGET}/alogin.html
install index.html ${TARGET}/status.html
install index.html ${TARGET}/logout.html

install json/login.html ${TARGET}/json/
install json/login.html ${TARGET}/json/alogin.html
install json/login.html ${TARGET}/json/status.html
install json/login.html ${TARGET}/json/logout.html

install config.json ${TARGET}
install js/app.js ${TARGET}/js/
install js/jquery/dist/jquery.min.js ${TARGET}/js/
install js/angular/angular.min.js ${TARGET}/js/
install js/angular-resource/angular-resource.min.js ${TARGET}/js/
install js/angular-animate/angular-animate.min.js ${TARGET}/js/
install style/fonts/* ${TARGET}/style/fonts/
install style/css/bootstrap.min.css ${TARGET}/style/css/
install style/*.css ${TARGET}/style/
install templates/*.html ${TARGET}/templates/
install partials/*.html ${TARGET}/partials/
popd
