from flask import Flask, Blueprint
from config import Config
from jsonschema import FormatChecker
from werkzeug.contrib.fixers import ProxyFix
from flask_apscheduler import APScheduler
from flask_executor import Executor
from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from flask_sslify import SSLify


app = Flask(__name__)
# FIXME: sslify is off because secret servers listen http, not https
# sslify = SSLify(app)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app)
logger = app.logger
logger.setLevel(app.config['LOGGER_LEVEL'])


db = SQLAlchemy(app)
session = db.session


blueprint = Blueprint('api', __name__, url_prefix='/webinars/api/v1')
api = Api(blueprint, version='1.0', title='Lectarium API', description='Lectarium API', authorizations={
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;TOKEN&gt;'**"
    }
}, security='apikey', format_checker=FormatChecker(formats=("date", "time")))
app.register_blueprint(blueprint)


migrate = Migrate(app, db)


scheduler = APScheduler(app=app)
executor = Executor(app)

with app.app_context():
    import lectarium_app.models as models

    # from lectarium_app import global_routes
    # from . import ath_routes, loy_routes, pmt_routes, directories_routes, stc_routes, param_routes, clm_routes, utm_routes
    # from . import redirect_routes
    # from . import event_service  # This application has no routes
    # from . import scheduled_jobs
