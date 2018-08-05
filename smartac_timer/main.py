from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_from_directory
import logging
import os
import requests
import unix_at


logging.basicConfig(level=logging.WARNING)

with open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       'settings.py'), 'rb') as fp:
    SETTINGS = {}
    exec(fp.read(), SETTINGS, SETTINGS)

app = Flask('smartac_timer',
            template_folder=os.path.join(os.path.dirname(__file__),
                                         'templates'),
            static_url_path='/static')


@app.route('/static/<path:path>')
def builtin_static_route(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    return render_template('index.html',
                           devices=SETTINGS['DEVICES'])


@app.route('/set-timer', methods=['POST'])
def set_timer():
    req = request.get_json()
    modlet = req.pop('modlet')
    mode = req.pop('mode')
    timeout = req.pop('time')
    if req:
        raise ValueError
    logging.warning("Got request: modlet=%s, mode=%s, timeout=%s",
                    modlet, mode, timeout)
    job = unix_at.submit_python_job('smartac_timer.main.update_smartac',
                                    'now + %s minutes' % timeout,
                                    modlet,
                                    mode)
    logging.warning("Submitted job %s", job.name)
    # TODO: Replace old schedule (save `at(1)` job name in a file?)
    return jsonify({'changed': True,
                    'time': datetime.utcnow(),
                    'turn': mode})


def update_smartac(modlet, mode):
    set_mode = dict(on=True, off=False)[mode]
    logging.warning("Triggering AC: mode=%s", mode)
    req = requests.post(
        'https://mymodlet.com/SmartAC/UserSettings',
        headers={
            'Referer': 'https://mymodlet.com/SmartAC',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': SETTINGS['COOKIE'],
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json, text/javascript',
        },
        json={
            'applianceId': modlet,
            'targetTemperature': 72,
            'thermostated': set_mode
        },
    )
    req.raise_for_status()
    if not req.json().get('Success'):
        raise ValueError("Server indicated failure")
