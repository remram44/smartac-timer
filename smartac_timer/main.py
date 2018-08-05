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
                                    mode,
                                    python=SETTINGS.get('PYTHON'))
    logging.warning("Submitted job %s", job.name)
    # TODO: Replace old schedule (save `at(1)` job name in a file?)
    return jsonify({'changed': True,
                    'time': datetime.utcnow(),
                    'turn': mode})


def update_smartac(modlet, mode):
    set_mode = dict(on='SwitchOn', off='SwitchOff')[mode]
    logging.warning("Triggering AC: mode=%s", mode)
    req = requests.post(
        'https://web.mymodlet.com/Devices/%s' % set_mode,
        headers={
            'Referer': 'https://web.mymodlet.com/Devices',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': SETTINGS['COOKIE'],
            'Content-Type': 'application/json',
            'Accept': '*/*',
        },
        json={
            'data': '{"id":"%s"}' % modlet,  # Yes, it is double-json-encoded
        },
    )
    req.raise_for_status()
