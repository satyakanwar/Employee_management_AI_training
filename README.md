# PeopleDesk — Employee Management System

A beginner-friendly full-stack Employee Management System built with React, JavaScript, HTML, CSS, Python Flask, and SQLite.

## Features
- Admin login
- Add, view, edit, delete and search employees
- Employee ID, name, email, phone, department and salary
- Daily attendance tracking (Present, Absent, Late, On Leave)
- Create, approve and reject leave requests
- Dashboard metrics and department-wise chart
- Responsive sidebar and mobile layout

## Requirements
- Python 3.9+
- Node.js 18+ and npm

## 1. Start the Flask backend

Open a terminal in the project folder:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

Install dependencies and start Flask:

```bash
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000`. On first run it creates `employees.db`, an admin account and four demo employees.

## 2. Start the React frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (usually `http://localhost:5173`).

## Demo admin login
- Username: `admin`
- Password: `admin123`

## API overview
All endpoints except `/api/login` and `/api/health` require the `X-Admin-Auth` header.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/login` | Admin login |
| GET | `/api/dashboard` | Dashboard metrics |
| GET | `/api/employees?search=` | List/search employees |
| POST | `/api/employees` | Add employee |
| PUT | `/api/employees/:id` | Update employee |
| DELETE | `/api/employees/:id` | Delete employee |
| GET | `/api/attendance?date=YYYY-MM-DD` | Attendance for a date |
| POST | `/api/attendance` | Create/update attendance |
| GET | `/api/leaves` | List leave requests |
| POST | `/api/leaves` | Create leave request |
| PATCH | `/api/leaves/:id` | Update leave status |

## Notes before production use
This is a learning/demo project. The simple frontend token is only a demonstration and is not secure authentication. For production, use server-side sessions or signed expiring JWTs, store secrets in environment variables, enforce role-based authorization, add CSRF protection and rate limiting, validate all inputs, use HTTPS, and never use the demo credentials. Also configure the frontend API URL via an environment variable before deployment.
