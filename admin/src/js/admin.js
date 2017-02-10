'use strict';

var app = angular.module('admin',['ngRoute', 'ngResource','ui.toggle'])
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
      when('/top/:year/:month/', {
        templateUrl: '/static/admin-forms/top.html',
        controller: 'Top'
      }).
      when('/top/', {
        templateUrl: '/static/admin-forms/top.html',
        controller: 'Top'
      }).
      when('/sms/', {
        templateUrl: '/static/admin-forms/sms.html',
        controller: 'Sms'
      }).
      when('/uam/', {
        templateUrl: '/static/admin-forms/uam.html',
        controller: 'Uam'
      }).
      when('/modem/', {
        templateUrl: '/static/admin-forms/modem.html',
        controller: 'Modem'
      }).
      otherwise({
        redirectTo: '/online/'
      });
  }
]);



app.controller('Sms',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "в сети"
        $scope.interval = intervalt;
        $scope.t = datefymd;
        $resource('/db/sms_received/0/23').save(
            [
            {find:{}},
            {sort:["_id",-1]}
        ]
        , function(response){
            $scope.sms_received = response.response;
        }
        );

        $resource('/db/sms_sent/0/23').save(
            [
            {find:{}},
            {sort:["_id",-1]}
        ]
        , function(response){
            $scope.sms_sent = response.response;
        }
        )

    }]);


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


var accounting_group = {'$group': {_id: {
                        year:{'$year':"$start_date"},
                        month :{'$month': "$start_date"},
                        day: {'$dayOfMonth': "$start_date"}
                        },
                        start: {'$min':"$start_time"},
                        stop: {'$max':"$event_time"},
                        count : {'$sum':1},
                        accts :{'$push':'$$CURRENT'},
                        session_time: {'$sum':'$session_time'},
                        output_bytes: {'$sum':'$output_bytes'},
                        input_bytes: {'$sum':'$input_bytes'}
                    }

                }

