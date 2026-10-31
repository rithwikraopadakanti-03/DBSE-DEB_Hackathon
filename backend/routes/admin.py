from datetime import datetime
from bson import ObjectId
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from database import complaints_collection, users_collection, notifications_collection
from utils import serialize_doc, serialize_docs, role_required
from ml_classifier import classifier

admin_bp = Blueprint('admin', __name__)

ALL_STATUSES = ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed']
ALL_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

def find_complaint(identifier):
    """Find complaint by ObjectId or string complaint_id."""
    if ObjectId.is_valid(identifier):
        return complaints_collection.find_one({'$or': [{'_id': ObjectId(identifier)}, {'complaint_id': identifier}]})
    return complaints_collection.find_one({'complaint_id': identifier})

@admin_bp.route('/complaints', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_admin_complaints():
    """
    Get full complaints list with filters and pagination (Admin only).
    Filters: status, category, priority, department, search, date_from, date_to
    """
    try:
        query = {}

        # Status filter
        status = request.args.get('status', '').strip()
        if status:
            query['status'] = status

        # Category filter
        category = request.args.get('category', '').strip()
        if category:
            query['category'] = category

        # Priority filter
        priority = request.args.get('priority', '').strip()
        if priority:
            query['priority'] = priority

        # Department filter
        department = request.args.get('department', '').strip()
        if department:
            query['department'] = department

        # Date range filter
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter['$gte'] = date_from
            if date_to:
                date_filter['$lte'] = date_to
            query['created_at'] = date_filter

        # Keyword search
        search = request.args.get('search', '').strip()
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}},
                {'complaint_id': {'$regex': search, '$options': 'i'}},
                {'student_name': {'$regex': search, '$options': 'i'}},
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

        total = complaints_collection.count_documents(query)
        cursor = complaints_collection.find(query).sort('created_at', -1).skip(skip).limit(limit)
        complaints_list = list(cursor)

        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return jsonify({
            'complaints': serialize_docs(complaints_list),
            'total': total,
            'page': page,
            'limit': limit,
            'pages': total_pages
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/complaints/<id>/assign', methods=['PUT'])
@jwt_required()
@role_required('admin')
def assign_complaint(id):
    """
    Assign complaint to department and specific personnel (Admin only).
    Body: {department, assigned_to}
    Sets status to 'Under Review' if currently 'Submitted'.
    """
    try:
        claims = get_jwt()
        admin_name = claims.get('name', 'Admin')

        complaint = find_complaint(id)
        if not complaint:
            return jsonify({'error': 'Not Found', 'message': 'Complaint not found'}), 404

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Validation Error', 'message': 'JSON payload is required'}), 400

        department = data.get('department', '').strip()
        assigned_to = data.get('assigned_to', '').strip()

        if not department and not assigned_to:
            return jsonify({'error': 'Validation Error', 'message': 'Provide department or assigned_to'}), 400

        now_iso = datetime.utcnow().isoformat()
        current_status = complaint.get('status', 'Submitted')
        new_status = 'Under Review' if current_status == 'Submitted' else current_status

        target_department = department or complaint.get('department')
        target_assigned_to = assigned_to or complaint.get('assigned_to')

        history_note = f"Assigned to {target_assigned_to or 'staff'} in {target_department} department"
        history_entry = {
            'status': new_status,
            'changed_by': admin_name,
            'timestamp': now_iso,
            'note': history_note
        }

        update_data = {
            'department': target_department,
            'assigned_to': target_assigned_to,
            'status': new_status,
            'updated_at': now_iso
        }

        complaints_collection.update_one(
            {'_id': complaint['_id']},
            {
                '$set': update_data,
                '$push': {'status_history': history_entry}
            }
        )

        # Notify student
        student_user_id = complaint.get('user_id')
        if student_user_id:
            notifications_collection.insert_one({
                'user_id': student_user_id,
                'complaint_id': complaint.get('complaint_id'),
                'title': f"Complaint Assigned: {complaint.get('complaint_id')}",
                'message': f"Your complaint '{complaint.get('title')}' was assigned to {target_department} ({target_assigned_to or 'Department Team'}).",
                'is_read': False,
                'created_at': now_iso
            })

        updated = complaints_collection.find_one({'_id': complaint['_id']})
        return jsonify({
            'message': 'Complaint assigned successfully',
            'complaint': serialize_doc(updated)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/complaints/<id>/status', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_complaint_status(id):
    """
    Update complaint status with an optional note (Admin only).
    Body: {status, note}
    """
    try:
        claims = get_jwt()
        admin_name = claims.get('name', 'Admin')

        complaint = find_complaint(id)
        if not complaint:
            return jsonify({'error': 'Not Found', 'message': 'Complaint not found'}), 404

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Validation Error', 'message': 'JSON payload is required'}), 400

        new_status = data.get('status', '').strip()
        note = data.get('note', '').strip()

        if not new_status:
            return jsonify({'error': 'Validation Error', 'message': 'Status is required'}), 400

        if new_status not in ALL_STATUSES:
            return jsonify({'error': 'Validation Error', 'message': f'Invalid status. Must be one of: {ALL_STATUSES}'}), 400

        now_iso = datetime.utcnow().isoformat()
        history_entry = {
            'status': new_status,
            'changed_by': admin_name,
            'timestamp': now_iso,
            'note': note or f'Status updated to {new_status}'
        }

        update_fields = {
            'status': new_status,
            'updated_at': now_iso
        }
        if new_status in ('Resolved', 'Closed'):
            update_fields['resolved_at'] = now_iso
        if note:
            update_fields['resolution_note'] = note

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
                'message': f"Your complaint '{complaint.get('title')}' status changed to '{new_status}'." + (f" Note: {note}" if note else ""),
                'is_read': False,
                'created_at': now_iso
            })

        updated = complaints_collection.find_one({'_id': complaint['_id']})
        return jsonify({
            'message': 'Status updated successfully',
            'complaint': serialize_doc(updated)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/complaints/<id>/resolve', methods=['PUT'])
@jwt_required()
@role_required('admin')
def resolve_complaint(id):
    """
    Mark complaint as Resolved with resolution notes (Admin only).
    Body: {resolution_note}
    """
    try:
        claims = get_jwt()
        admin_name = claims.get('name', 'Admin')

        complaint = find_complaint(id)
        if not complaint:
            return jsonify({'error': 'Not Found', 'message': 'Complaint not found'}), 404

        data = request.get_json(silent=True) or {}
        resolution_note = data.get('resolution_note', '').strip()

        if not resolution_note:
            return jsonify({'error': 'Validation Error', 'message': 'Resolution note is required'}), 400

        now_iso = datetime.utcnow().isoformat()
        history_entry = {
            'status': 'Resolved',
            'changed_by': admin_name,
            'timestamp': now_iso,
            'note': f"Resolved: {resolution_note}"
        }

        update_data = {
            'status': 'Resolved',
            'resolution_note': resolution_note,
            'resolved_at': now_iso,
            'updated_at': now_iso
        }

        complaints_collection.update_one(
            {'_id': complaint['_id']},
            {
                '$set': update_data,
                '$push': {'status_history': history_entry}
            }
        )

        # Notify student
        student_user_id = complaint.get('user_id')
        if student_user_id:
            notifications_collection.insert_one({
                'user_id': student_user_id,
                'complaint_id': complaint.get('complaint_id'),
                'title': f"Complaint Resolved: {complaint.get('complaint_id')}",
                'message': f"Your complaint '{complaint.get('title')}' has been resolved. Note: {resolution_note}",
                'is_read': False,
                'created_at': now_iso
            })

        updated = complaints_collection.find_one({'_id': complaint['_id']})
        return jsonify({
            'message': 'Complaint resolved successfully',
            'complaint': serialize_doc(updated)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_admin_dashboard_stats():
    """
    Return comprehensive admin statistics:
    - total_complaints, open_complaints, resolved_complaints
    - by_status: {Submitted: N, 'Under Review': N, ...}
    - by_category: {Electrical: N, ...}
    - by_priority: {Low: N, Medium: N, High: N, Critical: N}
    - recent_complaints: last 5
    - resolution_time_avg (days)
    """
    try:
        total_complaints = complaints_collection.count_documents({})
        open_complaints = complaints_collection.count_documents(
            {'status': {'$in': ['Submitted', 'Under Review', 'In Progress']}}
        )
        resolved_complaints = complaints_collection.count_documents(
            {'status': {'$in': ['Resolved', 'Closed']}}
        )

        # by_status
        by_status = {status: 0 for status in ALL_STATUSES}
        for doc in complaints_collection.aggregate([
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]):
            if doc['_id']:
                by_status[doc['_id']] = doc['count']

        # by_category
        by_category = {cat: 0 for cat in classifier.categories}
        for doc in complaints_collection.aggregate([
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}}
        ]):
            if doc['_id']:
                by_category[doc['_id']] = doc['count']

        # by_priority
        by_priority = {prio: 0 for prio in ALL_PRIORITIES}
        for doc in complaints_collection.aggregate([
            {'$group': {'_id': '$priority', 'count': {'$sum': 1}}}
        ]):
            if doc['_id']:
                by_priority[doc['_id']] = doc['count']

        # recent 5 complaints
        recent_cursor = complaints_collection.find({}).sort('created_at', -1).limit(5)
        recent_complaints = serialize_docs(list(recent_cursor))

        # resolution_time_avg (days)
        resolved_docs = complaints_collection.find(
            {'status': {'$in': ['Resolved', 'Closed']}, 'resolved_at': {'$exists': True, '$ne': None}},
            {'created_at': 1, 'resolved_at': 1}
        )

        durations_days = []
        for r in resolved_docs:
            try:
                c_at = r.get('created_at')
                r_at = r.get('resolved_at')
                if c_at and r_at:
                    dt_created = datetime.fromisoformat(c_at.replace('Z', '+00:00')) if isinstance(c_at, str) else c_at
                    dt_resolved = datetime.fromisoformat(r_at.replace('Z', '+00:00')) if isinstance(r_at, str) else r_at
                    diff_seconds = (dt_resolved - dt_created).total_seconds()
                    if diff_seconds >= 0:
                        durations_days.append(diff_seconds / 86400.0)
            except Exception:
                continue

        resolution_time_avg = round(float(sum(durations_days) / len(durations_days)), 2) if durations_days else 0.0

        return jsonify({
            'total_complaints': total_complaints,
            'open_complaints': open_complaints,
            'resolved_complaints': resolved_complaints,
            'by_status': by_status,
            'by_category': by_category,
            'by_priority': by_priority,
            'recent_complaints': recent_complaints,
            'resolution_time_avg': resolution_time_avg
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_students_list():
    """
    Return all students list (Admin only).
    Optional query param: role (defaults to 'student', can be 'all')
    """
    try:
        role_filter = request.args.get('role', 'student').strip().lower()
        query = {}
        if role_filter != 'all':
            query['role'] = role_filter

        users_cursor = users_collection.find(query, {'password': 0}).sort('created_at', -1)
        users_list = list(users_cursor)

        return jsonify({
            'users': serialize_docs(users_list),
            'total': len(users_list)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500
