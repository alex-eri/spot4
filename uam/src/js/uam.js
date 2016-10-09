'use strict';

var app = angular.module('uam',['ngRoute', 'ngResource','ngCookies'])

window.app = app;

app.directive('phoneValidation', function(){
   return {
     require: 'ngModel',
     link: function(scope, element, attrs, modelCtrl) {

       modelCtrl.$parsers.push(function (inputValue) {

         var transformedInput = inputValue.replace(/[^\d+]/g,'').replace(/^89/g,'+79');

         if (transformedInput!=inputValue) {
           modelCtrl.$setViewValue(transformedInput);
           modelCtrl.$render();
         }

         return transformedInput;
       });
     }
   };
});


app.directive('codeValidation', function(){
   return {
     require: 'ngModel',
     link: function(scope, element, attrs, modelCtrl) {

       modelCtrl.$parsers.push(function (inputValue) {
         var transformedInput = inputValue;

         if (typeof(inputValue)== "number") {
                transformedInput = Math.floor(inputValue) % 1000000;
         } else {
                transformedInput = String(inputValue).replace(/[^\d]/g,'');
            }
         if (transformedInput!=inputValue) {
           modelCtrl.$setViewValue(transformedInput);
           modelCtrl.$render();
         }

         return transformedInput;
       });
     }
   };
});

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
      when('/register/', {
        templateUrl: '/static/uam-forms/register.html',
        controller: 'Register'
      }).
      when('/status/', {
        templateUrl: '/static/uam-forms/status.html',
        controller: 'Status'
      }).
      when('/check/sms/', {
        templateUrl: '/static/uam-forms/check-sms.html',
        controller: 'Check'
      }).
      when('/wait/sms/', {
        templateUrl: '/static/uam-forms/wait-sms.html',
        controller: 'Check'
      }).
      when('/login/', {
        template: waittemplate,
        controller: 'Login'
      }).
      otherwise({
        redirectTo: '/status/'
      });
  }]);



app.controller('Register',  ['$rootScope','$resource','$cookies','$location','$window',
    function ( $scope, $resource, $cookies ,$location,$window){
        var mac = $location.$$search.mac || $cookies.get('mac');
        $scope.register = function(form) {
            console.log(form);
            if (form.$valid) {
                $resource('/register/').save(

                    {phone:form.phone.$modelValue, mac: mac, smsmode: form.smsmode.$modelValue},

                function(response) {
                    $scope.device = response;
                    $location.search('device', response._id.$oid);
                    $cookies.put('device', response._id.$oid);
                    if (response.checked) {
                        $location.search('password', response.password);
                        $location.search('username', response.username);
                        $location.path('/login/');
                        }
                    else if (response.sms_sent)
                        $location.path('/check/sms/')
                    else
                        $location.path('/wait/sms/')

                },
                function(error) {
                    $window.alert('Не сработало...Может Интернет сломался.');
                    $location.path('/register/');
                });
            }
        }


    }]);


function hex2bin(str) {
    return str.match(/.{1,2}/g).map(function(v){
      return String.fromCharCode(parseInt(v, 16));
    }).join('');
}


