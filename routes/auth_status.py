from flask import jsonify


def auth_status(current_user):
    return jsonify({"isLoggedIn": True, "user": {"id": int(current_user)}})
