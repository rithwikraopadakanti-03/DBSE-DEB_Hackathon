# 🎓 Campus Complaint Management System

A full-stack web application for managing campus complaints with ML-powered classification, built with **React.js**, **Python Flask**, and **MongoDB Atlas**.

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 🔐 **Authentication** | JWT-based login/registration with bcrypt password hashing |
| 📝 **Complaint Submission** | Submit complaints with title, description, category, location & priority |
| 🤖 **ML Classification** | AI auto-classifies category (TF-IDF + Logistic Regression) & recommends priority |
| 🏢 **Department Assignment** | Admins assign complaints to departments with staff |
| 📊 **Status Tracking** | Full lifecycle: Submitted → Under Review → In Progress → Resolved → Closed |
| 👨‍💼 **Admin Dashboard** | Filter, assign, update, resolve complaints with stats overview |
| 👨‍🎓 **Student Dashboard** | View personal complaints with real-time status |
| 🗄️ **MongoDB Atlas** | Cloud database for users, complaints, departments, notifications |
| 📱 **Responsive UI** | Works on desktop and mobile |

---

## 📁 Project Structure

```
campus-complaint-system/
├── backend/                    # Python Flask API
│   ├── app.py                  # Main Flask application
│   ├── config.py               # Configuration (env vars)
│   ├── database.py             # MongoDB connection & collections
│   ├── ml_classifier.py        # ML model (TF-IDF + Logistic Regression)
│   ├── utils.py                # Helpers (serialization, auth decorators)
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── .env                    # Your actual env vars (create from example)
│   └── routes/
│       ├── auth.py             # /api/auth/* endpoints
│       ├── complaints.py       # /api/complaints/* endpoints
│       ├── admin.py            # /api/admin/* endpoints
│       └── departments.py      # /api/departments endpoint
│
├── frontend/                   # React.js + Vite
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx             # Root with routing
│       ├── api/axios.js        # Axios instance with interceptors
│       ├── context/AuthContext.jsx  # Auth state management
│       ├── components/
│       │   ├── Navbar.jsx
│       │   └── ProtectedRoute.jsx
│       └── pages/
│           ├── Login.jsx
│           ├── Register.jsx
│           ├── StudentDashboard.jsx
│           ├── SubmitComplaint.jsx
│           ├── ComplaintDetail.jsx
│           └── AdminDashboard.jsx
│
└── README.md
```

---

## ⚙️ Prerequisites

