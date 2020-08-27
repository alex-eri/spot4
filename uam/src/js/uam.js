'use strict';

var app = angular.module('uam',['ngRoute', 'ngResource','ngCookies'])

window.app = app;

app.directive('phoneValidation', function(){
   return {
     require: 'ngModel',
     link: function(scope, element, attrs, modelCtrl) {

       modelCtrl.$parsers.push(function (inputValue) {

         var transformedInput = inputValue
            .replace(/[^\d+]/g,'')
            .replace(/^89/g,'+79')
            .replace(/^79/g,'+79')
            .replace(/^9/g,'+79')
            .replace(/^380/g,'+380') // ukr
            .replace(/^(02)([459])/g,'+3752$2') //belarus
            .replace(/^033/g,'+37533')
            .replace(/^044/g,'+37544')
            .replace(/^059/g,'+9989') // uzbekistan
            .replace(/^59/g,'+9989')  // uzbekistan
            .replace(/^7([04567])/g,'+77$1') //kazahstan
            ;

         if (transformedInput!=inputValue) {
           modelCtrl.$setViewValue(transformedInput);
           element.val('');
           element.val(transformedInput);
           //modelCtrl.$render();
//           setCaretPosition(element,len(transformedInput));
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

        var transformedInput = String(inputValue).replace(/[^\d]/g,'');
        var transformedInputView = transformedInput

            if (transformedInput.length > 3) {

              transformedInputView = ""
              var i=0;
              for (i=0; i < transformedInput.length-3 ; i+=4) {
                transformedInputView +=  transformedInput.slice(i,i+4) + "-" ;
                }
              transformedInputView += transformedInput.slice(i);
              }

         if (transformedInput!=inputValue) {
           modelCtrl.$setViewValue(transformedInputView);
           modelCtrl.$render();
         }

         return transformedInput;
       });
     }
   };
});



var waittemplate = '<center><div class="spinner"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div></center>';


app.config( [
    '$compileProvider','$sceProvider',
    function( $compileProvider, $sceProvider)
    {
        $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|tel|sms|mailto):/);
        $sceProvider.enabled(false);
    }
]);

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
        controller: 'PreRegister'
      }).
      when('/register/vk/', {
        templateUrl: '/static/uam-forms/register-vk.html',
        controller: 'RegisterVk'
      }).
      when('/register/sms/', {
        templateUrl: '/static/uam-forms/register-phone.html',
        controller: 'Register'
      }).
      when('/register/call/', {
        templateUrl: '/static/uam-forms/register-phone.html',
        controller: 'Register'
      }).
      when('/register/password/', {
        templateUrl: '/static/uam-forms/register-password.html',
        controller: 'RegisterPassword'
      }).
      when('/status/', {
        templateUrl: '/static/uam-forms/status.html',
        controller: 'Status'
      }).
      when('/check/sms/', {
        templateUrl: '/static/uam-forms/check-sms.html',
        controller: 'Check'
      }).
      when('/check/', {
        template: waittemplate,
        controller: 'Check'
      }).
      when('/wait/sms/', {
        templateUrl: '/static/uam-forms/wait-sms.html',
        controller: 'Check'
      }).
      when('/wait/call/', {
        templateUrl: '/static/uam-forms/wait-call.html',
        controller: 'Check'
      }).
      when('/login/', {
        templateUrl: '/static/uam-forms/login.html',
        controller: 'Login'
      }).
      when('/voucher/', {
        templateUrl: '/static/uam-forms/gtc.html'
        ,controller: 'VoucherGTC'
      }).
      when('/no-reg/', {
        templateUrl: '/static/uam-forms/no-reg.html'
      }).
      otherwise({
        redirectTo: '/status/'
      });
  }]);

