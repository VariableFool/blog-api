import re


def is_valid_email(email):
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    return re.match(email_regex, email) is not None


def is_valid_data(data):
    if not data:
        return {"isError": True, "message": "Некорректный запрос"}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"isError": True, "message": "Email и пароль обязательны"}

    if not is_valid_email(email):
        return {"isError": True, "message": "Некорректный email"}

    return {"isError": False}
