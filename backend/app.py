from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employees.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
CORS(app)
db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), default="")
    department = db.Column(db.String(80), nullable=False)
    salary = db.Column(db.Float, nullable=False, default=0)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    attendance_date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Present")
    __table_args__ = (db.UniqueConstraint("employee_id", "attendance_date"),)

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    start_date = db.Column(db.String(10), nullable=False)
    end_date = db.Column(db.String(10), nullable=False)
    reason = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")

def employee_json(e):
    return {"id": e.id, "employee_code": e.employee_code, "name": e.name,
            "email": e.email, "phone": e.phone, "department": e.department, "salary": e.salary}

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-Admin-Auth") != "employee-admin-session":
            return jsonify({"error": "Please log in as admin."}), 401
        return fn(*args, **kwargs)
    return wrapper

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.post("/api/login")
def login():
    data = request.get_json() or {}
    admin = Admin.query.filter_by(username=data.get("username", "")).first()
    if admin and check_password_hash(admin.password_hash, data.get("password", "")):
        return jsonify({"success": True, "username": admin.username, "token": "employee-admin-session"})
    return jsonify({"error": "Invalid username or password"}), 401

@app.get("/api/employees")
@login_required
def get_employees():
    q = request.args.get("search", "").strip()
    query = Employee.query
    if q:
        query = query.filter(db.or_(Employee.name.ilike(f"%{q}%"), Employee.department.ilike(f"%{q}%")))
    return jsonify([employee_json(e) for e in query.order_by(Employee.id.desc()).all()])

@app.post("/api/employees")
@login_required
def add_employee():
    data = request.get_json() or {}
    required = ["employee_code", "name", "email", "department"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "Employee ID, name, email and department are required."}), 400
    try:
        e = Employee(employee_code=data["employee_code"].strip(), name=data["name"].strip(),
                     email=data["email"].strip(), phone=data.get("phone", "").strip(),
                     department=data["department"].strip(), salary=float(data.get("salary") or 0))
        db.session.add(e); db.session.commit()
        return jsonify(employee_json(e)), 201
    except (ValueError, Exception) as ex:
        db.session.rollback()
        return jsonify({"error": "Could not add employee. Check that employee ID and email are unique and salary is numeric."}), 400

@app.put("/api/employees/<int:employee_id>")
@login_required
def update_employee(employee_id):
    e = db.session.get(Employee, employee_id)
    if not e: return jsonify({"error": "Employee not found"}), 404
    data = request.get_json() or {}
    try:
        for field in ["employee_code", "name", "email", "phone", "department"]:
            if field in data: setattr(e, field, data[field].strip())
        if "salary" in data: e.salary = float(data["salary"] or 0)
        db.session.commit()
        return jsonify(employee_json(e))
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Update failed. Check duplicate ID/email and salary."}), 400

@app.delete("/api/employees/<int:employee_id>")
@login_required
def delete_employee(employee_id):
    e = db.session.get(Employee, employee_id)
    if not e: return jsonify({"error": "Employee not found"}), 404
    Attendance.query.filter_by(employee_id=e.id).delete()
    LeaveRequest.query.filter_by(employee_id=e.id).delete()
    db.session.delete(e); db.session.commit()
    return jsonify({"success": True})

@app.get("/api/attendance")
@login_required
def get_attendance():
    day = request.args.get("date", date.today().isoformat())
    rows = db.session.query(Attendance, Employee).join(Employee).filter(Attendance.attendance_date == day).all()
    return jsonify([{"id": a.id, "employee_id": e.id, "employee_code": e.employee_code,
                     "name": e.name, "department": e.department, "date": a.attendance_date, "status": a.status}
                    for a, e in rows])

@app.post("/api/attendance")
@login_required
def save_attendance():
    data = request.get_json() or {}
    if not data.get("employee_id"): return jsonify({"error": "Employee is required"}), 400
    day = data.get("date", date.today().isoformat())
    status = data.get("status", "Present")
    if status not in ["Present", "Absent", "Late", "On Leave"]:
        return jsonify({"error": "Invalid attendance status"}), 400
    a = Attendance.query.filter_by(employee_id=data["employee_id"], attendance_date=day).first()
    if a: a.status = status
    else: a = Attendance(employee_id=data["employee_id"], attendance_date=day, status=status); db.session.add(a)
    db.session.commit()
    return jsonify({"success": True})

@app.get("/api/leaves")
@login_required
def get_leaves():
    rows = db.session.query(LeaveRequest, Employee).join(Employee).order_by(LeaveRequest.id.desc()).all()
    return jsonify([{"id": l.id, "employee_id": e.id, "employee_name": e.name,
                     "employee_code": e.employee_code, "start_date": l.start_date,
                     "end_date": l.end_date, "reason": l.reason, "status": l.status} for l, e in rows])

@app.post("/api/leaves")
@login_required
def create_leave():
    data = request.get_json() or {}
    required = ["employee_id", "start_date", "end_date", "reason"]
    if any(not data.get(k) for k in required): return jsonify({"error": "Complete all leave fields"}), 400
    l = LeaveRequest(employee_id=data["employee_id"], start_date=data["start_date"],
                     end_date=data["end_date"], reason=data["reason"], status="Pending")
    db.session.add(l); db.session.commit()
    return jsonify({"success": True, "id": l.id}), 201

@app.patch("/api/leaves/<int:leave_id>")
@login_required
def update_leave(leave_id):
    l = db.session.get(LeaveRequest, leave_id)
    if not l: return jsonify({"error": "Leave request not found"}), 404
    status = (request.get_json() or {}).get("status")
    if status not in ["Approved", "Rejected", "Pending"]:
        return jsonify({"error": "Invalid leave status"}), 400
    l.status = status; db.session.commit()
    return jsonify({"success": True})

@app.get("/api/dashboard")
@login_required
def dashboard():
    today = date.today().isoformat()
    total = Employee.query.count()
    departments = db.session.query(Employee.department).distinct().count()
    present = Attendance.query.filter_by(attendance_date=today, status="Present").count()
    pending = LeaveRequest.query.filter_by(status="Pending").count()
    dept_rows = db.session.query(Employee.department, db.func.count(Employee.id)).group_by(Employee.department).all()
    return jsonify({"total_employees": total, "total_departments": departments,
                    "present_today": present, "pending_leaves": pending,
                    "department_data": [{"department": d, "count": c} for d, c in dept_rows]})

def initialize():
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username="admin").first():
            db.session.add(Admin(username="admin", password_hash=generate_password_hash("admin123")))
            db.session.commit()
        if Employee.query.count() == 0:
            demo = [
                Employee(employee_code="EMP001", name="Aarav Sharma", email="aarav@example.com", phone="9876543210", department="Engineering", salary=65000),
                Employee(employee_code="EMP002", name="Diya Patel", email="diya@example.com", phone="9876543211", department="Human Resources", salary=52000),
                Employee(employee_code="EMP003", name="Kabir Singh", email="kabir@example.com", phone="9876543212", department="Sales", salary=48000),
                Employee(employee_code="EMP004", name="Meera Das", email="meera@example.com", phone="9876543213", department="Engineering", salary=72000),
            ]
            db.session.add_all(demo); db.session.commit()

if __name__ == "__main__":
    initialize()
    app.run(debug=True, port=5000)
