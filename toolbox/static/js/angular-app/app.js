var toolboxApp, home;
toolboxApp = angular.module(
  'toolboxApp', [
    'ngResource',
    'templates',
    'ui.router',
    'ui.bootstrap',
    'ngCookies',
    'base64',
    'home'
  ]
)

home = angular.module(
  'home', [
    'homeControllers'
  ]
)
