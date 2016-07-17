

(function(app) {
  app.Login =
    ng.core.Component({
      selector: 'my-app',
      templateUrl: '/templates/login.html'
    })
    .Class({
      constructor: function() {}
    });

  app.LoginForms =
    ng.core.Component({
      selector: 'forms',
      templateUrl: '/partials/login.html'
    })
    .Class({
      constructor: function() {}
    });


  app.User = User;
  function User(id, login, mac, password, sms_waited) {
    this.id = id;
    this.login = login;
    this.mac = mac;
    this.password = password;
    this.sms_waited = sms_waited;
  }

}

)(window.app || (window.app = {}));