app.controller('PreRegister',  ['$rootScope','$resource','$cookies','$location','$window',
    function ( $scope, $resource, $cookies ,$location,$window){

//  если всего один метод - редиректнуть на него, если несколько - показываем кнопки.

    var c=0;
    var r=false;

    if ($scope.config.external) {
      c++;
      r=false;
    }

    if ($scope.config.callrecieve) {
      r='/register/call/'
      c++;
      $scope.config.call = true;
    }

    if ($scope.config.nosms || $scope.config.smsrecieve || $scope.config.smssend) {
      r='/register/sms/';
      c++;
      $scope.config.sms = true;
    }
    if ($scope.config.password) {
      r='/register/password/';
      c++;
    }
    if ($scope.config.vk) {
      r='/register/vk/';
      c++;
    }
    if (c==1 && r) {
      $location.path(r);
    }

    if (c==0) {
      $location.path('/no-reg/');
    }


    }]);



app.controller('RegisterPassword',  ['$rootScope','$resource','$cookies','$location','$window',
    function ( $scope, $resource, $cookies ,$location,$window){

    $scope.register = function(form) {
                        $location.search('password', form.password.$modelValue);
                        $location.search('username', form.username.$modelValue);
                        $location.path('/login/');
    }

    }]);



app.controller('RegisterVk',  ['$rootScope','$resource','$cookies','$location','$window',
    function ( $scope, $resource, $cookies ,$location,$window){

/*
function sample(arr){
  return arr[Math.floor(Math.random()*arr.length)];
}


onclick="VK.Auth.login(authInfo);"



function authInfo(response) {
  if (response.session) {
    $('#vk_login').hide();
    if (window.hs_config.post) {
        $('#vk_post').show();
    } else {
        CanLogin();
    }

  } else {
    // no auth
  }
}


CanLogin = function(){



};


$scope.register = function(){




VK.Api.call('wall.post', $scope.config.post , function(r) {
  console.log(r);
  if(r.response && r.response['post_id']) {
    CanLogin();
  }
});

}
*/

var script = document.createElement('script');
script.type = 'text/javascript';
script.src = "//vk.com/js/api/openapi.js";
document.body.appendChild(script);

$scope.vk = false;

function register(vk){
        console.log(vk)

        var mac = $location.$$search.mac || $cookies.get('mac');
        var called = $location.$$search.called || $cookies.get('called');

$resource('/register/vk').save(
                    {vk:vk.session.user, mac: mac, profile:called},
                function(response) {
                    console.log(response)
                    if (response.checked) {
                        $location.search('password', response.password);
                        $location.search('username', response.username);
                        $location.path('/login/');
                    }

                }, function(error) {
                    $window.alert('Не сработало...Может Интернет сломался.');
                    $location.path('/register/');
                })

}

$scope.vk_post = function(){

	VK.Api.call('wall.post', $scope.config.post , function(r) {
	  console.log(r);
	  if(r.response && r.response['post_id']) {
	    var vk=$scope.vk;
	    vk.session.user.post_id = r.response['post_id'];
	    register(vk);
	  }
	});

}

$scope.vk_login = function(){

if ($scope.config.vk_message) {
        $scope.config.post = {
          "message":$scope.config.vk_message,
          "attachments":$scope.config.vk_attachments,
          "place_id": $scope.config.vk_place_id
          }
 		}

 function authInfo(response){
 	if (response.session) {
 		$scope.vk = response;
 		register(response);
 		if ($scope.config.vk_message) {
      $scope.post = true;
 		}
 	} else {

 		$scope.error = "Авторизация не удалась"

 	}
    $scope.$apply();
 	}

 VK.init({
    apiId: $scope.config.vk_appid
  });
  VK.Auth.login(authInfo);

}


    }]);


