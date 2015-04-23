'use strict';

angular
    .module('inboxApp', [
        'ngRoute',
        'vxWamp',
        'angularMoment'
    ])
    .config(function ($routeProvider, $wampProvider) {

        $wampProvider.init({
            url: 'ws://127.0.0.1:8080/ws',
            realm: 'realm1'
        });

        $routeProvider
            .when('/:username', {
                templateUrl: 'views/main.html',
                controller: 'MainCtrl as inbox',
                resolve: {
                    messages: ['$wamp', '$rootScope', '$q', '$route', function ($wamp, $rootScope, $q, $route) {
                        var deferred = $q.defer(),
                            username = $route.current.params.username;

                        $wamp.call('com.vik.authUser', [username]).then(
                            function (res) {
                                $rootScope.currentUser = {
                                    "id": res,
                                    "name": username
                                };

                                $wamp.call('com.vik.getMessages', [$rootScope.currentUser.id]).then(//since no auth in app - we're simply using rootScope to hold current user
                                    function (res) {
                                        deferred.resolve(res);
                                    }
                                );
                            }
                        );
                        return deferred.promise;
                    }],
                    users: ['$wamp', '$rootScope', '$q', function ($wamp, $rootScope, $q) {
                        var deferred = $q.defer();

                        $wamp.call('com.vik.getUsers', []).then(
                            function (res) {
                                deferred.resolve(res);
                            }
                        );
                        return deferred.promise;
                    }]
                }
            })
            .otherwise({
                redirectTo: '/Vik'
            });
    })
    .run(function ($wamp, $rootScope) {
        $wamp.open();
        $rootScope.currentUser = {};
    });