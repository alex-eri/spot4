'use strict';

var app = angular.module('admin',['ngRoute', 'ngResource'])
window.app = app;
var waittemplate = '<center><div class="spinner"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div></center>';

app.config(['$routeProvider','$locationProvider',
  function($routeProvider, $locationProvider) {
    $locationProvider.html5Mode(
        {
        enabled: true,
        requireBase: true,
        rewriteLinks: true
        }
    ).hashPrefix('!');
    $routeProvider.
      when('/wait/', {
        template: waittemplate
      }).
      when('/online/', {
        templateUrl: '/static/admin-forms/online.html',
        controller: 'Online'
      }).
      when('/accounting/', {
        templateUrl: '/static/admin-forms/online.html',
        controller: 'Accs'
      }).
      when('/registrations/', {
        templateUrl: '/static/admin-forms/registrations.html',
        controller: 'Regs'
      }).
      otherwise({
        redirectTo: '/online/'
      });
  }
]);

function daysf(time){
            return Math.floor(time/86400)
        }

function datefymd(id) {
            return new Date(id.year , id.month - 1, id.day);
        };

app.controller('Online',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "в сети"
        $scope.days = daysf;
        $scope.t = datefymd;
        $resource('/db/accounting').save(
            [

            {aggregate:[[
                {'$match': {'termination_cause':{$exists: false}} },
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
        ], function(response){
            $scope.online = response;
        }
        )
    }]);

app.controller('Accs',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "";
        $scope.days = daysf;
        $scope.t = datefymd;
        $resource('/db/accounting').save(
            [

            {aggregate:[[
                //{'$match': {'termination_cause':{$exists: false}} },
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
        ], function(response){
            $scope.online = response;
        }
        )
    }]);