app.controller('Register',  ['$rootScope','$resource','$cookies','$location','$window',
    function ( $scope, $resource, $cookies ,$location,$window){
        var mac = $location.$$search.mac || $cookies.get('mac');
        var called = $location.$$search.called || $cookies.get('called');

        var method = 'sms'

        if ( $location.path() == '/register/call/' )

        method = 'call'

        $scope.register = function(form) {
            console.log(form);
            if (form.$valid) {
                $resource('/register/phone').save(

                    {phone:form.phone.$modelValue, mac: mac, profile:called, method: method},

                function(response) {
                    console.log(response)
                    console.log(response.username)
                    console.log(response.password)

                    $scope.device = response;
                    $location.search('device', response._id.$oid);
                    $cookies.put('device', response._id.$oid);
                    $cookies.put('username', response.username);
                    if (response.checked) {
                        $location.search('password', response.password);
                        $location.search('username', response.username);
                        $location.path('/login/');
                        }
                    else if (response.call_waited)
                        $location.path('/wait/call/')
                    else if (response.sms_sent)
                        $location.path('/check/sms/')
                    else if (response.sms_waited)
                        $location.path('/wait/sms/')
                    else $location.path('/no-reg/')

                },
                function(error) {
                    $window.alert('Не сработало...');
                    //window.location.replace('/register/');
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

app.controller('VoucherGTC',  ['$scope','$resource','$cookies','$location','$http',
    function ( $scope, $resource, $cookies ,$location,$http){
      $scope.username = $location.$$search.username|| $cookies.get('username');
      var oid = $location.$$search.device || $cookies.get('device');

      $scope.gtc = ""
      $scope.wrongcode = false

      var ischilli = $cookies.get('uamip');
      if (ischilli)
            var chilli = 'http://'+$cookies.get('uamip')+':'+$cookies.get('uamport') +'/json/';

      function onlogoff(resp) {
        console.log(resp)
        $location.path('/check/')
      }


      function logoff() {
          if (ischilli)
            $resource(chilli+'logoff',
                {
                },
                {get:{ method: 'JSONP',jsonpCallbackParam:'callback'}}
            ).get(onlogoff)
          else
            $resource($cookies.get('linklogout'),
                {
                    target:'jsonp',
                },
                {get:{ method: 'JSONP',jsonpCallbackParam:'var'}}).get(onlogoff)
      }


      function onconfirm(resp) {
          console.log(resp)
          if (resp.error) {$scope.wrongcode = true} else {
            $scope.wrongcode = false
            logoff()
            }
      }

      $scope.logoff = logoff;
      $scope.confirm = function(form){
          $resource('/billing/voucher').save(
                    {

        'voucher' : $scope.gtc,
        'callee': $cookies.get('called'),
        'nas': $cookies.get('nasid'),
        'device' : oid,
        'username': $scope.username
                    },
                onconfirm
      )
   }


    }]);


app.controller('Login',  ['$window','$resource','$cookies','$location','$http','$rootScope',
    function ( $window, $resource, $cookies ,$location, $http, $scope ){
        var username = $location.$$search.username ;
        var password = $location.$$search.password;
        var ischilli = $cookies.get('uamip');
        if (ischilli)
            var chilli = 'http://'+$cookies.get('uamip')+':'+$cookies.get('uamport') +'/json/';

        function onerror(error){
            console.log('login failed');
            console.log(error)
            if ($cookies.get('linklogout') ) {
              $window.location.href=$cookies.get('linklogout') ;
            } else {
              $location.path('/status/')
            }
        }

        function onlogin(response) {

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

        setTimeout(function(){
          console.log("originalURL timed out")
          //$location.path('/status/')
          window.location.href='/uam/status/'
          }, 3000); //generate_204 не закрывает окно

        }

        function onchillistatus(response) {

            console.log(response)

            var challenge = hex2bin(response.challenge);
            var chapid = '\x00';

            var charpassw = hexMD5(chapid + password + challenge);

            console.log(hex2bin(charpassw));
            console.log(password);


            $resource(chilli+'logon',
                {
                    username:username,
                    response:charpassw,
                },
                {get:{ method: 'JSONP',jsonpCallbackParam:'callback'}}
            ).get(onlogin);
            if (response.redir.logoutURL) $cookies.put('linklogout', response.redir.logoutURL);
        }

        function onmikrotikstatus(response){
                var dst = $cookies.get('linkorig') || "/uam/status/";

                if (response.challenge) {
                  var charpassw = hexMD5(response.chapid + password + response.challenge);
                } else {
                  var charpassw = password;
                }
                $resource($cookies.get('linklogin'),
                {
                    target:'jsonp',
                    dst:dst,
                    username:username,
                    password:charpassw,
                },
                {get:{ method: 'JSONP',jsonpCallbackParam:'var'}}).get(onlogin)
                if (response.redir.logoutURL) $cookies.put('linklogout', response.redir.logoutURL);
        }

        function login(){
              console.log(1)
              if(ischilli) {
                  //chilli
                  $resource(chilli+'status', { },
                  {get:{ method: 'JSONP',jsonpCallbackParam:'callback'}}
                  ).get(onchillistatus,onerror)
              } else {
                  //mikrotik
                  console.log(2)
                  $resource($cookies.get('linklogin'),
                  {
                      target:'jsonp',
                  },
                  {get:{ method: 'JSONP',jsonpCallbackParam:'var'}}).get(onmikrotikstatus,onerror)
                  console.log(3)
              }

        }

        $scope.login = login;

        if ($scope.config.loginbtn) {
        } else {
          if (username && password) {
            login()
          } else {
            onerror({})
          }
        }

}]);



app.controller('Check',  ['$rootScope','$resource','$cookies','$location', '$window','$interval',
    function ( $scope, $resource, $cookies ,$location,$window,$interval){
        $scope.wrongcode = false;
        $scope.code = null;
        var oid = $location.$$search.device || $cookies.get('device');

        function prelogin(response){
            $scope.device=response;
            console.log(response);
            $scope.device = response;
            if (response.password) {
                $interval.cancel($scope.checker)
                $location.search('password', response.password);
                $location.search('username', response.username);
                $location.path('/login/')
            }
        }

        function confirm_cb(response){
          prelogin(response);
          if (!response.password) {
                  $scope.wrongcode = true;
                  $scope.code = null;
            }
        }

        function onerror(error) {
                        $window.alert('Не сработало...Попробуйте с начала. Похоже Сервер Вас не помнит.');
                        $window.location.href=$cookies.get('linklogout') || 'http://ya.ru/'  ;
                }

        if ($scope.checker) {
            $interval.cancel($scope.checker)
        }
        function getdevice(){
                 $resource('/device/:oid').get({
                        'oid': oid
                    },
                    prelogin,onerror
                 )
            }

        $scope.checker = $interval(
            getdevice, 1000)

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
                confirm_cb,onerror

            );


        }}

    }]);

app.controller('Status',  ['$rootScope','$resource','$cookies',
    function ( $scope, $resource, $cookies ){

    var ischilli = $cookies.get('uamip');

    function onstatus(response){
        $scope.status = response;
        var logoutURL = response.redir.logoutURL ||$cookies.get('linklogout');
        $scope.logoutURL = logoutURL.replace('/jsonp/','/');
    }

    if(ischilli) {
        //chilli
        var chilli = 'http://'+$cookies.get('uamip')+':'+$cookies.get('uamport') +'/json/';
        $resource(chilli+'status', { },
        {get:{ method: 'JSONP',jsonpCallbackParam:'callback'}}
        ).get(onstatus)
    } else {
        //mikrotik

        $resource($cookies.get('linklogin').replace('login','status'),
        {
            target:'jsonp'
        },
        {get:{ method: 'JSONP',jsonpCallbackParam:'var'}}).get(onstatus)

    }

    }]);


app.run(['$route','$location','$rootScope','$resource','$cookies','$interval',
 function ($route,$location,$scope,$resource,$cookies,$interval) {
    console.log($location);
    console.log($route);

    $scope.$location = $location;
    $scope.$cookies = $cookies;


    $scope.onlocation = function(location) {
      return ($location.$$path.indexOf(location) == 0)
    }


    $scope.countdown = function() {
      var start = $scope.counter;
      $interval( function(){ $scope.counter--}, 1000, start)
    }


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

    if ( $location.$$search.nasid && ! $location.$$search.called )
        $cookies.put('called', $location.$$search.nasid);

    console.log($cookies.getAll())

    $resource('/config/uam/:called.json').get(
    {called:$cookies.get('called')},
    function(response){
        $scope.config = response
    },
    function(error){
        $scope.config ={
            password_auth:true,
            theme:"default"
            }
    }
    )


}
]);


app.filter('EmbedUrl', function ($sce) {
    return function(uri,ext) {
      return $sce.trustAsResourceUrl(uri + ext);
    };
  });
