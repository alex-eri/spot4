(function(app) {
  document.addEventListener('DOMContentLoaded', function() {
    ng.platformBrowserDynamic.bootstrap(app.Login);
    ng.platformBrowserDynamic.bootstrap(app.LoginForms);
  });
})(window.app || (window.app = {}));
