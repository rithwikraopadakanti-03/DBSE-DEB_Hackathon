from datetime import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from database import complaints_collection, users_collection, notifications_collection
from utils import serialize_doc, serialize_docs, role_required
from ml_classifier import classifier

complaints_bp = Blueprint('complaints', __name__)

VALID_STATUSES = ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed']
VALID_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

def find_complaint_by_id_or_complaint_id(identifier):
    """Helper to query a complaint either by its MongoDB ObjectId or complaint_id string."""
    query = None
    if ObjectId.is_valid(identifier):
        query = {'$or': [{'_id': ObjectId(identifier)}, {'complaint_id': identifier}]}
    else:
        query = {'complaint_id': identifier}
    return complaints_collection.find_one(query)

@complaints_bp.route('', methods=['POST'])
@jwt_required()
def create_complaint():
    """
    Create a new complaint (Student role).
    Request body: {title, description, category, location, priority (optional), attachments (optional)}
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'student')

        # Check role permission
        if user_role != 'student':
            return jsonify({
                'error': 'Forbidden',
                'message': 'Only students are permitted to submit new complaints'
            }), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Validation Error', 'message': 'JSON payload is required'}), 400

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        location = data.get('location', '').strip()
        priority = data.get('priority', '').strip()
        attachments = data.get('attachments', [])

        if not isinstance(attachments, list):
            attachments = []

        # Validate required fields
        if not title:
            return jsonify({'error': 'Validation Error', 'message': 'Complaint title is required'}), 400
        if not description:
            return jsonify({'error': 'Validation Error', 'message': 'Complaint description is required'}), 400
        if not category:
            return jsonify({'error': 'Validation Error', 'message': 'Category is required'}), 400
        if not location:
            return jsonify({'error': 'Validation Error', 'message': 'Location is required'}), 400

        # Auto-predict priority with ML classifier if missing or invalid
        if not priority or priority not in VALID_PRIORITIES:
            priority = classifier.predict_priority(title, description, category=category)

        # Retrieve student details
        user_info = None
        try:
            user_info = users_collection.find_one({'_id': ObjectId(current_user_id)})
        except Exception:
            pass

        student_name = claims.get('name') or (user_info.get('name') if user_info else 'Student')
        student_email = claims.get('email') or (user_info.get('email') if user_info else '')
        student_id_val = user_info.get('student_id') if user_info else None

        # Generate unique sequential complaint_id: COMP-YYYY-XXX
        current_year = datetime.utcnow().year
        total_count = complaints_collection.count_documents({}) + 1
        complaint_id = f"COMP-{current_year}-{total_count:03d}"
        while complaints_collection.find_one({'complaint_id': complaint_id}):
            total_count += 1
            complaint_id = f"COMP-{current_year}-{total_count:03d}"

        now_iso = datetime.utcnow().isoformat()

        status_history = [
            {
                'status': 'Submitted',
                'changed_by': student_name,
                'timestamp': now_iso,
                'note': 'Complaint submitted successfully by student'
            }
        ]

        new_complaint = {
            'complaint_id': complaint_id,
            'title': title,
            'description': description,
            'category': category,
            'location': location,
            'priority': priority,
            'status': 'Submitted',
            'department': category,  # Initially mapped to category
            'assigned_to': None,
            'resolution_note': None,
            'attachments': attachments,
            'user_id': current_user_id,
            'student_name': student_name,
            'student_email': student_email,
            'student_id': student_id_val,
            'status_history': status_history,
            'created_at': now_iso,
            'updated_at': now_iso,
            'resolved_at': None
        }

        result = complaints_collection.insert_one(new_complaint)
        new_complaint['_id'] = result.inserted_id

        # Create student notification
        notifications_collection.insert_one({
            'user_id': current_user_id,
            'complaint_id': complaint_id,
            'title': f"Complaint Created: {complaint_id}",
            'message': f"Your complaint '{title}' was registered successfully with status 'Submitted'.",
            'is_read': False,
            'created_at': now_iso
        })

        return jsonify({
            'message': 'Complaint submitted successfully',
            'complaint': serialize_doc(new_complaint)
        }), 201

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@complaints_bp.route('', methods=['GET'])
@jwt_required()
def get_complaints():
    """
    Get complaints with filtering and pagination.
    Students see only their complaints; Admins see all complaints.
    Query params: status, category, priority, page, limit, search
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'student')

        query = {}
        # Students can only access their own submissions
        if user_role != 'admin':
            query['user_id'] = current_user_id

        # Query filters
        status = request.args.get('status', '').strip()
        if status:
            query['status'] = status

        category = request.args.get('category', '').strip()
        if category:
            query['category'] = category

        priority = request.args.get('priority', '').strip()
        if priority:
            query['priority'] = priority

        search = request.args.get('search', '').strip()
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}},
                {'complaint_id': {'$regex': search, '$options': 'i'}},
                {'location': {'$regex': search, '$options': 'i'}}
            ]

        # Pagination
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1

        try:
            limit = max(1, min(100, int(request.args.get('limit', 10))))
        except ValueError:
            limit = 10

        skip = (page - 1) * limit

        total_records = complaints_collection.count_documents(query)
        cursor = complaints_collection.find(query).sort('created_at', -1).skip(skip).limit(limit)
        complaints_list = list(cursor)

        total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1

        return jsonify({
            'complaints': serialize_docs(complaints_list),
            'total': total_records,
            'page': page,
            'limit': limit,
            'pages': total_pages
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@complaints_bp.route('/<id>', methods=['GET'])
@jwt_required()
def get_complaint_by_id(id):
    """
    Get complaint details by MongoDB ObjectId or complaint_id string.
    Includes full status history.
    """
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'student')

        complaint = find_complaint_by_id_or_complaint_id(id)
        if not complaint:
            return jsonify({'error': 'Not Found', 'message': 'Complaint not found'}), 404

        # Enforce student access restriction
        if user_role != 'admin' and str(complaint.get('user_id')) != str(current_user_id):
            return jsonify({'error': 'Forbidden', 'message': 'Access denied to this complaint'}), 403

        return jsonify({
            'complaint': serialize_doc(complaint)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@complaints_bp.route('/<id>/status', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_complaint_status(id):
    """
    Update complaint status (Admin only).
    Request body: {status, note}
    Valid statuses: Submitted, Under Review, In Progress, Resolved, Closed
    """
    try:
        claims = get_jwt()
        admin_name = claims.get('name', 'Admin')

        complaint = find_complaint_by_id_or_complaint_id(id)
        if not complaint:
            return jsonify({'error': 'Not Found', 'message': 'Complaint not found'}), 404

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Validation Error', 'message': 'JSON payload is required'}), 400

        new_status = data.get('status', '').strip()
        note = data.get('note', '').strip()

        if not new_status or new_status not in VALID_STATUSES:
            return jsonify({
                'error': 'Validation Error',
                'message': f"Status must be one of: {', '.join(VALID_STATUSES)}"
            }), 400

        now_iso = datetime.utcnow().isoformat()
        history_entry = {
            'status': new_status,
            'changed_by': admin_name,
            'timestamp': now_iso,
            'note': note or f"Status changed to {new_status}"
        }

        update_fields = {
            'status': new_status,
            'updated_at': now_iso
        }
        if new_status in ['Resolved', 'Closed'] and not complaint.get('resolved_at'):
            update_fields['resolved_at'] = now_iso

        complaints_collection.update_one(
            {'_id': complaint['_id']},
            {
                '$set': update_fields,
                '$push': {'status_history': history_entry}
            }
        )

        # Notify student
        student_user_id = complaint.get('user_id')
        if student_user_id:
            notifications_collection.insert_one({
                'user_id': student_user_id,
                'complaint_id': complaint.get('complaint_id'),
                'title': f"Status Update: {complaint.get('complaint_id')}",
                'message': f"Your complaint '{complaint.get('title')}' is now '{new_status}'. Note: {note or 'Status updated by administrator.'}",
                'is_read': False,
                'created_at': now_iso
            })

        updated_complaint = complaints_collection.find_one({'_id': complaint['_id']})

        return jsonify({
            'message': 'Complaint status updated successfully',
            'complaint': serialize_doc(updated_complaint)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@complaints_bp.route('/classify', methods=['POST'])
@jwt_required()
def classify_complaint():
    """
    Run machine learning classification on title and description.
    Request body: {title, description}
    Returns: {category_predictions: [{category, confidence}, ...], priority: str}
    """
    try:
        data = request.get_json(silent=True) or {}
        title = data.get('title', '')
        description = data.get('description', '')

        if not title and not description:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Please provide title or description for classification'
            }), 400

        recommendations = classifier.get_recommendations(title, description)
        return jsonify(recommendations), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@complaints_bp.route('/stats', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_complaints_stats():
    """
    Get summary counts by status, category, and priority (Admin only).
    """
    try:
        # Aggregation by status
        status_counts = {status: 0 for status in VALID_STATUSES}
        for doc in complaints_collection.aggregate([
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]):
            if doc['_id'] in status_counts:
                status_counts[doc['_id']] = doc['count']
            elif doc['_id']:
                status_counts[doc['_id']] = doc['count']

        # Aggregation by category
        category_counts = {cat: 0 for cat in classifier.categories}
        for doc in complaints_collection.aggregate([
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}}
        ]):
            if doc['_id']:
                category_counts[doc['_id']] = doc['count']

        # Aggregation by priority
        priority_counts = {prio: 0 for prio in VALID_PRIORITIES}
        for doc in complaints_collection.aggregate([
            {'$group': {'_id': '$priority', 'count': {'$sum': 1}}}
        ]):
            if doc['_id'] in priority_counts:
                priority_counts[doc['_id']] = doc['count']
            elif doc['_id']:
                priority_counts[doc['_id']] = doc['count']

        total = complaints_collection.count_documents({})
        open_count = complaints_collection.count_documents({'status': {'$in': ['Submitted', 'Under Review', 'In Progress']}})
        resolved_count = complaints_collection.count_documents({'status': {'$in': ['Resolved', 'Closed']}})

        return jsonify({
            'total': total,
            'open': open_count,
            'resolved': resolved_count,
            'by_status': status_counts,
            'by_category': category_counts,
            'by_priority': priority_counts
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500
