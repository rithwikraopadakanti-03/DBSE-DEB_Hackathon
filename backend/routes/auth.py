import re
from datetime import datetime
from bson import ObjectId
import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from database import users_collection
from utils import serialize_doc

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user (student or admin).
    Request body: {name, email, password, role ('student'|'admin'), student_id (optional), department (optional)}
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid request body', 'message': 'JSON payload is required'}), 400

        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'student').strip().lower()
        student_id = data.get('student_id', '').strip() if data.get('student_id') else None
        department = data.get('department', '').strip() if data.get('department') else None

        # Validation
        if not name:
            return jsonify({'error': 'Validation Error', 'message': 'Name is required'}), 400
        if not email or not re.match(EMAIL_REGEX, email):
            return jsonify({'error': 'Validation Error', 'message': 'A valid email address is required'}), 400
        if not password or len(password) < 6:
            return jsonify({'error': 'Validation Error', 'message': 'Password must be at least 6 characters long'}), 400
        if role not in ['student', 'admin']:
            return jsonify({'error': 'Validation Error', 'message': "Role must be either 'student' or 'admin'"}), 400

        # Check existing user
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'Conflict', 'message': 'An account with this email already exists'}), 409

        # Hash password using bcrypt
        password_salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), password_salt).decode('utf-8')

        new_user = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role,
            'student_id': student_id,
            'department': department,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        result = users_collection.insert_one(new_user)
        user_id_str = str(result.inserted_id)

        # Generate JWT access token
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims={
                'role': role,
                'email': email,
                'name': name
            }
        )

        user_response = {
            'id': user_id_str,
            '_id': user_id_str,
            'name': name,
            'email': email,
            'role': role,
            'student_id': student_id,
            'department': department,
            'created_at': new_user['created_at']
        }

        return jsonify({
            'message': 'User registered successfully',
            'token': access_token,
            'access_token': access_token,
            'user': user_response
        }), 201

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user with email and password.
    Request body: {email, password}
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid request body', 'message': 'JSON payload is required'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Validation Error', 'message': 'Email and password are required'}), 400

        user = users_collection.find_one({'email': email})
        if not user:
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid email or password'}), 401

        # Verify password
        user_password_hash = user.get('password', '')
        if not bcrypt.checkpw(password.encode('utf-8'), user_password_hash.encode('utf-8')):
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid email or password'}), 401

        user_id_str = str(user['_id'])
        user_role = user.get('role', 'student')
        user_name = user.get('name', '')

        # Generate JWT access token
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims={
                'role': user_role,
                'email': user.get('email'),
                'name': user_name
            }
        )

        user_response = {
            'id': user_id_str,
            '_id': user_id_str,
            'name': user_name,
            'email': user.get('email'),
            'role': user_role,
            'student_id': user.get('student_id'),
            'department': user.get('department'),
            'created_at': user.get('created_at')
        }

        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'access_token': access_token,
            'user': user_response
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Retrieve current authenticated user's profile information.
    """
    try:
        current_user_id = get_jwt_identity()

        try:
            object_id = ObjectId(current_user_id)
        except Exception:
            return jsonify({'error': 'Invalid Token', 'message': 'Invalid user identity'}), 401

        user = users_collection.find_one({'_id': object_id})
        if not user:
            return jsonify({'error': 'Not Found', 'message': 'User profile not found'}), 404

        # Remove sensitive password field
        user.pop('password', None)

        return jsonify({
            'user': serialize_doc(user)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500
