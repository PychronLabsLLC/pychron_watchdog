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

class Client:
    handle = None
    def connect(self):
        self.handle = self._get_handle()
        return self.handle

    def sendmail(self, *args, **kw):
        raise NotImplementedError

    def _get_handle(self):
        raise NotImplementedError

    def debug(self, msg):
        self.log('DEBUG', msg)

    def warning(self, msg):
        self.log('WARNING', msg)

    def info(self, msg):
        self.log('INFO', msg)

    def log(self, tag, msg):
        print(f'[{tag}] -- {msg}')
# ============= EOF =============================================
