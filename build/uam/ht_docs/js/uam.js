'use strict';

var app = angular.module('uam',['ngResource'])

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

app.controller('login',  ['$rootScope','$http','$timeout',
    function ( $scope, $http, $timeout ){
    $scope.forms = 'forms/register.html'
    }]);
