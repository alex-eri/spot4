'use strict';

var app = angular.module('hotspot',['ngResource','ngAnimate'])

.run(['$http','$rootScope',
    function ($http,$rootScope) {

        function onAPI(APIURL){
            $http.get(APIURL+'/salt').then(
                function(response) {
                    app.SALT = response.data.salt;
                }, function(error){
                    $rootScope.error = "Сервер не отвечает, попробуйте позже";
                    $rootScope.stage = 'error';
                });
        };


        $http.get('config.json').then( function(response) {
            console.log(response.data);
            app.APIURL = response.data.api;
            document.title = response.data.title || 'Spot 4 hotspot';
            $rootScope.config = response.data ;
            onAPI(app.APIURL)
            }
         ,function(error) { alert('Не найду локальный кофиг/ Хотспот сломался') });

    }
]);

window.app = app;


app.factory('User', ['$resource','$http',
    function($resource,$http) {
      return function (api_url) { return $resource( api_url + '/device/:phonehash/:mac', {phonehash:'@phonehash',mac:'@mac'}); }
    }]);



app.factory('Client', ['$resource',
    function($resource) {
      return $resource('/json/login.html');
    }]);

app.factory('Status', ['$resource',
    function($resource) {
      return $resource('/json/status.html');
    }]);


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



function hash(salt,data) {
    return hexMD5(salt+data);
}


app.controller('login',  ['User','Client','$rootScope','$http','$timeout',
    function (User, Client, $rootScope, $http, $timeout ){
        var self = this;
        $rootScope.forms = 'partials/login.form.html'
        $rootScope.stage = 'mac';
        var creds = {};
        $rootScope.sms = {};
        $rootScope.client = {};
        $rootScope.phone = "";
        var phonehash = "";

        Client.get(
            function (data) {
                    $rootScope.client = data;
                    if (data.logged_in == 'yes') {
                        $rootScope.stage = 'status';
                    } else {
                        $rootScope.stage = 'form';
                    }
                console.log(data);
            }
        )


        function user_wait(){

                User(app.APIURL).get(
                    {
                        phonehash: phonehash ,
                        mac:$rootScope.client.mac
                    },
                    function(data){
                        if (data.response.password) {
                        $rootScope.stage = 'login';
                        creds.username = data.response.username;
                        creds.password = data.response.password;
                        hotspot_login()

                        } else {
                        $rootScope.stage = 'cod';
                        $rootScope.sms.waited = data.response.sms_waited;
                        $rootScope.sms.callie = data.response.sms_callie;
                        $timeout(user_wait,1000);//TODO port to $interval
                        }
                        console.log(data);
                    },function(error){
                        $timeout(user_wait,1000);//TODO port to $interval
                    });
        }

        function to_status(){
            $rootScope.stage = 'status'; //не пашет, но вызывается
            $rootScope.$apply();
        }

        function hotspot_login(){
            $http.post($rootScope.client.link_login_only,jQuery.param(creds)).then( function(response) {
                console.log(response)
                var data = response.data
                $rootScope.client = data;
                if (data.logged_in == 'yes') {
                    $rootScope.stage = 'ok';
                    data.link_redirect = data.link_redirect.replace('/json/','/')
                    $timeout(to_status, 10000);
                } else {
                    $rootScope.error = data.error;
                    $rootScope.stage = 'error';
                }
            })
        }

        $rootScope.back_to = function(stage){
            $rootScope.stage = stage;
        }
        $rootScope.register = function(form){
            console.log(form);
            if (form.$valid) {
                console.log(app.APIURL);
                console.log(app.SALT);
                console.log($rootScope.phone);
                $rootScope.stage = 'reg';

                phonehash = hash(app.SALT,$rootScope.phone);
                console.log(phonehash)
                user_wait();
                $timeout(function(){$rootScope.waiting=true},5000);
            }
        }


    } ]

);

app.controller('status',  ['Status','$rootScope','$timeout',
    function (Status, $rootScope, $timeout) {

        $rootScope.client = {};
        function update(){
        Status.get(
            function (data) {
                console.log($rootScope);
                $rootScope.client = data;
                if (data.logged_in == 'yes') {
                    $timeout(update, 3000);//TODO port to $interval
                } else {
                    $rootScope.stage = 'form';
                }

                console.log(data);
            },
            function(error){ $timeout(update, 3000); } //TODO port to $interval
        );

        }


        update();

    }
    ]);
