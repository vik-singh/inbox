from datetime import datetime
from autobahn.twisted.wamp import ApplicationSession

from twisted.internet.defer import inlineCallbacks
from twisted.enterprise import adbapi

from twistar.registry import Registry
from twistar.dbobject import DBObject

import os


# i'm sure there is a better place to put this - contructor, initializer, etc.
filename = os.path.dirname(os.path.abspath(__file__)) + "/inbox.sqlite"
Registry.DBPOOL = adbapi.ConnectionPool("sqlite3", filename, check_same_thread=False)

# wasn't sure on Python code organization or naming conventions - using camelCased function names and I'd usually do one class per file
# following are twistar async ORM objects - fields pass through from db table so no need for each field definition
class User(DBObject):
    pass

class Message(DBObject):
    pass

class AppSession(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details):
        #auth user by name or create a new user
        def authUser(name):
            def returnUserId(user):
                return user.id

            return User.findOrCreate(name = name).addCallback(returnUserId)

        try:
           yield self.register(authUser, 'com.vik.authUser')
        except Exception as e:
           print("could not register authUser procedure: {0}".format(e))

        #get a list of users for selectlist on client end
        def getUsers():
            def formatUsers(users):
                formatted_users = []
                for user in users:
                    formatted_users.append({
                        "id": user.id,
                        "name": user.name
                    })
                return formatted_users

            return User.all().addCallback(formatUsers)

        try:
            yield self.register(getUsers, 'com.vik.getUsers')
        except Exception as e:
            print("could not register getUsers procedure: {0}".format(e))

        # send a message to a user
        def sendMessage(subject, body, sender_id, receiver_id):
            now = datetime.now()

            Timestamp = Registry.getDBAPIClass("Timestamp")
            # save message to datastore
            message = Message(
                subject=subject,
                body=body,
                sender_id=sender_id,
                receiver_id=receiver_id,
                sent_at=Timestamp(now.year, now.month, now.day, now.hour, now.minute, now.second)
            )
            message.save()

            # js client is subscribed to topic with name inbox_user_<user_id> so it will publish to their list
            self.publish('com.vik.inbox_user_' + str(message.receiver_id), formatMessage(message))

        try:
            yield self.register(sendMessage, 'com.vik.sendMessage')
        except Exception as e:
            print("could not register sendMessage procedure: {0}".format(e))



        # get a list of a messages for a given user - RPC to initially populate message list for a user
        def getMessages(user_id):
            def formatMessages(messages):
                formatted_messages = []
                for message in messages:
                    # hack to make datetime json serializable for now - better solution would be to make Autobahn support custom json encoders
                    formatted_messages.append(formatMessage(message))

                return formatted_messages

            return Message.findBy(receiver_id = user_id).addCallback(formatMessages)

        try:
            yield self.register(getMessages, 'com.vik.getMessages')
        except Exception as e:
            print("could not register getMessages procedure: {0}".format(e))


        # hacked to ensure datetime json serialized properly
        def formatMessage(message):
            return {
                "id": message.id,
                "subject": message.subject,
                "body": message.body,
                "sent_at": str(message.sent_at),
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id
            }