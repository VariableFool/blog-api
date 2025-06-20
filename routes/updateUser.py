from flask import request, jsonify
from config import get_db_connection


def build_update_query(userData, user_id):
    # Начинаем запрос
    sql = "UPDATE users SET "
    values = []

    updates = []
    if "status" in userData:
        updates.append("status = %s")
        values.append(userData["status"])
    if "nickname" in userData:
        updates.append("nickname = %s")
        values.append(userData["nickname"])
    if "bio" in userData:
        updates.append("bio = %s")
        values.append(userData["bio"])

    if not updates:
        return None, None

    # Соединяем обновления и завершаем запрос
    sql += ", ".join(updates)
    sql += " WHERE id = %s"
    values.append(user_id)

    return sql, values


def updateUser(current_user, user_id):
    if int(current_user) != user_id:
        return jsonify({"message": "У вас нет прав на изменение этих данных"}), 400

    if not request.is_json:
        return jsonify({"message": "Некорректные данные"}), 400

    userData = request.get_json()

    sql = "UPDATE users SET "
    values = []
    updates = []

    if "status" in userData:
        updates.append("status = %s")
        values.append(userData["status"])
    if "nickname" in userData:
        updates.append("nickname = %s")
        values.append(userData["nickname"])
    if "bio" in userData:
        updates.append("bio = %s")
        values.append(userData["bio"])

    if not updates:
        return jsonify({"message": "Некорректные данные"}), 400

    sql += ", ".join(updates)
    sql += " WHERE id = %s"

    sql, values = build_update_query(userData, int(current_user))

    try:
        if sql and values:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                connection.commit()
                return jsonify({"message": "Данные успешно сохранены"}), 201
        else:
            return jsonify({"message": "Нет данных для обновления"}), 400

    except Exception as e:
        connection.rollback()
        return jsonify({"message": "Что-то пошло не так...", "detail": str(e)}), 400

    finally:
        if connection.open:
            connection.close()
