from flask import Blueprint, request, jsonify
from app.db.database import db
from app.db.models import User, UserStats

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409

    # Save user with plain text password
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    
    # Initialize empty stats for the new user
    new_stats = UserStats(user_id=username, accuracy=0.0, attempts=0, streak=0)
    db.session.add(new_stats)
    
    db.session.commit()

    return jsonify({"message": "Registration successful", "user_id": username}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = User.query.filter_by(username=username).first()
    
    # Plain text check
    if user and user.password == password:
        return jsonify({"message": "Login successful", "user_id": username}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401