from flask import Flask, render_template
import logging
import os


logging.basicConfig(level=logging.WARNING)

app = Flask('smartac_timer',
            template_folder=os.path.join(os.path.dirname(__file__),
                                         'templates'),
            static_url_path='/static')


@app.route('/static/<path:path>')
def builtin_static_route(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    return render_template('index.html')
