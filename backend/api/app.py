#!/usr/bin/env python3
import os
from flask import jsonify, Flask
from flask_cors import CORS
from dotenv import load_dotenv
from api.library.views import app_views
from models.engine.db import db
from api.cli_commands import register_cli_commands
from flask_migrate import Migrate
from helpers.decorators import is_authenticated, token_required, admin_required
from models.engine.admin_manager import AdminManager


student_manager = AdminManager(db)
authenticated_user_requests = 0
unauthenticated_user_requests = 0

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


# Migrations
migrate = Migrate(app, db)

# initialize database
CORS(app)

# load environment variables
load_dotenv(override=True)
SECRET_KEY = os.getenv('SECRET_KEY')


# register blueprints
app.register_blueprint(app_views)


# create tables
with app.app_context():
    db.create_all()

# register cli commands
register_cli_commands(app)


# count number of request
@app.before_request
def count_requests():
    global authenticated_user_requests, unauthenticated_user_requests
    if is_authenticated():
        authenticated_user_requests += 1
    else:
        unauthenticated_user_requests += 1


@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'message': 'OK'}), 200


@app.route('/api/v1/admin/statistics', methods=['GET'])
@token_required
@admin_required
def statistics():
    try:
        data = student_manager.statistics()
        requests = {
            'authenticated_user_requests': authenticated_user_requests,
            'unauthenticated_user_requests': unauthenticated_user_requests
        }
        data['requests'] = requests
        return jsonify({'message': 'success', 'data':
                        data
                        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


if __name__ == '__main__':
    # Use the PORT environment variable or default to 3000
    port = int(os.getenv('PORT', 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
