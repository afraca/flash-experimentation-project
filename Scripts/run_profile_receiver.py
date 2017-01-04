"""
Required: flask and flask-cors
set FLASK_APP=run_profile_receiver.py
flask run --host=0.0.0.0
"""

from datetime import datetime
from urllib.parse import unquote
import sqlite3
from pathlib import Path
import pickle
from base64 import b64decode
import json

from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ROOT_PATH = Path.cwd().parent
DB_PATH = ROOT_PATH / 'logfile.db'
CONNECTION = sqlite3.connect(str(DB_PATH))
CURSOR = CONNECTION.cursor()


@app.route('/')
def serve():
    """ Executions make request to here """
    query_params = request.args
    required = ['project', 'compiler', 'optimized', 'version', 'standalone', 'elapsed']

    for name in required:
        if name not in query_params:
            raise MissingArgumentException('Missing query parameter \'{}\''.format(name))

    project = unquote(query_params.get('project'))
    # Config was pickled, base64 encoded, now un-pickled and converted to json
    config_b64 = None if 'config' not in query_params else query_params.get('config')
    config = json.dumps(pickle.loads(b64decode(config_b64)))
    compiler = int(query_params.get('compiler'))
    optimized = int(query_params.get('optimized')) == 1
    # Somehow when there are no quotes you get problems when unquoting?
    version = query_params.get('version')
    standalone = int(query_params.get('standalone')) == 1
    elapsed = int(query_params.get('elapsed'))
    datetimestamp = datetime.now().isoformat()

    with CONNECTION:
        fields = '(project, compiler, optimized, version, standalone, elapsed, created_at, config)'
        info = (project, compiler, optimized, version, standalone, elapsed, datetimestamp, config)
        CURSOR.execute('INSERT INTO log {} VALUES (?,?,?,?,?,?,?, ?)'.format(fields), info)
    return 'Insertion completed'


@app.route('/ping')
def ping():
    """ Let applications know we're reachable """
    return 'pong'


@app.route('/crossdomain.xml')
def crossdomain():
    """ Adobe security constraints """
    xml = """
<?xml version="1.0"?>
<cross-domain-policy>
  <allow-access-from domain="*" />
</cross-domain-policy>
"""
    return Response(xml, mimetype='text/xml')


@app.route('/mark')
def mark():
    """ Tab marks when done with running """
    with CONNECTION:
        CURSOR.execute('INSERT INTO marks (mark) VALUES (?)', str(1))
    return '1'


@app.route('/asktabdone')
def ask_tab_done():
    """ Our global runner pings continuously to know if it should continue """
    with CONNECTION:
        CURSOR.execute('SELECT COUNT(*) FROM marks')
        result = CURSOR.fetchone()[0]
        return str(result)


@app.route('/unmark')
def unmark():
    """ On startup, and when continuing after failed tab, discard old marks """
    with CONNECTION:
        CURSOR.execute('DELETE FROM marks')
    return '1'


@app.route('/callmethod')
def callmethod():
    """ Executions make request to here """
    query_params = request.args
    required = ['optimized', 'utime', 'stime', 'maxrss', 'ixrss', 'idrss', 'seed']
    for name in required:
        if name not in query_params:
            raise MissingArgumentException('Missing query parameter \'{}\''.format(name))
    optimized = int(query_params.get('optimized')) == 1
    user_time = float(query_params.get('utime'))
    system_time = float(query_params.get('stime'))
    max_rss = int(query_params.get('maxrss'))
    ix_rss = int(query_params.get('maxrss'))
    id_rss = int(query_params.get('maxrss'))
    seed = int(query_params.get('seed'))
    # Config was pickled, base64 encoded, now un-pickled and converted to json
    config_b64 = None if 'config' not in query_params else query_params.get('config')
    config = json.dumps(pickle.loads(b64decode(config_b64)))
    datetimestamp = datetime.now().isoformat()
    with CONNECTION:
        info = (optimized, user_time, system_time, max_rss, ix_rss, id_rss, seed, config, datetimestamp)
        fields = '(optimized, utime, stime, maxrss, ixrss, idrss, seed, config, created_at)'
        CURSOR.execute(
            'INSERT INTO callmethod {} VALUES (?,?,?,?,?,?,?,?,?)'.format(fields),
            info)
    return 'Insertion completed'


@app.route('/config-debug')
def config_debug():
    """ To quickly check in browser some config """
    config_str = request.args.get('config')
    config = pickle.loads(b64decode(config_str))
    return str(config)


class MissingArgumentException(Exception):
    """ Easier recognition of problem """
    pass

# We cannot get debug mode for Flask to work on Windows, it is a known problem
# Let the errors flow out

# @app.errorhandler(MissingArgumentException)
# def handle_missing_arguments(error):
#     """ _ """
#     return str(error), 500
#
#
# @app.errorhandler(ValueError)
# def handle_value_error(error):
#     """ _ """
#     return str(error), 500
#
#
# @app.errorhandler(Exception)
# def handle_every_error(error):
#     """ _ """
#     return str(error), 500
