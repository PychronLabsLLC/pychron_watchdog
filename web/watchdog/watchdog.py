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
from flask import request, render_template, jsonify, redirect, url_for, Blueprint

bp = Blueprint('watchdog', __name__, url_prefix='/wd')
R = redis.Redis(host='redis')


@bp.route('/')
def index():
    return render_template('home.html')


def make_ajax_table(tag, row_factory):
    data = [row_factory(k) for k in R.keys(tag)]

    resp = {'data': data}
    return jsonify(resp)


@bp.route('/success')
def success():
    def row_factory(k):
        v = R.get(k)
        v = datetime.datetime.fromtimestamp(float(v))
        return k.decode('utf8'), v

    return make_ajax_table('success:*', row_factory)


@bp.route('/failed')
def failed():
    def row_factory(k):
        v = R.get(k)
        v = datetime.datetime.fromtimestamp(float(v))
        return k.decode('utf8'), v

    return make_ajax_table('failed:*', row_factory)


@bp.route('/status')
def status():
    def row_factory(k):
        kk = k.decode('utf8')
        value = float(R.get(k))
        ts = datetime.datetime.fromtimestamp(value)
        tl = int(value - time.time())
        return kk, ts, tl

    return make_ajax_table('experiment:*', row_factory)


@bp.route('/manage')
def manage():
    return render_template('manage.html')


@bp.route('/experiment_start', methods=['POST'])
def experiment_start():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']
    addresses = data.get('addresses')

    success = _register_key(key, time_to_expire_s, 'experiment_start', addresses)
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@bp.route('/run_start', methods=['POST'])
def run_start():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']

    success = _register_key(key, time_to_expire_s, 'run_start')
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@bp.route('/run_save', methods=['POST'])
def run_save():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']

    success = _register_key(key, time_to_expire_s, 'run_save')
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@bp.route('/run_end', methods=['POST'])
def run_end():
    data = request.json
    key = data['key']
    time_to_expire_s = data['expire']

    success = _register_key(key, time_to_expire_s, 'run_end')
    return jsonify({'registered': {'key': key,
                                   'time': success}})


@bp.route('/experiment_end', methods=['POST'])
def experiment_end():
    data = request.json
    key = data['key']
    success = _experiment_end(key)
    return jsonify({'unregistered': {'key': key,
                                   'time': success}})


@bp.route('/testing_experiment_start', methods=['POST'])
def testing_experiment_start():
    if request.method == 'POST':
        key = request.form.get('key')
        time_to_expire_s = int(request.form.get('expire'))
        success = _register_key(key, time_to_expire_s)
        # return jsonify({'registered': {'key': key,
        #                               'time': success}})
        return redirect(url_for('manage'))


@bp.route('/testing_run_start', methods=['POST'])
def testing_run_start():
    if request.method == 'POST':
        key = request.form.get('key')
        time_to_expire_s = int(request.form.get('expire'))
        success = _register_key(key, time_to_expire_s)
        # return jsonify({'registered': {'key': key,
        #                               'time': success}})
        return redirect(url_for('manage'))


@bp.route('/testing_experiment_end', methods=['POST'])
def testing_experiment_end():
    if request.method == 'POST':
        key = request.form.get('key')
        success = _experiment_end(key)
        return redirect(url_for('manage'))


def _register_key(key, expire, event, addresses=None):
    key = f'experiment:{key}'
    expire_at = time.time() + expire
    R.set(key, str(expire_at))
    if addresses:
        R.set(f'email_addresses:{key}', ','.join(addresses))

    skey = f'event:{key}'
    R.set(skey, event)

    return R.get(key).decode('utf8')


def _experiment_end(key):
    key = f'experiment:{key}'
    skey = f'success:{key}'
    R.delete(key)
    R.set(skey, str(time.time()))
    return True

# ============= EOF =============================================
