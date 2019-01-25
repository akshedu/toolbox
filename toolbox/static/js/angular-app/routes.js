var toolboxApp;

toolboxApp = angular.module('toolboxApp');

toolboxApp.config([
  '$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/');

    return $stateProvider.
      state('home', {
        url: '/',
        templateUrl: 'home.html',
        controller: 'homeController',
        activetab: ''
      });
  }
]);
