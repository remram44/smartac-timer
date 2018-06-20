import logging

import smartac_timer.main


logging.basicConfig(level=logging.WARNING)

# WSGI interface
application = smartac_timer.main.app
