from flask import Flask, render_template
import logging
import os


logging.basicConfig(level=logging.WARNING)

app = Flask('smartac_timer',
            template_folder=os.path.join(os.path.dirname(__file__),
                                         'templates'))


@app.route('/')
def index():
    return render_template('index.html')
