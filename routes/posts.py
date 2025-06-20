from flask import jsonify, request
from datetime import datetime
from config import get_db_connection


class DBConnection:
    def __enter__(self):
        self.conn = get_db_connection()
        return self.conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"DB error: {exc_val}")
        self.conn.close()
        return True  # Подавляем исключение (если нужно)


def post_validation(data):
    if not data:
        return jsonify({"message": "Некорректный запрос"}), 400

    if "title" not in data or "content" not in data:
        return jsonify({"message": "Заголовок или текст поста обязательны"}), 400

    title = data.get("title")
    content = data.get("content")

    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 150
    MIN_CONTENT_LENGTH = 50
    MAX_CONTENT_LENGTH = 10000

    if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
        return jsonify(
            {
                "message": f"Длина заголовка должна быть от {MIN_TITLE_LENGTH} до {MAX_TITLE_LENGTH} символов"
            }
        ), 400

    if len(content) < MIN_CONTENT_LENGTH or len(content) > MAX_CONTENT_LENGTH:
        return jsonify(
            {
                "message": f"Длина текста должна быть от {MIN_CONTENT_LENGTH} до {MAX_CONTENT_LENGTH} символов"
            }
        ), 400


def get_posts():
    with DBConnection() as cursor:
        cursor.execute(
            """SELECT 
                    p.id, 
                    DATE_FORMAT(p.created_at, '%d.%m.%Y, %H:%i') AS created_at, 
                    DATE_FORMAT(p.updated_at, '%d.%m.%Y, %H:%i') AS updated_at, 
                    p.title, 
                    p.content, 
                    p.author_id,
                    p.is_pinned,
                    p.is_ad,
                    p.comment_count,
                    u.nickname AS author_nickname
                    FROM posts p 
                    JOIN users u 
                    ON p.author_id = u.id 
                    ORDER BY
                        COALESCE(p.updated_at, p.created_at) DESC;
                    """
        )

        return jsonify({"posts": cursor.fetchall()})


def get_post(post_id):
    if not post_id:
        return jsonify({"message": "Некорректный запрос"}), 400

    try:
        with DBConnection() as cursor:
            cursor.execute(
                """SELECT 
                        p.id, 
                        p.title, 
                        p.content, 
                        DATE_FORMAT(p.created_at, '%%d.%%m.%%Y, %%H:%%i') AS created_at, 
                        DATE_FORMAT(p.updated_at, '%%d.%%m.%%Y, %%H:%%i') AS updated_at, 
                        p.author_id, 
                        p.comment_count,
                        u.nickname AS author_nickname 
                        FROM posts p 
                        JOIN users u 
                        ON p.author_id = u.id 
                        WHERE p.id = %s
                    """,
                (post_id,),
            )
            post = cursor.fetchone()
            if post is None:
                return jsonify({"isError": True, "message": "Пост не найден"}), 404

        return jsonify({"isError": False, "post": post})
    except Exception as e:
        print("FULL ERROR:", str(e))  # Выведет в консоль сервера
        return jsonify({"isError": True, "message": str(e)}), 500


def new_post(current_user):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Некорректный запрос"}), 400

    if data["author_id"] != int(current_user):
        return jsonify({"message": "Нет прав для добавления этого поста"}), 400

    missing_fields = []

    if "author_id" not in data:
        missing_fields.append("id автора")

    if "title" not in data:
        missing_fields.append("заголовок")

    if "content" not in data:
        missing_fields.append("текст")

    if missing_fields:
        field_str = ", ".join(missing_fields)
        return jsonify(
            {
                "message": f"Отсутствуют обязательные поля нового поста: {field_str}",
                "Пример_body": {
                    "title": "Ваш заголовок должен быть тут",
                    "content": "Ваш текст поста должен быть тут",
                },
            }
        ), 400

    MIN_TITLE_LENGTH = 10
    MAX_TITLE_LENGTH = 150
    MIN_CONTENT_LENGTH = 50
    MAX_CONTENT_LENGTH = 10000

    title = data.get("title")
    content = data.get("content")

    if len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
        return jsonify(
            {
                "message": f"Длина заголовка должна быть от {MIN_TITLE_LENGTH} до {MAX_TITLE_LENGTH} символов"
            }
        ), 400

    if len(content) < MIN_CONTENT_LENGTH or len(content) > MAX_CONTENT_LENGTH:
        return jsonify(
            {
                "message": f"Длина текста должна быть от {MIN_CONTENT_LENGTH} до {MAX_CONTENT_LENGTH} символов"
            }
        ), 400

    with DBConnection() as cursor:
        cursor.execute("SELECT nickname FROM users WHERE id = %s", (current_user,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "Пользователь не найден"}), 404

        author_nickname = user["nickname"]

        sql = "INSERT INTO posts (title, content, author_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (data["title"], data["content"], current_user))
        post_id = cursor.lastrowid
        cursor.connection.commit()
        now = datetime.now()

    return jsonify(
        {
            "message": "Пост успешно добавлен",
            "post": {
                "id": post_id,
                "title": data["title"],
                "content": data["content"],
                "author_id": current_user,
                "author_nickname": author_nickname,
                "created_at": now.strftime("%d.%m.%Y, %H:%M"),
            },
        }
    ), 201


def upd_post(current_user, post_id):
    if not current_user or not post_id:
        return jsonify({"status": False, "message": "Некорректный запрос"}), 400

    data = request.get_json()

    invalid_post = post_validation(data)
    if invalid_post:
        return invalid_post

    title = data.get("title")
    content = data.get("content")

    with DBConnection() as cursor:
        cursor.execute(
            "UPDATE posts SET title = %s, content = %s, updated_at = NOW() WHERE id = %s AND author_id = %s;",
            (title, content, post_id, current_user),
        )
        if cursor.rowcount == 0:
            return jsonify(
                {"message": "Пост не найден или у вас нет прав на его удаление"}
            ), 404
        cursor.connection.commit()
        now = datetime.now()

    return jsonify(
        {
            "message": "Пост успешно изменен",
            "updated_at": now.strftime("%d.%m.%Y, %H:%M"),
        }
    )


def del_post(current_user, post_id):
    with DBConnection() as cursor:
        cursor.execute(
            "DELETE FROM posts WHERE id = %s AND author_id = %s;",
            (post_id, current_user),
        )
        if cursor.rowcount == 0:
            return jsonify(
                {"message": "Пост не найден или у вас нет прав на его удаление"}
            ), 404
        cursor.connection.commit()

        return jsonify({"message": "Пост был удален :("})


def toggle_option(current_user, post_id):
    if int(current_user) != 1:
        return jsonify({"message": "У вас нет прав на изменение этих настроек"}), 403

    if not request.is_json:
        return jsonify({"message": "Некорректный запрос: ожидается JSON"}), 400

    data = request.get_json()
    option = data.get("option")
    ALLOWED_OPTIONS = {"is_pinned", "is_ad"}

    if not option or option not in ALLOWED_OPTIONS:
        return jsonify({"message": "Недопустимая опция"}), 400

    with DBConnection() as cursor:
        query = f"SELECT {option} FROM `posts` WHERE id = %s"
        cursor.execute(query, (post_id,))
        current_value = cursor.fetchone()

        new_value = 0 if current_value[option] else 1

        query = f"UPDATE posts SET {option} = %s WHERE id = %s"
        cursor.execute(query, (new_value, post_id))
        cursor.connection.commit()

        return jsonify(
            {
                "message": "Успешно изменено",
                "option": option,
                "new_value": bool(new_value),
                "post_id": post_id,
            }
        )
