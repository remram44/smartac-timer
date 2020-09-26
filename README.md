SmartAC Timer
=============

This is a web application allowing you to control ThinkEco/mymodlet.com air conditioner without using the mymodlet.com website or Android app.

In addition to being a much simpler interface, it supports setting a timer for your AC, such as "turn off in 30 minutes".

The mymodlet.com website has no stable API, so this might break any time they update. Though updating the code to match should only take a few seconds.

Disclaimer
----------

I made this for my own need, but I'm happy to help you set this up for yourself or build upon it.

I am not affiliated with ThinkEco or Con Edison. I understand that there is no "public API" to mymodlet.com, but I did not "hack" it in any way. I am simply sending the same requests my web browser would send if I clicked the button.

This software is provided without warranty, subject to the terms of the LICENSE.

Setup intructions
-----------------

* Clone this repository
* Install Python 3 and [Poetry](https://python-poetry.org/)
* Install dependencies using `poetry install`. This will create a virtual environment for you
* Create the configuration file: copy `settings.py.sample` to `settings.py`
* Edit `settings.py`, put in the email and password of your ThinkEco account

To run the app:

* Run `poetry run uvicorn --log-level=info smartac_timer:app --reload`
* Open [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/) in your browser
