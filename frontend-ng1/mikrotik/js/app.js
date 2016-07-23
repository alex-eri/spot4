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
         ,function(error) { alert('Не найду локальный кофиг/ Хотспот сломался') });
    }
]);

window.app = app;


app.factory('User', ['$resource','$http',
    function($resource,$http) {
      return function (api_url) { return $resource( api_url + '/user/:login/:mac', {login:'@login',mac:'@mac'}); }
    }]);

app.factory('Client', ['$resource',
    function($resource) {
      return $resource('/json/login.html');
    }]);

app.factory('Status', ['$resource',
    function($resource) {
      return $resource('/json/status.html');
    }]);


app.controller('login',  ['User','Client','$scope','$http',
    function (User,Client,$scope,$http){
        var self = this;
        $scope.forms = 'partials/login.form.html'
        $scope.stage = 'mac';
        $scope.creds = {};
        $scope.sms = {};
        $scope.client = {};

        Client.get(
            function (data) {
                $scope.client = data;
                if (data.logged_in == 'yes') {
                    $scope.stage = 'status';
                } else {
                    $scope.stage = 'form';
                }
                console.log(data);
            }
        )


        function user_wait(){
                User(app.APIURL).get(
                    {login:$scope.creds.username, mac:$scope.client.mac},
                    function(data){
                        if (data.response.password) {
                        $scope.stage = 'login';
                        $scope.creds.password = data.response.password;
                        hotspot_login()

                        } else {
                        $scope.stage = 'cod';
                        $scope.sms.waited = data.response.sms_waited;
                        $scope.sms.callie = data.response.sms_callie;
                        setTimeout(user_wait,1000);
                        }
                        console.log(data);
                    },function(error){
                        setTimeout(user_wait,1000);
                    });
        }

        function to_status(){
            $scope.stage = 'status'; //не пашет, но вызывается
            $scope.$apply();
        }

        function hotspot_login(){
            $http.post($scope.client.link_login_only,jQuery.param($scope.creds)).then( function(response) {
                console.log(response)
                var data = response.data
                $scope.client = data;
                if (data.logged_in == 'yes') {
                    $scope.stage = 'ok';
                    data.link_redirect = data.link_redirect.replace('/json/','/')
                    setTimeout(to_status, 10000);
                } else {
                    $scope.error = data.error
                    $scope.stage = 'error';
                }
            })
        }

        $scope.back_to = function(stage){
            $scope.stage = stage;
        }
        $scope.register = function(form){
            console.log(form);
            if (form.$valid) {
                console.log(app.APIURL);
                console.log($scope.creds);
                $scope.stage = 'reg';
                user_wait();
                setTimeout(function(){$scope.waiting=true},5000);
            }
        }


    } ]

);

app.controller('status',  ['Status','$scope','$http',
    function (Status,$scope,$http) {

        $scope.client = {};
        function update(){
        Status.get(
            function (data) {
                $scope.client = data;
                if (data.logged_in == 'yes') {
                    $scope.stage = 'status';
                } else {
                    $scope.stage = 'form';
                }
                console.log(data);
            }
        );
         setTimeout(update,3000);
        }
        update();

    }
    ]);
