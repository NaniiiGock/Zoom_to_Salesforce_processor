from models.OpenIAClient import process_meeting_data
from flask import Flask, request, jsonify
import logging
import json
import requests
import sys
from dotenv import load_dotenv
import os 
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import re
from flask_limiter import Limiter
from datetime import datetime, timedelta
from functools import wraps
from flask_limiter.util import get_remote_address


load_dotenv()

BASE_URL_SalesforceConnector = os.getenv('BASE_URL_SalesforceConnector')
BASE_URL_ZoomMeeting = os.getenv('BASE_URL_ZoomMeeting')
BASE_URL_Openai = os.getenv('BASE_URL_Openai')
BASE_URL_MAIN = os.getenv('BASE_URL_MAIN')


app = Flask(__name__)
# app.config['SECRET_KEY'] =  os.getenv('SECRET_KEY')
# app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1)

users = {} 

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger(__name__)
# logger.info(f"Loaded SECRET_KEY (first 5 chars): {app.config['SECRET_KEY'][:5]}")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        logger.info(f"Received Authorization header: {token}")
        
        if not token:
            logger.warning("No token provided")
            return jsonify({'message': 'Token is missing!'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        logger.info(f"Parsed token: {token}")
        
        try:
            logger.info(f"Attempting to decode token with SECRET_KEY: {app.config['SECRET_KEY'][:5]}...")
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            logger.info(f"Successfully decoded token. Payload: {data}")
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token error: {str(e)}")
            return jsonify({'message': f'Token is invalid! Error: {str(e)}'}), 401
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            return jsonify({'message': f'Unexpected error: {str(e)}'}), 500
        
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
# @limiter.limit("20 per minute")
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required!'}), 400
    
    if username in users:
        return jsonify({'message': 'Username already exists!'}), 400
    
    # Password policy: at least 8 characters, 1 uppercase, 1 lowercase, 1 number
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        return jsonify({'message': 'Password does not meet security requirements!'}), 400
    
    # Using 'pbkdf2:sha256' method, which is more secure
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    users[username] = {'username': username, 'password': hashed_password}
    
    return jsonify({'message': 'Registered successfully!'}), 201

@app.route('/login', methods=['POST'])
# @limiter.limit("20 per minute")
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        logger.warning("Login attempt with missing credentials")
        return jsonify({'message': 'Could not verify!'}), 401
    
    user = users.get(auth.username)
    if not user:
        logger.warning(f"Login attempt for non-existent user: {auth.username}")
        return jsonify({'message': 'User not found!'}), 401
    
    if check_password_hash(user['password'], auth.password):
        token = jwt.encode({
            'username': user['username'],
            'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
        }, app.config['SECRET_KEY'])
        logger.info(f"Generated token for user {auth.username}: {token}")
        return jsonify({'token': token})
    
    logger.warning(f"Failed login attempt for user: {auth.username}")
    return jsonify({'message': 'Could not verify!'}), 401


@app.route('/')
# @limiter.limit("5 per minute")
# @token_required
def home():
    logger.debug('Debug message from the home route')
    logger.info('Info message from the home route')
    logger.warning('Warning message from the home route')
    logger.error('Error message from the home route')
    logger.critical('Critical message from the home route')

    return f"Loaded SECRET_KEY: {app.config['SECRET_KEY']}"


def get_ids(participants):
    response = requests.post(f"{BASE_URL_SalesforceConnector}/get_ids", json={'participants': participants})
    print('POST /get_ids')
    return response.json()

def get_cleared_info(ids):
    response = requests.post(f"{BASE_URL_SalesforceConnector}/get_cleared_info", json={'ids': ids})
    print('POST /get_cleared_info')
    return response.json()

def update_contacts(contacts):
    response = requests.post(f"{BASE_URL_SalesforceConnector}/update_contacts", json={'contacts': contacts})
    print('POST /update_contacts')
    return response.json()


def get_participants(json_file_path):
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)
    response = requests.post(f"{BASE_URL_ZoomMeeting}/get_participants", json=json_data)
    return response.json()


def update_contacts(contacts):
    response = requests.post(f"{BASE_URL_SalesforceConnector}/update_contacts", json={'contacts': contacts})
    return response.json()

def processing(webvtt_file, zoom_json_file, participants):
    response = requests.post(f"{BASE_URL_Openai}/process", json={'webvtt_file': webvtt_file, 'zoom_json_file': zoom_json_file, 'participants': participants})
    result = response.json()
    updated_contacts = result['updated_contacts']
    call_data = result['call_data']
    return updated_contacts, call_data

# webvtt_file = "example/transcript.webvtt"
# zoom_json_file = "example/zoom_meeting.json"


@app.route('/process', methods=['POST'])
# @token_required
# @limiter.limit("10 per minute")
def process():
    data = request.get_json()
    required_fields = ['webvtt_file', 'zoom_json_file']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    webvtt_file = data['webvtt_file']
    zoom_json_file = data['zoom_json_file']

    if not (os.path.exists(webvtt_file) and os.path.exists(zoom_json_file)):
        return jsonify({'message': 'Invalid file path!'}), 400
    
    participants = get_participants(zoom_json_file)
    ids = get_ids(participants)
    contacts_details = get_cleared_info(ids)
    
    result = processing(webvtt_file, zoom_json_file, contacts_details)
    print(result)

    updated_contacts, call_data = result[0], result[1]
    print("Updated contacts:", updated_contacts)
    print("Call data:", call_data)
    response = update_contacts(updated_contacts)
    
    return result


if __name__ == '__main__':
    host, port = BASE_URL_MAIN[:-4], BASE_URL_MAIN[-4:]
    # app.run(port=port, host='localhost', ssl_context='adhoc')
    app.run(port=port, host='localhost')