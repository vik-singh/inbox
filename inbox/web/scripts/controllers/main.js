'use strict';

angular.module('inboxApp')
  .controller('MainCtrl', function ($scope, $wamp, messages, $rootScope, users) {
        this.users = users;
        this.messages = messages;
        var that = this;

        function onMessageReceived(args, kwargs) {
            var message = args[0];
            $scope.$apply(function() {
                that.messages.push(message);
            })
        }

        // subscribe to receive messages published to my user_id / inbox
        $wamp.subscribe('com.vik.inbox_user_' + $rootScope.currentUser.id, onMessageReceived);

        this.sendMessage = function (message) {
            $wamp.call('com.vik.sendMessage', ["", message.body, $rootScope.currentUser.id, message.to]).then(
                function (res) {
                    that.new_message = {};
                }
            );
        };

        this.resolveUser = function(user_id) {
            for (var i = 0; i < this.users.length; i++) {
                if (user_id === this.users[i].id) {
                    return this.users[i].name;
                }
            }
            return "Unknown";
        }
    });