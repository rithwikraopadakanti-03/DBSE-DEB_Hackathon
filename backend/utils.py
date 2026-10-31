from functools import wraps
from datetime import datetime, date
from bson import ObjectId
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

def serialize_doc(doc):
    """
    Recursively serialize a MongoDB document converting ObjectId to str
    and formatting datetime instances as ISO strings.
    Ensures both 'id' and '_id' are available as string representations.
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                str_id = str(value)
                serialized['id'] = str_id
                serialized['_id'] = str_id
            elif isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, (datetime, date)):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = serialize_doc(value)
            elif isinstance(value, list):
                serialized[key] = [
                    serialize_doc(item) if isinstance(item, (dict, list, ObjectId, datetime, date)) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized
    return doc

def serialize_docs(docs):
    """Serialize a list of MongoDB documents."""
    return [serialize_doc(doc) for doc in docs]

def role_required(allowed_roles):
    """
    Decorator to ensure the authenticated user has one of the allowed roles.
    Works seamlessly with Flask-JWT-Extended claims or database lookup.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')
            if not user_role or user_role not in allowed_roles:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f"Access forbidden: requires one of {allowed_roles} roles"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required():
    """Decorator ensuring that only users with role 'admin' can access the route."""
    return role_required(['admin'])
