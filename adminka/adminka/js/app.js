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
         ,function(error) { alert('Не найду локальный кофиг/ Хотспот сломался?') });

    }
]);

app.filter('int2ip', function () {
        return function (ipl) {
            return ( (ipl>>>24) +'.' +
              (ipl>>16 & 255) +'.' +
              (ipl>>8 & 255) +'.' +
              (ipl & 255) );;
        };
    });

app.filter('dict2date', function () {
        return function (dict) {
            return new Date(dict.year, dict.month-1, dict.day)
        };
    });

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


app.controller('AccountingCtrl',['$scope', '$http',
function($scope, $http) {

    var pipe = JSON.stringify([
            {aggregate:[[
                {'$group': {_id: {
                        year:{'$year':"$start_date"},
                        month :{'$month': "$start_date"},
                        day: {'$dayOfMonth': "$start_date"}
                        },
                        accts :{'$push':'$$CURRENT'},
                        session_time: {'$sum':'$session_time'},
                        output_bytes: {'$sum':'$output_bytes'},
                        input_bytes: {'$sum':'$input_bytes'}
                    }

                },
                {'$sort':{ '_id.year': -1, '_id.month': -1 , '_id.day': -1}}
                ]]
            }
        ]);
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