- **Node.js** v18+ and npm — [Download](https://nodejs.org/)
- **Python** 3.9+ — [Download](https://python.org/)
- **MongoDB Atlas** account (free tier) — [Sign up](https://www.mongodb.com/cloud/atlas)

---

## 🗄️ MongoDB Atlas Setup

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and create a **free account**
2. Create a new **Free Tier Cluster** (M0 Sandbox)
3. In **Database Access**: Add a new user with read/write permissions
   - Username: e.g., `campus_admin`
   - Password: Generate a secure password (save it!)
4. In **Network Access**: Click **"Add IP Address"** → **"Allow Access from Anywhere"** (`0.0.0.0/0`)
5. Click **"Connect"** on your cluster → **"Connect your application"**
6. Copy the connection string — it looks like:
   ```
   mongodb+srv://campus_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
7. Replace `<password>` with your actual password and append the database name:
   ```
   mongodb+srv://campus_admin:yourpassword@cluster0.xxxxx.mongodb.net/campus_complaints?retryWrites=true&w=majority
   ```

---

## 🔧 Backend Setup

```bash
# Navigate to backend directory
cd campus-complaint-system/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file from the example
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` with your actual values:
```env
MONGO_URI=mongodb+srv://campus_admin:yourpassword@cluster0.xxxxx.mongodb.net/campus_complaints?retryWrites=true&w=majority
JWT_SECRET_KEY=your-very-long-random-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
```

```bash
# Start the Flask server
python app.py
```

The API will be available at **http://localhost:5000**

✅ Verify it's working: Open http://localhost:5000/api/health — you should see:
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "ml_model": "ready"
}
```

---

## ⚛️ Frontend Setup

```bash
# Open a NEW terminal window
cd campus-complaint-system/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The app will be available at **http://localhost:5173**

---

## 🏃 Running the Complete System

You need **two terminal windows** running simultaneously:

**Terminal 1 — Backend:**
```bash
cd campus-complaint-system/backend
venv\Scripts\activate
python app.py
```

**Terminal 2 — Frontend:**
```bash
cd campus-complaint-system/frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## 👥 Creating Your First Accounts

### Register as Admin
1. Open http://localhost:5173/register
2. Fill in your details
3. Select **Role: Admin**
4. Click Register

### Register as Student
1. Open http://localhost:5173/register
2. Fill in your details
3. Select **Role: Student**, enter your Student ID
4. Click Register

---

## 🤖 ML Classification

The system uses a trained TF-IDF + Logistic Regression model to:
- **Auto-classify** complaints into categories: Electrical, Maintenance, IT Support, Hostel Administration, Canteen, Transport, Academic, Security
- **Recommend priority**: Low, Medium, High, Critical

To use it in the Submit Complaint form:
1. Enter the complaint **Title** and **Description**
2. Click the **"🤖 AI Classify"** button
3. The system will suggest the most likely **Category** (with confidence %) and **Priority**
4. Accept or manually override the suggestions before submitting

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user (JWT required) |

### Complaints
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/complaints` | Submit new complaint | Student |
| GET | `/api/complaints` | List complaints | Any |
| GET | `/api/complaints/:id` | Get complaint details | Any |
| PUT | `/api/complaints/:id/status` | Update status | Admin |
| POST | `/api/complaints/classify` | ML classification | Any |
| GET | `/api/complaints/stats` | Complaint statistics | Admin |

### Admin
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/admin/complaints` | All complaints with filters | Admin |
| PUT | `/api/admin/complaints/:id/assign` | Assign department | Admin |
| PUT | `/api/admin/complaints/:id/resolve` | Resolve complaint | Admin |
| GET | `/api/admin/stats` | Dashboard statistics | Admin |
| GET | `/api/admin/users` | List all students | Admin |

### Departments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/departments` | List all departments |

---

## 🛡️ Security Features

- **Password Hashing**: bcrypt with salt rounds
- **JWT Tokens**: 24-hour expiry, signed with secret key
- **Role-Based Access**: Student and Admin routes protected separately
- **CORS**: Only accepts requests from `http://localhost:5173`
- **Environment Variables**: Credentials never hardcoded

---

## 🎨 Complaint Status Flow

```
Submitted → Under Review → In Progress → Resolved → Closed
```

| Status | Color | Who Sets It |
|--------|-------|-------------|
| Submitted | 🔵 Blue | Auto (on creation) |
| Under Review | 🟠 Orange | Admin (on department assign) |
| In Progress | 🟣 Purple | Admin |
| Resolved | 🟢 Green | Admin |
| Closed | ⚫ Gray | Admin |

---

## 🏢 Departments

The system comes pre-seeded with these departments:
- ⚡ Electrical
- 🔧 Maintenance
- 💻 IT Support
- 🏠 Hostel Administration
- 🍽️ Canteen
- 🚌 Transport
- 📚 Academic
- 🔒 Security

---

## 🐛 Troubleshooting

### "MongoDB connection failed"
- Check your `MONGO_URI` in `.env` is correct
- Ensure your IP is whitelisted in MongoDB Atlas Network Access
- Verify the database user has read/write permissions

### "Module not found" (Python)
```bash
# Make sure virtual environment is activated
venv\Scripts\activate
pip install -r requirements.txt
```

### "npm install" fails
```bash
# Delete node_modules and try again
rm -rf node_modules package-lock.json
npm install
```

### CORS errors in browser
- Ensure Flask is running on port 5000
- Ensure React dev server is on port 5173
- Check that CORS is configured in `app.py`

### JWT token errors
- Clear browser localStorage: `localStorage.clear()` in browser console
- Re-login to get a fresh token

---

## 📝 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, React Router 6, Axios |
| Backend | Python Flask 3.0, Flask-JWT-Extended, Flask-CORS |
| Database | MongoDB Atlas, PyMongo 4.6 |
| ML | scikit-learn (TF-IDF + Logistic Regression) |
| Auth | bcrypt, JSON Web Tokens (JWT) |
| Styling | Custom CSS (no frameworks) |

---

## 📜 License

MIT License — Free for educational and personal use.
