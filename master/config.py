import os
from dotenv import load_dotenv

# In fact, it is not required, but "Explicit is better than implicit."
load_dotenv()


class Config(object):
    SCHEDULER_API_ENABLED = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RAW_MYSQL_USERNAME = os.environ['MYSQL_USERNAME']
    RAW_MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
    RAW_MYSQL_HOSTNAME = os.environ['MYSQL_HOSTNAME']
    RESTPLUS_VALIDATE = True

    # Without this setting flask_restplus (namely, api object) ignores error handlers
    #  that was registered by api.error_handler(ExceptionType), except werkzeug.HTTPException
    #  and its subtypes. See method api.handle_error.
    PROPAGATE_EXCEPTIONS = False

    LOGGER_LEVEL = os.getenv('LOGGER_LEVEL', 'INFO')
    # flask reloader sets variable WERKZEUG_RUN_MAIN for the second instance.
    # Second instance will be launched in the following cases:
    #  $ FLASK_ENV=development flask run
    #  $ FLASK_ENV=development python3 ./run.py
    ENABLE_SCHEDULER = (os.getenv('ENABLE_SCHEDULER', '0') == '1') and (os.getenv('WERKZEUG_RUN_MAIN') != 'true')
    ENABLE_RELOAD = (not ENABLE_SCHEDULER) and (os.getenv('FLASK_ENV', 'production') == 'development')

    # If true, module 'constant_objects.py' checks that certain objects are presented
    #  in a database and creates them, if necessary.
    # Usually you want this variable to be true, except db migration process.
    CREATE_OBJECTS = (os.getenv('CREATE_OBJECTS', '1') == '1')
