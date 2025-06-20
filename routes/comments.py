from flask import jsonify, request
from config import get_db_connection


def getComments(post_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT 
                    c.id, 
                    c.post_id, 
                    c.user_id, 
                    u.nickname, 
                    c.content,
                    c.parent_id,
                    DATE_FORMAT(c.created_at, '%%d.%%m.%%Y в %%H:%%i') AS created_at 
                    FROM comments c 
                    JOIN users u 
                    ON c.user_id = u.id 
                    WHERE c.post_id = %s;""",
                    (post_id),
                )
                comments = cursor.fetchall()

                if not comments:
                    return jsonify(
                        {"message": "Комментарии не найдены", "comments": None}
                    ), 404

                return jsonify(
                    {"message": "Комментарии успешно получены", "comments": comments}
                )

    except Exception as e:
        return jsonify(
            {
                "message": "Ошибка при получении комментариев, подробности в консоли",
                "detail": str(e),
            }
        )


def addComment(current_user, post_id):
    data = request.get_data()

    if not data:
        return jsonify({"message": "Некорректный запрос"}), 400

    data = request.get_json()

    if "post_id" not in data or "user_id" not in data or "content" not in data:
        return jsonify({"message": "Отсутствуют обязательные поля"}), 400

    if len(data["content"]) < 10:
        return jsonify({"message": "Комментарий должен быть больше 5 символов"}), 400

    user_id = current_user
    post_id = data["post_id"]
    content = data["content"]
    parent_id = data.get("parent_id")

    sql = "INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)"
    values = [post_id, user_id, content]

    if parent_id is not None:
        sql = "INSERT INTO comments (post_id, user_id, content, parent_id) VALUES (%s, %s, %s, %s)"
        values.append(parent_id)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                comment_id = cursor.lastrowid
                cursor.execute(
                    "UPDATE posts SET comment_count = comment_count + 1 WHERE id = %s",
                    (post_id,),
                )
                cursor.connection.commit()

                cursor.execute(
                    """SELECT 
                    c.id,
                    c.post_id,
                    c.parent_id,
                    c.user_id,
                    u.nickname,
                    c.content, 
                    DATE_FORMAT(c.created_at, '%%d.%%m.%%Y в %%H:%%i') AS created_at 
                    FROM comments c 
                    JOIN users u 
                    ON c.user_id = u.id 
                    WHERE c.id = %s;""",
                    (comment_id,),
                )
                comment = cursor.fetchone()

                if comment["parent_id"] is not None:
                    return jsonify(
                        {
                            "message": "Комментарий успешно добавлен",
                            "commentsReplies": comment,
                        }
                    )

                return jsonify(
                    {"message": "Комментарий успешно добавлен", "comment": comment}
                )

    except Exception as e:
        print({"Ошибка": str(e)})
        return jsonify(
            {
                "message": "Ошибка при добвавлении комментария",
                "detail": f"Ошибка при добавлении комментария: {str(e)}",
            }
        ), 500


def delComment(current_user, comment_id):
    if not current_user or not comment_id:
        return jsonify({"message": "Некорректный запрос"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT post_id FROM comments WHERE id = %s", (comment_id,)
                )
                post_id = cursor.fetchone()["post_id"]

                cursor.execute(
                    "DELETE FROM comments WHERE id = %s AND user_id = %s",
                    (
                        comment_id,
                        current_user,
                    ),
                )
                if cursor.rowcount == 0:
                    return jsonify(
                        {"message": "У вас нет прав на удаление этого комментария"}
                    ), 403

                cursor.execute(
                    "UPDATE posts SET comment_count = GREATEST(0, comment_count - 1) WHERE id = %s",
                    (post_id,),
                )

                cursor.connection.commit()
                return jsonify({"message": "Комментарий успешно удален"}), 200

    except Exception as e:
        return jsonify(
            {
                "message": "Ошибка при удалении комментария, подробности в консоли",
                "detail": f"{str(e)}",
            }
        ), 500
