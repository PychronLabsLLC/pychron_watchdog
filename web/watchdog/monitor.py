# ===============================================================================
# Copyright 2022 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from threading import Event, Thread
import time
import smtplib
import redis
import os

# from watchdog.smtp_client import SMTPClient
from watchdog.twilio_client import TwilioClient


class Notifier:
    def __init__(self):
        # self._sender = SMTPClient()
        self._sender = TwilioClient()

    def start(self):
        # send a test notification to indicate the watchdog has started
        addrs = self._get_addresses([])
        sub = 'WatchDog Started'
        msg = 'This is a test message to indicate the Pychron WatchDog has started'
        self._sender.sendmail(addrs, sub, msg)

    def notify(self, k, addresses, context):
        print(f'Notify, k={k}, context={context}')
        # send email to configured users

        addrs = self._get_addresses(addresses)
        sub, msg = self._make_message(k, context)
        self._sender.sendmail(addrs, sub, msg)

    def _get_addresses(self, addresses):
        addrs = os.environ.get('EMAILER_ADDRESSES', '')
        addrs = addrs.split(',')
        if addresses:
            addrs.extend(addresses.split(','))
        return addrs

    def _make_message(self, k, context):
        k = k.decode('utf8')
        return f"Experiment {k} Hard Crash'", f"""Experiment {k} failed to respond to the watchdog. 
            
Context={context}"""


class Monitor:
    _active = None
    _poll_thread = None

    def __init__(self):
        self._notifier = Notifier()

    def start(self):
        self._notifier.start()
        self._active = Event()
        self._active.set()

        self._poll_thread = Thread(target=self._poll)
        self._poll_thread.setDaemon(1)
        self._poll_thread.start()

    def _poll(self):
        print(f'{id(self)} starting poll')
        poll_delay = 2
        r = redis.Redis(host='redis')
        while self._active.is_set():
            for k in r.keys('experiment:*'):
                expires_at = r.get(k)
                ct = time.time()
                if ct > float(expires_at):
                    print(f'!!!!!! {k} expired.  {ct} {expires_at}')

                    r.delete(k)
                    kk = k.decode('utf8')
                    r.set(f'failed:{kk}', ct)

                    emk = f'email_addresses:{kk}'
                    addresses = r.get(emk)
                    r.delete(emk)

                    evk = f'event:{kk}'
                    evt = r.get(evk)
                    r.delete(evk)

                    self._notifier.notify(k, addresses, {'ct': ct,
                                                         'event': evt,
                                                         'expires_at': expires_at})

            time.sleep(poll_delay)


monitor = Monitor()
# ============= EOF =============================================
