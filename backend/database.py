import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config
from utils import serialize_doc, serialize_docs

logger = logging.getLogger(__name__)

# Initialize PyMongo client with a reasonable connection timeout
client = None
db = None

try:
    client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        default_db = client.get_default_database()
        if default_db is not None and default_db.name != 'admin':
            db = default_db
        else:
            db = client['campus_complaints']
    except Exception:
        db = client['campus_complaints']
except Exception as e:
    logger.error(f"Failed to initialize PyMongo client: {e}")
    raise

# Export collections
users_collection = db['users']
complaints_collection = db['complaints']
departments_collection = db['departments']
notifications_collection = db['notifications']

def check_db_connection():
    """Verify if MongoDB is reachable."""
    try:
        client.admin.command('ping')
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as err:
        logger.warning(f"Database ping failed: {err}")
        return False

def init_db():
    """Create essential MongoDB indexes and seed initial departments if necessary."""
    try:
        # Check connectivity first
        if not check_db_connection():
            logger.warning("MongoDB not connected. Skipping index creation until MongoDB is active.")
            return False

        # Users collection indexes: unique email
        users_collection.create_index("email", unique=True)
        users_collection.create_index("role")

        # Complaints collection indexes: unique complaint_id, user_id, status, category, priority
        complaints_collection.create_index("complaint_id", unique=True)
        complaints_collection.create_index("user_id")
        complaints_collection.create_index("status")
        complaints_collection.create_index("category")
        complaints_collection.create_index("priority")
        complaints_collection.create_index("created_at")

        # Departments collection indexes
        departments_collection.create_index("name", unique=True)

        # Notifications collection indexes
        notifications_collection.create_index("user_id")
        notifications_collection.create_index([("user_id", 1), ("is_read", 1)])

        # Seed initial departments if table is empty
        if departments_collection.count_documents({}) == 0:
            initial_departments = [
                {
                    "name": "Electrical",
                    "description": "Power infrastructure, lighting, fans, AC units, switchboards, and electrical appliances",
                    "contact_email": "electrical@campus.edu"
                },
                {
                    "name": "Maintenance",
                    "description": "Plumbing, carpentry, masonry, furniture repair, door and window maintenance",
                    "contact_email": "maintenance@campus.edu"
                },
                {
                    "name": "IT Support",
                    "description": "Campus Wi-Fi, computer labs, student portal, audio-visual systems, and software licenses",
                    "contact_email": "itsupport@campus.edu"
                },
                {
                    "name": "Hostel Administration",
                    "description": "Room allocation, water supply, warden affairs, cleanliness, and hostel discipline",
                    "contact_email": "hostel@campus.edu"
                },
                {
                    "name": "Canteen",
                    "description": "Food quality, hygiene, mess timetable, cafeteria pricing, and cleanliness",
                    "contact_email": "canteen@campus.edu"
                },
                {
                    "name": "Transport",
                    "description": "College bus services, schedules, routes, shuttle transport, and vehicle parking",
                    "contact_email": "transport@campus.edu"
                },
                {
                    "name": "Academic",
                    "description": "Curriculum, timetable clashes, faculty attendance, grade discrepancies, and exams",
                    "contact_email": "academics@campus.edu"
                },
                {
                    "name": "Security",
                    "description": "Campus security guards, CCTV surveillance, gate entry/exit, lost-and-found, and student safety",
                    "contact_email": "security@campus.edu"
                }
            ]
            departments_collection.insert_many(initial_departments)
            logger.info("Default departments seeded successfully into MongoDB.")

        logger.info("MongoDB indexes verified and ready.")
        return True
    except Exception as e:
        logger.error(f"Error during MongoDB initialization: {e}")
        return False
