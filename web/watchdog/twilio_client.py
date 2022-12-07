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
import os

from watchdog.client import Client
from sendgrid import SendGridAPIClient, Mail


class TwilioClient(Client):

    def sendmail(self, addrs, sub, msg):
        sg = self.connect()
        message = Mail(from_email= 'nmgrl4039@gmail.com',
                       to_emails=addrs,
                       subject=sub,
                       plain_text_content=msg
                       )
        response = sg.send(message)
        self.info(response.status_code)
        self.info(response.body)

    def _get_handle(self):
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            return sg
        except Exception as e:
            self.warning(f'get handle exception {e}')
# ============= EOF =============================================
