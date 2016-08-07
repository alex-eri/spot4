'use strict';

var app = angular.module('hotspot',['ngRoute', 'ngResource', 'ngAnimate'])

.run(['$http','$rootScope','$route',
    function ($http,$rootScope) {

        $http.defaults.headers.common.Authorization = 'Basic YWRtaW46dGVzdGluZzEyMw==';

        function onAPI(APIURL){
            $http.get(APIURL+'/salt').then(
                function(response) {
                    app.SALT = response.data.salt;
                }, function(error){
                    $rootScope.error = "Сервер не отвечает, попробуйте позже";
                    $rootScope.stage = 'error';
                });
        };


        $http.get('config.json').then( function(response) {
            console.log(response.data);
            app.APIURL = response.data.api;
            document.title = response.data.title || 'Spot 4 adminka';
            $rootScope.config = response.data ;
            onAPI(app.APIURL)
            }
         ,function(error) { alert('Не найду локальный кофиг/ Хотспот сломался') });

    }
]);


app.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/accounting', {
        templateUrl: 'partials/accounting.html',
        controller: 'AccountingCtrl'
      }).
      when('/status', {
        templateUrl: 'partials/status.html',
        controller: 'StatusCtrl'
      }).
      otherwise({
        redirectTo: '/status'
      });
  }]);

app.factory('Accounting', ['$resource',
    function($resource) {
      return $resource( app.APIURL + '/db/accounting/');
    }]);

app.controller('AccountingCtrl',['$scope', '$http',
function($scope, $http) {
    var pipe = JSON.stringify([]);
     $http.post( app.APIURL + '/db/accounting' ,pipe).success(
        function(data){
            console.log(data);
            $scope.accounting = data.response
        }
        )

}
])

app.controller('StatusCtrl',['$scope',
function($scope) {

}
])
