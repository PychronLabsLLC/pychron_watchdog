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

import redis


class Notifier:
    def notify(self, k, context):
        print(f'Notify, k={k}, context={context}')
        # send email to configured users

        addrs = self._get_addresses()
        msg = self._make_message(k, context)
        self._send_email(addrs, msg)

    def _get_addresses(self):
        addrs = []
        return addrs

    def _make_message(self, k, context):
        return ''

    def _send_email(self, addrs, msg):
        pass


class Monitor:
    _active = None
    _poll_thread = None

    def __init__(self):
        self._notifier = Notifier()

    def start(self):
        self._active = Event()
        self._active.set()

        self._poll_thread = Thread(target=self._poll)
        self._poll_thread.start()

    def _poll(self):
        print(f'{id(self)} starting poll')
        poll_delay = 5
        r = redis.Redis(host='redis')
        while self._active.is_set():
            for k in r.keys('experiment_*'):
                expires_at = r.get(k)
                ct = time.time()
                if ct > float(expires_at):
                    print(f'!!!!!! {k} expired.  {ct} {expires_at}')
                    self._notifier.notify(k, {'ct': ct, 'expires_at': expires_at})
                    r.delete(k)

            time.sleep(poll_delay)


monitor = Monitor()
monitor.start()
# ============= EOF =============================================
