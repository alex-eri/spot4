
app.factory('Client', ['$resource',
    function($resource) {
      return $resource('/json/login.html');
    }]);

app.factory('Status', ['$resource',
    function($resource) {
      return $resource('/json/status.html');
    }]);