app.controller('Online',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "в сети"
        $scope.interval = intervalt;
        $scope.t = datefymd;
        $resource('/db/accounting').save(
            [

            {aggregate:[[
                {'$match': {'termination_cause':{$exists: false}} },
                accounting_group,
                {'$sort':{  'start': -1 }}
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
            var y = $routeParams.year , m = $routeParams.month - 1;
        }   else {
            var date = new Date(), y = date.getFullYear(), m = date.getMonth();
        }
            var startdate = new Date(y, m, 1);
            var stopdate = new Date(y, m+1, 1);

        $scope.startdate = startdate;
        $scope.stopdate= stopdate;

        $resource('/db/accounting').save(
            [

            {aggregate:[[
                {'$match': {'start_date':{
                    '$gte': {'$date':startdate.getTime()},
                    '$lte': {'$date':stopdate.getTime()}
                }}},
                {'$sort':{ 'start_date': -1}},
                accounting_group,
                {'$sort':{'start': -1}}
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
                {'$sort':{ 'registred': -1}},
                {'$group': {_id: {
                        username:"$username",
                        },
                        devs :{'$push':'$$CURRENT'},
                        count: {'$sum':1},
                        seen: {'$max':"$seen"},
                        registred: {'$min':"$registred"},
                    }

                },
                {'$sort':{ 'registred': -1}}
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

        $scope.limits = { default:{_id:'default'}}

        $resource('/db/accounting').save(

        [
            {distinct:['callee']}
        ], function(response){

            response.response.forEach( function(item){
                var id = item;
                var item_name=item.replace(/[.:-]/g,"_");
                $scope.limits[item_name]={_id:id};
            })
            }
        )


        $resource('/db/limit').save(
            [
            {find: {} }
        ], function(response){
            response.response.forEach( function(item){
                var id = item._id;
                var item_name=id.replace(/[.:-]/g,"_");
                $scope.limits[item_name]=item;
            })

        })
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
                var id = response.response._id;
                var item_name=id.replace(/[.:-]/g,"_");
                $scope.limits[item_name] = response.response;
            })
        }
    }]);


app.controller('Top',  ['$scope','$resource','$routeParams',
    function ( $scope, $resource ,$routeParams){

        if ($routeParams.month) {
            var y = $routeParams.year , m= $routeParams.month - 1;
        }   else {
            var date = new Date(), y = date.getFullYear(), m = date.getMonth();
        }
        var startdate = new Date(y, m, 1);
        var stopdate = new Date(y, m+1, 1);
        $scope.startdate = startdate;
        $scope.stopdate= stopdate;

        $resource('/db/accounting').save(
            [
                {aggregate:[[
                {'$match': {'start_date':{
                    '$gte': {'$date':startdate.getTime()},
                    '$lte': {'$date':stopdate.getTime()}
                }}},
                {'$group': {_id: {
                        username:"$username"
                        },

                        session_time: {'$sum':"$session_time"},
                        output_bytes: {'$sum':'$output_bytes'},
                        input_bytes: {'$sum':'$input_bytes'}
                    }

                },
                {'$sort':{'session_time':-1}},
                {'$limit': 10 }
                ]]
            }
        ], function(response){
            $scope.users = response.response;
        }
        );
        $resource('/db/accounting').save(
            [
                {aggregate:[[
                {'$match': {'start_date':{
                    '$gte': {'$date':startdate.getTime()},
                    '$lte': {'$date':stopdate.getTime()}
                }}},
                {'$group': {_id: {
                        nas:"$nas"
                        },

                        session_time: {'$sum':"$session_time"},
                        output_bytes: {'$sum':'$output_bytes'},
                        input_bytes: {'$sum':'$input_bytes'},
                        count: { $sum: 1 }
                    }

                },
                {'$sort':{'session_time':-1}},
                {'$limit': 10 }
                ]]
            }
        ], function(response){
            $scope.nases = response.response;
        }
        )
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


app.filter('mega', function() {
  return function(input) {
    if (input > 1073741824) {
        var G = input / 1073741824 ;
        return G.toFixed(1) + 'G';
    }
    var M = input >> 20;
    if( M > 3 )
        return M + 'M';
    var k = input >> 10;
    if( k > 4 )
        return k + 'k';
    return input;
  };
})

app.filter('proto', function() {
  return function(input) {
switch(input) {
    case 6: return 'tcp'
    case 17: return 'udp'
    case 1: return 'icmp'
    case 2: return 'igmp'
    case 47: return 'gre'
    default:return input;
    }
  };
})




app.controller('Uam',  ['$scope','$resource',
    function ( $scope, $resource ){
        $scope.label = "";
        $scope.interval = intervalt;
        $scope.t = datefymd;


    $resource('/admin/themes.json').query(
    function(response){
        $scope.themes = response
    },
    function(error){
        $scope.themes =["default"]
    }
    )

        $scope.limits = { default:{_id:'default'}}

        $resource('/db/accounting').save(

        [
            {distinct:['callee']}
        ], function(response){

            response.response.forEach( function(item){
                var id = item;
                var item_name=item.replace(/[.:-]/g,"_");
                $scope.limits[item_name]={_id:id,newbie:true};
            })
            }
        )


        $resource('/db/uamconfig').save(
            [
            {find: {} }
        ], function(response){
            response.response.forEach( function(item){
                var id = item._id;
                var item_name=id.replace(/[.:-]/g,"_");
                $scope.limits[item_name]=item;
            })

        })
        $scope.update = function(router){
            var id = router._id
            $resource('/db/uamconfig').save([{
            find_and_modify:{
                query:{_id:id},
                update:router,
                upsert:true,
                new:true
                }
            }], function(response){
                console.log(response)
                var id = response.response._id;
                var item_name=id.replace(/[.:-]/g,"_");
                $scope.limits[item_name] = response.response;

            })
        }
    }]);



app.controller('Modem',  ['$scope','$resource',
    function ( $scope, $resource ){
        }]);
