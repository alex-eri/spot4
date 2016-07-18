'use strict';

var app = angular.module('hotspot',['ngResource','ngAnimate'])

.run(['$http','$rootScope',
    function ($http,$rootScope) {
        $http.get('config.json').then( function(response) {
            console.log(response.data);
            app.APIURL = response.data.api;
            document.title = response.data.title || 'Spot 4 hotspot';
            $rootScope.config = response.data ;
            }
         ,function(error) { alert('не найду локальный кофиг') });
    }
]);

window.app = app;




app.factory('User', ['$resource','$http',
    function($resource,$http) {
      return function (api_url) { return $resource( api_url + '/user/:login/:mac', {login:'@login',mac:'@mac'}); }
    }]);

app.factory('Client', ['$resource',
    function($resource) {
      return $resource('hotspot.json');
    }]);


app.controller('login',  ['User','Client','$scope',
    function (User,Client,$scope){
        var self = this;
        $scope.forms = 'partials/login.html'
        $scope.stage = 'mac';
        $scope.creds = {};
        $scope.sms = {};

        Client.get(
            function (data) {
                $scope.client = data;
                $scope.stage = 'form';
                console.log(data);
            }
        )

        $scope.register = function(form){
            console.log(form);
            if (form.$valid) {
                console.log(app.APIURL);
                console.log($scope.creds);
                $scope.stage = 'reg';
                User(app.APIURL).get(
                    {login:$scope.creds.login, mac:$scope.client.mac},
                    function(data){

                        $scope.stage = 'cod';
                        $scope.sms.waited = data.response.sms_waited;
                        $scope.sms.callie = data.response.sms_callie;
                        console.log(data);
                    });
            }
        }

    } ]

);


