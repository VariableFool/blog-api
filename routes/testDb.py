from flask import jsonify, render_template
from config import get_db_connection
from pymysql import MySQLError

def testdb():
    try:
        # Устанавливаем соединение
        connection = get_db_connection()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS test_value")
                result = cursor.fetchone()
                if result['test_value'] == 1:
                    return render_template("result.html", value='ok')
                print('\033[92mDataBase OK!\033[0m')
        finally:
            connection.close()
            
    except MySQLError:
        print('\033[91mDataBase ERROR!\033[0m')
        return render_template("result.html", value='error')
        
    except Exception as e:
        print('\033[91mDataBase ERROR!\033[0m')
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Неожиданная ошибка: {str(e)}"
        }), 500