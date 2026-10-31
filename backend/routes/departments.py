from flask import Blueprint, jsonify, request
from database import departments_collection, complaints_collection
from utils import serialize_doc, serialize_docs

departments_bp = Blueprint('departments', __name__)

DEFAULT_DEPARTMENTS = [
    {'name': 'Electrical', 'description': 'Electrical infrastructure, lighting, fans, ACs, and power outlets'},
    {'name': 'Maintenance', 'description': 'Civil repairs, plumbing, carpentry, doors, windows, and sanitation'},
    {'name': 'IT Support', 'description': 'Wi-Fi network, student ERP portal, computer labs, and smart classrooms'},
    {'name': 'Hostel Administration', 'description': 'Hostel facilities, room allotments, hygiene, and warden affairs'},
    {'name': 'Canteen', 'description': 'Food safety, cafeteria hygiene, meal pricing, and dining facilities'},
    {'name': 'Transport', 'description': 'Campus shuttle, college buses, bus stops, and vehicle parking'},
    {'name': 'Academic', 'description': 'Curriculum scheduling, timetable clashes, faculty lectures, and grading'},
    {'name': 'Security', 'description': 'Campus surveillance, security guards, gate entry/exit, and emergency alarms'}
]

@departments_bp.route('', methods=['GET'])
def get_departments():
    """
    Get list of departments with aggregate complaint statistics.
    Returns: [{name, description, total_complaints, open_complaints, resolved_complaints}, ...]
    """
    try:
        dept_docs = list(departments_collection.find({}).sort('name', 1))

        # Fallback to standard defaults if database collection is empty
        if not dept_docs:
            dept_docs = DEFAULT_DEPARTMENTS

        # Compute complaint counts per department/category
        dept_stats = []
        for dept in dept_docs:
            name = dept.get('name')
            
            # Match by department name or category name
            dept_query = {'$or': [{'department': name}, {'category': name}]}
            
            total_count = complaints_collection.count_documents(dept_query)
            open_count = complaints_collection.count_documents({
                '$and': [
                    dept_query,
                    {'status': {'$in': ['Submitted', 'Under Review', 'In Progress']}}
                ]
            })
            resolved_count = complaints_collection.count_documents({
                '$and': [
                    dept_query,
                    {'status': {'$in': ['Resolved', 'Closed']}}
                ]
            })

            dept_item = serialize_doc(dept) if isinstance(dept, dict) else {'name': name}
            dept_item['total_complaints'] = total_count
            dept_item['open_complaints'] = open_count
            dept_item['resolved_complaints'] = resolved_count
            dept_stats.append(dept_item)

        return jsonify({
            'departments': dept_stats,
            'total': len(dept_stats)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server Error', 'message': str(e)}), 500
