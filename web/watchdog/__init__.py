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
import time

from flask import Flask, request, render_template

app = Flask(__name__)

from flask import jsonify, redirect, url_for
import redis

R = redis.Redis(host='redis')


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/success')
def success():
    data = [[k.decode('utf8'), R.get(k).decode('utf8')] for k in R.keys('success:*')]

    resp = {'data': data}
    return jsonify(resp)


@app.route('/failed')
def failed():
    data = [[k.decode('utf8'), R.get(k).decode('utf8')] for k in R.keys('failed:*')]

    resp = {'data': data}
    return jsonify(resp)


@app.route('/status')
def status():
    key = request.args.get('key')
    if key:
        value = R.get(key)
        if value:
            value = value.decode('utf8')
        data = [[key, value]]
    else:
        def factory(k):
            kk = k.decode('utf8')
            value = float(R.get(k).decode('utf8'))
            tl = int(value - time.time())
            return kk, int(value), tl

        data = [factory(k) for k in R.keys('experiment:*')]

    resp = {'data': data}
    return jsonify(resp)


@app.route('/manage')
def manage():
    return render_template('manage.html')


@app.route('/testing_experiment_start', methods=['POST'])
def testing_experiment_start():
    if request.method == 'POST':
        key = request.form.get('key')
        time_to_expire_s = int(request.form.get('expire'))
        success = _experiment_start(key, time_to_expire_s)
        #return jsonify({'registered': {'key': key,
        #                               'time': success}})
        return redirect(url_for('manage'))


@app.route('/testing_run_start', methods=['POST'])
def testing_run_start():
    if request.method == 'POST':
        key = request.form.get('key')
        time_to_expire_s = int(request.form.get('expire'))
        success = _experiment_start(key, time_to_expire_s)
        #return jsonify({'registered': {'key': key,
        #                               'time': success}})
        return redirect(url_for('manage'))


@app.route('/testing_experiment_end', methods=['POST'])
def testing_experiment_end():
    if request.method == 'POST':
        key = request.form.get('key')
        success = _experiment_end(key)
        return redirect(url_for('manage'))


def _experiment_start(key, expire):
    key = f'experiment:{key}'
    expire_at = time.time() + expire
    R.set(key, str(expire_at))
    return R.get(key).decode('utf8')


def _experiment_end(key):
    key = f'experiment:{key}'
    skey = f'success:{key}'
    R.delete(key)
    R.set(skey, str(time.time()))
    return True


@app.route('/run_start')
def run_start():
    pass


@app.route('/run_end')
def run_end():
    pass
# ============= EOF =============================================
