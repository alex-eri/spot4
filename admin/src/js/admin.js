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
      when('/limits/', {
        templateUrl: '/static/admin-forms/limits.html',
        controller: 'Limit'
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
    } else if (time === 0){
        return {
            s : '00',
            m : '00',
            h : '00',
            d : 0
        }
    }
    else {
//        console.log(start);
//        var now = new Date();
//        var t = Date.UTC(now.getUTCFullYear(),now.getUTCMonth(), now.getUTCDate() ,
//      now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds(), now.getUTCMilliseconds());
//        console.log(t);
//        return intervalt((t-start)/1000);
        return intervalt(0);
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
                {'$sort':{ 'start_date': -1}},
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
                {'$sort':{ 'seen': -1}},
                {'$group': {_id: {
                        username:"$username",
                        },
                        devs :{'$push':'$$CURRENT'},
                        count: {'$sum':1},
                        seen: {'$max':"$seen"}
                    }

                }
                ]]
            }
        ], function(response){
            $scope.registred = response.response;
        }
        )
    }]);

app.controller('Limit',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "";
        $scope.interval = intervalt;
        $scope.t = datefymd;
        $resource('/db/limit').save(
            [
            {find: {} }
        ], function(response){
            var nodefault = true ;
            response.response.forEach( function(item){
                if (item._id == "default") nodefault = false;
            })

            if (nodefault)
                response.response.push({_id:'default'})

            $scope.limits = response.response;
        }
        )
        $scope.update = function(router){
            var id = router._id
            $resource('/db/limit').save([{
            find_and_modify:{
                query:{_id:id},
                update:router,
                upsert:true,
                new:true
                }
            }], function(response){
                console.log(response)
                $scope.limits.forEach( function(item,i){
                    if (response._id == id )
                        $scope.limits[i] = response;
                })

            })
        }
    }]);

app.controller("MenuCtrl", function($scope, $location) {
  $scope.menuClass = function(page) {
    var current = $location.path().substring(1);
    return current.startsWith(page) ? "active" : "";
  };
});

app.filter('interval', function() {
  return function(input) {
    input = input || 0;
    var t = intervalt(input);
    var out = '';
    if (t.d) out = out + t.d + 'd ';
    out = out + t.h+':'+ t.m +':'+t.s;
    return out;
  };
})