app.controller('Login',  ['$window','$resource','$cookies','$location','$http',
    function ( $window, $resource, $cookies ,$location,$http){
        var username =    $location.$$search.username;
        var password =    $location.$$search.password;
        var ischilli = $cookies.get('uamip');
        if (ischilli)
            var chilli = 'http://'+$cookies.get('uamip')+':'+$cookies.get('uamport') +'/json/';

        function onerror(error){
            console.log('login failed');
            $window.location.href=$cookies.get('linklogout') || 'http://ya.ru/'  ;
        }

        function onchillilogin(response) {
            console.log(response)
                if (response.redir.redirectionURL) {
                    console.log(response.redir.redirectionURL)
                    $window.location.href=response.redir.redirectionURL
                }
                else if (response.redir.originalURL) {
                    console.log(response.redir.originalURL)
                    $window.location.href=response.redir.originalURL
                } else {
                    $location.path('/status/')
                }
        }

        function onchillistatus(response) {

            var challenge = hex2bin(response.challenge);
            var chapid = '\x00';

            var charpassw = hexMD5(chapid + password + challenge);

            console.log(hex2bin(charpassw));
            console.log(password);


            $resource(chilli+'logon',
                {
                    username:username,
                    response:charpassw,
                    callback:"JSON_CALLBACK"
                },
                {get:{ method: 'JSONP'}}
            ).get(onchillilogin)
            if (response.redir.logoutURL) $cookies.put('linklogout', response.redir.logoutURL);
        }

        function onmikrotikstatus(response){

                var charpassw = hexMD5(response.chapid + password + response.challenge);
                $resource($cookies.get('linklogin'),
                {
                    target:'jsonp',
                    dst:$cookies.get('linkorig'),
                    username:username,
                    password:charpassw,
                    var:"JSON_CALLBACK"
                },
                {get:{ method: 'JSONP'}}).get(onchillilogin)
                if (response.redir.logoutURL) $cookies.put('linklogout', response.redir.logoutURL);
        }


        if (username && password) {
            if(ischilli) {
                //chilli
                $resource(chilli+'status', { callback:"JSON_CALLBACK"},
                {get:{ method: 'JSONP'}}
                ).get(onchillistatus,onerror)
            } else {
                //mikrotik

                $resource($cookies.get('linklogin'),
                {
                    target:'jsonp',
                    var:"JSON_CALLBACK"
                },
                {get:{ method: 'JSONP'}}).get(onmikrotikstatus,onerror)


            }
        } else {
            onerror({})
        }

}]);


app.controller('Check',  ['$rootScope','$resource','$cookies','$location', '$window',
    function ( $scope, $resource, $cookies ,$location,$window){
        $scope.wrongcode = false;
        $scope.code = null;
        var oid = $location.$$search.device || $cookies.get('device');

        function prelogin(response){
            $scope.device=response;
            console.log(response);
            $scope.device = response;
            if (response.password) {
                $location.search('password', response.password);
                $location.search('username', response.username);
                $location.path('/login/')
            } else {
                $scope.wrongcode = true;
                $scope.code = null;
            }
        }
        function onerror(error) {
                        $window.alert('Не сработало...Попробуйте с начала. Похоже Сервер Вас не помнит.');
                        $window.location.href=$cookies.get('linklogout') || 'http://ya.ru/'  ;
                }

        if ($scope.device) {
        } else {
             $resource('/device/:oid').get({
                    'oid': oid
                },
                prelogin,onerror
             )
        }

        $scope.confirm = function(form) {if (form.$valid) {

            console.log(form);

            //TODOdisable form
            $resource('/device/:oid').save(
                {
                    'oid': oid
                },
                {
                    'oid': oid,
                    'sms_sent': form.code.$viewValue
                },
                prelogin,onerror

            );


        }}

    }]);

app.controller('Status',  ['$rootScope','$resource','$cookies',
    function ( $scope, $resource, $cookies ){

    var ischilli = $cookies.get('uamip');

    function onstatus(response){
        $scope.status = response;
    }

    if(ischilli) {
        //chilli
        var chilli = 'http://'+$cookies.get('uamip')+':'+$cookies.get('uamport') +'/json/';
        $resource(chilli+'status', { callback:"JSON_CALLBACK"},
        {get:{ method: 'JSONP'}}
        ).get(onstatus)
    } else {
        //mikrotik

        $resource($cookies.get('linklogin').replace('login','status'),
        {
            target:'jsonp',
            var:"JSON_CALLBACK"
        },
        {get:{ method: 'JSONP'}}).get(onstatus)

    }

    }]);


app.run(['$route','$location','$rootScope','$resource','$cookies',
 function ($route,$location,$scope,$resource,$cookies) {
    console.log($location);
    console.log($route);

    for (var key in $location.$$search){
        $cookies.put(key, $location.$$search[key]);
        console.log(key);
        console.log($location.$$search[key])
        if (key == 'uamip'){
            $cookies.remove('linklogin');
            }
        if (key == 'linklogin') {
            $cookies.remove('uamip');
        }
    }

    console.log($cookies.getAll())

    $resource('/uam/config/:nasid.json').get(
    {nasid:$cookies.get('nasid')},
    function(response){
        $scope.config = response
    },
    function(error){
        $scope.config ={
            smsmode:'wait',
            password_auth:true,
            theme:"default"
            }
    }
    )


}
]);

