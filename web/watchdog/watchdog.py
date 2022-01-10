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
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Emailer:
    server_host = None
    server_port = None
    server_username = None
    server_password = None

    def debug(self, msg):
        self.log('DEBUG', msg)

    def warning(self, msg):
        self.log('WARNING', msg)

    def info(self, msg):
        self.log('INFO', msg)

    def log(self, tag, msg):
        print(f'[{tag}] -- {msg}')

    def config_from_env(self):
        self.server_host = os.environ.get('EMAILER_HOST')
        self.server_port = os.environ.get('EMAILER_PORT')
        self.server_username = os.environ.get('EMAILER_USERNAME')
        self.server_password = os.environ.get('EMAILER_PASSWORD')

    def connect(self, warn=True, test=False):
        if not self.server_host:
            self.config_from_env()

        try:
            server = smtplib.SMTP(self.server_host, self.server_port, timeout=5)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.server_username, self.server_password)
            if test:
                server.quit()
                return True
        except (smtplib.SMTPServerDisconnected, BaseException) as e:
            self.debug(
                "SMTPServer connection err: {}. "
                "host={}, user={}, port={}".format(
                    e, self.server_host, self.server_username, self.server_port
                )
            )
            if warn:
                self.warning("SMTPServer not properly configured")
            server = None

        return server

    def send(self, addrs, sub, msg, paths=None):
        self.info("Send email. addrs: {}".format(addrs, sub))

        if "," in addrs:
            addrs = ",".split(addrs)

        st = time.time()
        for i in range(2):
            server = self.connect()
            if server is not None:
                break
            self.debug("doing email connection retry {}".format(i))
            time.sleep(1)
        self.debug("server connection duration={}".format(time.time() - st))

        if server:
            if not isinstance(addrs, (list, tuple)):
                addrs = [addrs]

            msg = self._message_factory(addrs, sub, msg, paths)
            try:
                st = time.time()
                server.sendmail(self.sender, addrs, msg.as_string())
                server.quit()
                self.debug("server.sendmail duration={}".format(time.time() - st))
                return True
            except BaseException as e:
                self.warning("Failed sending mail. {}".format(e))
        else:
            self.warning("Failed connecting to server")

    def _message_factory(self, addrs, sub, txt, paths):
        msg = MIMEMultipart()
        msg["From"] = f'{self.server_username}@gmail.com'
        msg["To"] = ",".join(addrs)
        msg["Subject"] = sub
        msg.attach(MIMEText(txt))

        if paths:
            for p in paths:
                name = os.path.basename(p)
                with open(p, "rb") as rfile:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(rfile.read())
                    part["Content-Disposition"] = 'attachment; filename="{}"'.format(
                        name
                    )
                    msg.attach(part)
        return msg


class Notifier:
    def __init__(self):
        self._emailer = Emailer()

    def notify(self, k, context):
        print(f'Notify, k={k}, context={context}')
        # send email to configured users

        addrs = self._get_addresses()
        sub, msg = self._make_message(k, context)
        self._emailer.send(addrs, sub, msg)

    def _get_addresses(self):
        addrs = os.environ.get('EMAILER_ADDRESSES', '')
        return addrs.split(',')

    def _make_message(self, k, context):
        return f'Experiment {k} Failed', f"Experiment {k} failed to respond to the watchdog. Context={context}"


class Monitor:
    _active = None
    _poll_thread = None

    def __init__(self):
        self._notifier = Notifier()

    def start(self):
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
                    r.set(f'failed:{k.decode("utf8")}', ct)
                    self._notifier.notify(k, {'ct': ct, 'expires_at': expires_at})

            time.sleep(poll_delay)


monitor = Monitor()
monitor.start()
# ============= EOF =============================================
