from flask import request, jsonify
from routes.customvalidator import is_valid_data
import bcrypt
import jwt
import time
from config import SECRET_KEY, get_db_connection


def userData(target_user_id):
    token = request.headers.get("Authorization")
    current_user = 0

    if token and token.startswith("Bearer "):
        try:
            token = token[7:]

            data = jwt.decode(
                token, SECRET_KEY, algorithms=["HS256"], options={"require_exp": True}
            )
            current_user = data.get("sub", 0)
        except Exception:
            pass

    self_user_id = int(current_user)
    isOwner = self_user_id == target_user_id

    try:
        full_info_sql = """
                SELECT id, nickname, email, bio, banner_url, status, DATE_FORMAT(created_at, '%%d.%%m.%%Y') as created_at, is_active 
                FROM users 
                WHERE id = %s
            """

        short_info_sql = """
                SELECT id, nickname, bio, banner_url, status, DATE_FORMAT(created_at, '%%d.%%m.%%Y') as created_at, is_active 
                FROM users 
                WHERE id = %s
            """

        sql = full_info_sql if isOwner else short_info_sql

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (target_user_id,))
                user = cursor.fetchone()

        if not user:
            return jsonify({"isError": True, "message": "Неверные данные"}), 401

        return jsonify(
            {
                "isError": False,
                "isOwner": isOwner,
                "user": {
                    "id": user["id"],
                    "nickname": user["nickname"],
                    "bio": user["bio"],
                    "bannerUrl": user["banner_url"],
                    "status": user["status"],
                    "is_active": user["is_active"],
                    "created_at": user["created_at"],
                    **({"email": user["email"]} if isOwner else {}),
                },
            }
        )
    except Exception as e:
        return jsonify({"isError": True, "message": str(e)}), 500


def login():
    auth_data = request.get_json()

    validation = is_valid_data(auth_data)

    if validation["isError"]:
        return jsonify(validation), 400

    email = auth_data["email"]
    password = auth_data["password"]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT id, email, password_hash FROM users WHERE email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

        if not user:
            return jsonify({"isError": True, "message": "Неверные данные"}), 401

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8"),
        ):
            return jsonify({"isError": True, "message": "Неверные данные"}), 401

        current_time = int(time.time())
        token = jwt.encode(
            {
                "sub": str(user["id"]),
                "email": user["email"],
                "iat": current_time,
                "exp": current_time + 3600,
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        return jsonify(
            {
                "isError": False,
                "token": token,
                "exp": current_time + 3600,
                "user_id": user["id"],
                "message": "Пользователь успешно авторизован",
            }
        ), 200

    except jwt.PyJWKError:
        return jsonify({"isError": True, "message": "Ошибка при генерации токена"}), 500

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"isError": True, "message": "Внутренняя ошибка сервера"}), 500


def register():
    reg_data = request.get_json()

    validation = is_valid_data(reg_data)

    if validation["isError"]:
        return jsonify(validation), 400

    if "nickname" not in reg_data:
        return jsonify({"isError": True, "message": "Никнейм обязателен"}), 400

    email = reg_data["email"]
    nickname = reg_data["nickname"]
    password = reg_data["password"]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return jsonify(
                        {
                            "isError": True,
                            "message": "Пользователь с таким email уже существует",
                        }
                    ), 409

                password_hash = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                )

                sql = "INSERT INTO users (email, password_hash, nickname) VALUES (%s, %s, %s)"
                cursor.execute(sql, (email, password_hash.decode("utf-8"), nickname))
                new_user_id = cursor.lastrowid
                conn.commit()

        current_time = int(time.time())
        token = jwt.encode(
            {
                "sub": str(new_user_id),
                "email": email,
                "iat": current_time,
                "exp": current_time + 3600,
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        return jsonify(
            {
                "isError": False,
                "message": "Пользователь успешно зарегестрирован",
                "user_id": new_user_id,
                "token": token,
            }
        ), 201
    except Exception as e:
        return jsonify(
            {"isError": True, "message": "Ошибка при регистрации", "detail": str(e)}
        )
