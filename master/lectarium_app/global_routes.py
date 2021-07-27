import traceback
import functools
from datetime import datetime
from flask import request
from flask import jsonify, g
from . import api, app, db, logger, session
from lectarium_app.exceptions import *
from flask_restplus import inputs


webinar_nsp = api.namespace('Webinars', path='/webinars', description='Operations related to webinars')


@api.errorhandler(StatusChangeError)
def web_error_handler(e):
    return {'message': "You cannot change from {}, to {}".format(e.args[0], e.args[1])}, 400


@api.errorhandler(ClmOperationalError)
def web_error_handler(e):
    return {'message': "Error in clickmeeting API: {}".format(e.args[0])}, 400


pagination_parser = api.parser()
pagination_parser.add_argument('page', type=inputs.positive, help='Page number', default=1)
pagination_parser.add_argument('size', type=inputs.natural, help='Items per page or 0 for all items', default=0)
pagination_parser.add_argument('offset', type=inputs.natural, help='Skip first N items', default=0)
pagination_parser.add_argument('filter', help='Comma-separated filters: field1 EQ "value1", field2 GE "value2"')
pagination_parser.add_argument('order_by', help='Comma-separated ORDER BY criterions: "field1, -field2"')

filter_parser = api.parser()
filter_parser.add_argument('filter', help='Comma-separated filters: field1 EQ "value1", field2 GE "value2"')
