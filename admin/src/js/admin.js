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
      when('/accounting/:year/:month/', {
        templateUrl: '/static/admin-forms/online.html',
        controller: 'Accs'
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

function pad(num) {
    var s = "0" + num;
    return s.substr(s.length-2);
}

function intervalt(time,start){
    if (time) {
        return {
        s : pad(time % 60),
        m : pad(Math.floor(time/60) % 60),
        h : pad(Math.floor(time/3600) % 24),
        d : Math.floor(time/86400)
        }
    } else {
        console.log(start);
        var now = new Date();
        var t = Date.UTC(now.getUTCFullYear(),now.getUTCMonth(), now.getUTCDate() ,
      now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds(), now.getUTCMilliseconds());
        console.log(t);
        return intervalt((t-start)/1000);
     }

}



function datefymd(id) {
            return new Date(id.year , id.month - 1, id.day);
        };


app.controller('Online',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "в сети"
        $scope.interval = intervalt;
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
                {'$sort':{  '_id.day': -1, '_id.year': -1,'_id.month': -1 }}
                ]]
            }
        ], function(response){
            $scope.online = response;
        }
        )
    }]);

app.controller('Accs',  ['$scope','$resource','$routeParams',
    function ( $scope, $resource, $routeParams){
        $scope.label = "";
        $scope.interval = intervalt;
        $scope.t = datefymd;

        if ($routeParams.month) {
            var y = $routeParams.year , m= $routeParams.month - 1;
        }   else {
            var date = new Date(), y = date.getFullYear(), m = date.getMonth();
        }
            var startdate = new Date(y, m, 1);
            var stopdate = new Date(y, m+1, 1);
        $resource('/db/accounting').save(
            [

            {aggregate:[[
                {'$match': {'start_date':{
                    '$gte': {'$date':startdate.getTime()},
                    '$lte': {'$date':stopdate.getTime()}
                }}},
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
                {'$sort':{'_id.day': -1}}
                ]]
            }
        ], function(response){
            $scope.online = response;
        }
        )
    }]);

app.controller('Regs',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "";
        $scope.interval = intervalt;
        $scope.t = datefymd;
        $resource('/db/devices').save(
            [

            {aggregate:[[

                {'$group': {_id: {
                        username:"$username",
                        },
                        devs :{'$push':'$$CURRENT'},
                        count: {'$sum':1},
                        seen: {'$max':"$seen"}
                    }

                },
            {'$sort':{ 'seen': -1}}
                ]]
            }
        ], function(response){
            $scope.registred = response.response;
        }
        )
    }]);