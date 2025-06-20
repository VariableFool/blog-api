from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import jwt
import os
from functools import wraps
from dotenv import load_dotenv
from config import SECRET_KEY, get_db_connection
from flask_caching import Cache
from routes.debug import debug
from routes.testDb import testdb
from routes.auth import userData, login, register
from routes.updateUser import updateUser
from routes.auth_status import auth_status
from routes.comments import getComments, addComment, delComment
from routes.posts import (
    get_posts,
    get_post,
    new_post,
    upd_post,
    del_post,
    toggle_option,
)
from pathlib import Path

env_path = Path(".") / ".env"

load_dotenv(dotenv_path=env_path)

cache = Cache(config={"CACHE_TYPE": "SimpleCache"})

application = Flask(__name__)
application.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
application.config["UPLOAD_FOLDER"] = "uploads"
application.config["BANNER_UPLOAD_FOLDER"] = "uploads/userbanner"
application.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/gif"}
os.makedirs(application.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(application.config["BANNER_UPLOAD_FOLDER"], exist_ok=True)

CORS(application, resources={r"/*": {"origins": ["https://blog.gghub.ru"]}})


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in application.config["ALLOWED_EXTENSIONS"]
    )


cache.init_app(application)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return {"isError": True, "message": "Токен отсутствует"}, 401

        try:
            if token.startswith("Bearer "):
                token = token[7:]
            data = jwt.decode(
                token, SECRET_KEY, algorithms=["HS256"], options={"require_exp": True}
            )
            current_user = data["sub"]
        except jwt.ExpiredSignatureError:
            return {"isError": True, "message": "Токен просрочен"}, 401
        except jwt.InvalidTokenError as e:
            return {
                "isError": True,
                "message": "Невалидный токен",
                "detail": str(e),
            }, 401

        return f(current_user, *args, **kwargs)

    return decorated


@application.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.mimetype not in ALLOWED_MIMETYPES:
        return jsonify({"error": "Invalid file content type"}), 400

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(application.config["UPLOAD_FOLDER"], filename))
        file_url = f"{os.getenv('API_URL')}/uploads/{filename}"
        return jsonify({"url": file_url}), 200

    return jsonify({"error": "Invalid file type"}), 400


@application.route("/upload/userbanner/<int:user_id>", methods=["POST"])
@token_required
def upload_banner(current_user, user_id):
    if int(current_user) != user_id:
        return jsonify({"message": "У вас нет прав на изменение этих данных"}), 400

    if not user_id or "file" not in request.files:
        return jsonify({"message": "Некорректный запрос"}), 400

    file = request.files["file"]

    if file.mimetype not in ALLOWED_MIMETYPES:
        return jsonify({"message": "Неправильный формат файла"}), 400

    if file.filename == "":
        return jsonify({"message": "Неправильный формат файла"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(application.config["BANNER_UPLOAD_FOLDER"], filename))
        file_url = f"{os.getenv('API_URL')}/uploads/userbanner/{filename}"

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET banner_url = %s WHERE id = %s",
                    (file_url, current_user),
                )
                cursor.connection.commit()

                return jsonify(
                    {"message": "Баннер успешно изменен", "bannerUrl": file_url}
                ), 200

    return jsonify({"message": "Некорректный запрос"}), 400


@application.route("/uploads/<filename>")
def serve_uploaded_file(filename):
    return send_from_directory(application.config["UPLOAD_FOLDER"], filename)


@application.route("/uploads/userbanner/<filename>")
def serve_uploaded_banner(filename):
    return send_from_directory(application.config["BANNER_UPLOAD_FOLDER"], filename)


@application.route("/debug", methods=["POST"])
@token_required
def apiDebug():
    return debug()


@application.route("/testapi", methods=["GET"])
@token_required
def apiTest():
    return testdb()


@application.route("/status", methods=["GET"])
@token_required
def userStatus(current_user):
    return auth_status(current_user)


@application.route("/login", methods=["POST"])
def userLogin():
    return login()


@application.route("/register", methods=["POST"])
def userRegistration():
    return register()


@application.route("/profile/<int:target_user_id>", methods=["GET"])
def getUser(target_user_id):
    return userData(target_user_id)


@application.route("/profile/<int:user_id>", methods=["PATCH"])
@token_required
def updateUserInfo(current_user, user_id):
    return updateUser(current_user, user_id)


@application.route("/posts", methods=["GET"])  # РАБОТАЕТ
@cache.cached(timeout=60)
def get_all_post():
    return get_posts()


@application.route("/posts/<int:post_id>", methods=["GET"])  # РАБОТАЕТ
def get_single_post(post_id):
    return get_post(post_id)


@application.route("/posts/create", methods=["POST"])  # РАБОТАЕТ
@token_required
def create_new_post(current_user):
    return new_post(current_user)


@application.route("/posts/<int:post_id>", methods=["PATCH", "DELETE"])  # МЫ ТУТ
@token_required
def post_detail(current_user, post_id):
    if request.method == "PATCH":
        return upd_post(current_user, post_id)
    elif request.method == "DELETE":
        return del_post(current_user, post_id)


@application.route("/posts/option/<int:post_id>", methods=["PATCH"])
@token_required
def toggle_post_option(current_user, post_id):
    return toggle_option(current_user, post_id)


@application.route("/posts/<int:post_id>/comments", methods=["GET"])
def getPostComments(post_id):
    return getComments(post_id)


@application.route("/posts/<int:post_id>/comments", methods=["POST"])
@token_required
def addCommentToPost(current_user, post_id):
    return addComment(current_user, post_id)


@application.route("/comments/<int:comment_id>", methods=["DELETE"])
@token_required
def delPostComment(current_user, comment_id):
    return delComment(current_user, comment_id)


if __name__ == "__main__":
    application.run(debug=False)
