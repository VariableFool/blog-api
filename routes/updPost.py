from flask import request, jsonify
from config import get_db_connection
import logging


def updPost(current_user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Нет данных"}), 400

        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            return jsonify({"message": "Некорректный запрос"})

        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "INSERT INTO posts (title, content, author_id) VALUES (%s, %s, %s)"
            cursor.execute(sql, (title, content, current_user))
            connection.commit()

        return jsonify({"message": "Пост успешно добавлен"}), 201

    except Exception as e:
        return jsonify({"message": "Ошибка сервера", "error": str(e)}), 500

    finally:
        if "connection" in locals() and connection.open:
            connection.close()


def delete_post(current_user):
    connection = None
    try:
        post_data = request.get_json()

        if not current_user or not post_data or "id" not in post_data:
            return jsonify({"message": "Некорректный запрос"}), 400

        post_id = post_data["id"]
        connection = get_db_connection()

        with connection.cursor() as cursor:
            sql = "DELETE FROM posts WHERE id = %s AND author_id = %s"
            rows_deleted = cursor.rowcount
            cursor.execute(
                sql,
                (
                    post_id,
                    current_user,
                ),
            )
            connection.commit()

        if rows_deleted == 0:
            return jsonify({"message": "Пост не найден или нет прав"}), 404

        return jsonify(
            {"message": "Пост успешно удален", "title": post_data["title"]}
        ), 200

    except Exception as e:
        logging.error(f"Ошибка при удалении поста {post_id}: {e}")
        if connection:
            connection.rollback()
        return jsonify({"message": "Что-то пошло не так"}), 500

    finally:
        if connection:
            connection.close()
