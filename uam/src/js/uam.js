'use strict';

var app = angular.module('uam',['ngRoute', 'ngResource'])

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
        template: '<center><div class="spinner"><div class="bounce1"></div><div class="bounce2"></div><div class="bounce3"></div></div></center>'
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
        templateUrl: '/static/uam-forms/sms.html',
        controller: 'Check'
      })
      /*.
      otherwise({
        redirectTo: '/register/'
      })*/;
  }]);


app.controller('Register',  ['$scope','$resource','$timeout','$location',
    function ( $scope, $resource, $timeout ,$location){
        $scope.register = function(form) {
            console.log(form);
            if (form.$valid) {
                $location.path('/wait/');
                $resource('/register/').save(

                    {phone:form.phone.$modelValue, mac: $location.$$search.mac},

                function(response) {
                    console.log(response);
                    console.log($location);
                    $location.search('device', response.id.$oid);
                    $location.path('/check/sms/');
                },
                function(error) {
                    alert('Не сработало...Может Интернет сломался.');
                    $location.path('/register/');
                });
            }
        }


    }]);

app.controller('Check',  ['$scope','$resource','$timeout','$location',
    function ( $scope, $resource, $timeout ,$location){
        $scope.wrongcode = false;
        $scope.code = null;
        $scope.confirm = function(form) {if (form.$valid) {
        var oid = $location.search().device;
        console.log(form);
        //$location.path('/wait/');
        $resource('/device/:oid').save(
            {
                'oid': oid
            },
            {
                'oid': oid,
                'sms_sended': form.code.$viewValue
            },
            function(response) {
                    console.log(response);
                    if (response.checked) {

                    } else {
                        $scope.wrongcode = true;
                        $scope.code = null;
                        $location.path('/check/sms/');
                    }
                    },
            function(error) {
                    alert('Не сработало...Похоже Сервер сошел с ума.');
                    $location.path('/register/');
            }
        );

        }}

    }]);

app.controller('Status',  ['$rootScope','$http','$timeout',
    function ( $scope, $http, $timeout ){
    }]);


app.run(['$route','$location','$rootScope','$resource', function ($route,$location,$scope,$resource) {
    console.log($location);
    console.log($route);

    $resource('/uam/config/:nasid.json').get(
    {nasid:$location.$$search.nasid},
    function(response){
        $scope.config = response
    },
    function(error){
        $scope.config ={
            send_sms:false,
            password_auth:true,
            theme:"default"
            }
    }
    )


}
]);

