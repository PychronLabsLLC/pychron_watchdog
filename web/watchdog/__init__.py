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
import datetime
import time
import redis
from flask import Flask, request, render_template, jsonify, redirect, url_for

app = Flask(__name__)
R = redis.Redis(host='redis')


@app.route('/')
def index():
    return render_template('home.html')


def make_ajax_table(tag, row_factory):
    data = [row_factory(k) for k in R.keys(tag)]

    resp = {'data': data}
    return jsonify(resp)


@app.route('/success')
def success():
    def row_factory(k):
        v = R.get(k)
        v = datetime.datetime.fromtimestamp(float(v))
        return k.decode('utf8'), v

    return make_ajax_table('success:*', row_factory)


@app.route('/failed')
def failed():
    def row_factory(k):
        v = R.get(k)
        v = datetime.datetime.fromtimestamp(float(v))
        return k.decode('utf8'), v

    return make_ajax_table('failed:*', row_factory)


@app.route('/status')
def status():
    def row_factory(k):
        kk = k.decode('utf8')
        value = float(R.get(k))
        ts = datetime.datetime.fromtimestamp(value)
        tl = int(value - time.time())
        return kk, ts, tl

    return make_ajax_table('experiment:*', row_factory)


@app.route('/manage')
def manage():
    return render_template('manage.html')


@app.route('/experiment_start', methods=['POST'])
def experiment_start():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']

    success = _experiment_start(key, time_to_expire_s)
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@app.route('/run_start', methods=['POST'])
def run_start():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']

    success = _experiment_start(key, time_to_expire_s)
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@app.route('/run_end', methods=['POST'])
def run_end():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']

    success = _experiment_start(key, time_to_expire_s)
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@app.route('/experiment_end', methods=['POST'])
def experiment_end():
    data = request.json
    key = data['key']
    success = _experiment_end(key)
    return jsonify({'unregistered': {'key': key,
                                   'time': success}})


@app.route('/testing_experiment_start', methods=['POST'])
def testing_experiment_start():
    if request.method == 'POST':
        key = request.form.get('key')
        time_to_expire_s = int(request.form.get('expire'))
        success = _experiment_start(key, time_to_expire_s)
        # return jsonify({'registered': {'key': key,
        #                               'time': success}})
        return redirect(url_for('manage'))


@app.route('/testing_run_start', methods=['POST'])
def testing_run_start():
    if request.method == 'POST':
        key = request.form.get('key')
        time_to_expire_s = int(request.form.get('expire'))
        success = _experiment_start(key, time_to_expire_s)
        # return jsonify({'registered': {'key': key,
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

# ============= EOF =============================================
