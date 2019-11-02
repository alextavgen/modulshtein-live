from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNOperationType, PNStatusCategory
import random
import midi_interface
import queue
from pubnub.exceptions import PubNubException
import asyncio
import json
import logging

logger = logging.getLogger('modulshtein-live')

instruments = dict()
CHANNEL_START = 10
CHANNEL_END = 12
pnconfig = PNConfiguration()
pnconfig.subscribe_key = "sub-c-6a7e619c-f3fd-11e9-ad72-8e6732c0d56b"
pnconfig.publish_key = "pub-c-04e1d58f-37d0-42ae-9db2-088a4753a892"
pnconfig.ssl = False

pubnub = PubNub(pnconfig)

phones_dict = dict()

q = queue.Queue()

class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):

        # The status object returned is always related to subscribe but could contain
        # information about subscribe, heartbeat, or errors
        # use the operationType to switch on different options
        if status.operation == PNOperationType.PNSubscribeOperation \
                or status.operation == PNOperationType.PNUnsubscribeOperation:
            if status.category == PNStatusCategory.PNConnectedCategory:
                pass
                # This is expected for a subscribe, this means there is no error or issue whatsoever
            elif status.category == PNStatusCategory.PNReconnectedCategory:
                pass
                # This usually occurs if subscribe temporarily fails but reconnects. This means
                # there was an error but there is no longer any issue
            elif status.category == PNStatusCategory.PNDisconnectedCategory:
                pass
                # This is the expected category for an unsubscribe. This means there
                # was no error in unsubscribing from everything
            elif status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                pass
                # This is usually an issue with the internet connection, this is an error, handle
                # appropriately retry will be called automatically
            elif status.category == PNStatusCategory.PNAccessDeniedCategory:
                pass
                # This means that PAM does not allow this client to subscribe to this
                # channel and channel group configuration. This is another explicit error
            else:
                pass
                # This is usually an issue with the internet connection, this is an error, handle appropriately
                # retry will be called automatically
        elif status.operation == PNOperationType.PNSubscribeOperation:
            # Heartbeat operations can in fact have errors, so it is important to check first for an error.
            # For more information on how to configure heartbeat notifications through the status
            # PNObjectEventListener callback, consult http://www.pubnub.com/docs/python/api-reference-configuration#configuration
            if status.is_error():
                pass
                # There was an error with the heartbeat operation, handle here
            else:
                pass
                # Heartbeat operation was successful
        else:
            pass
            # Encountered unknown status type

    def presence(self, pubnub, presence):
        pass  # handle incoming presence data


    def message(self, pubnub, message):
        print(message.message)
        if 'command' in message.message:
            if message.message['command'] == 'INSTRUMENTS':
                print('Received command INSTRUMENTS')
                give_instruments_info()
        else:
            print(message.message)
            if message.message['sender'] not in phones_dict and 'command' not in message.message:
                sender = message.message['sender']
                phones_dict[sender] = message.message['instrument']
                instruments[message.message['instrument']] = False
                print('Send instruments ')
                give_instruments_info()
            midi_interface.handle_message(message, 9 + message.message['instrument'], q)


    def signal(self, pubnub, signal):
        pass # handle incoming signals


def give_instruments_info():
    try:
        global instruments
        print('Preparing to send')
        msg = instruments
        print(msg)
        envelope = pubnub.publish().channel("instruments_channel").message(msg).sync()
        print("publish timetoken: %d" % envelope.result.timetoken)
        print(instruments)
    except PubNubException as e:
        print(e)
        pass


pubnub.add_listener(MySubscribeCallback())
#pubnub.subscribe().channels('geo_channel').execute()
#pubnub.subscribe().channels('motion_channel').execute()
pubnub.subscribe().channels('orientation_channel').execute()



async def periodic():
    while True:
        print('Scheduled task async')
        midi_interface.clear_queue(q)
        await asyncio.sleep(1)

def stop():
    task.cancel()

loop = asyncio.get_event_loop()
loop.call_later(60000, stop)
task = loop.create_task(periodic())

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass