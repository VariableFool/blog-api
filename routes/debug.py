from flask import request, jsonify

WANTED_HEADERS = {'Content-Type', 'Authorization', 'X-*'}

def debug():
    # Фильтруем заголовки
    filtered_headers = {
        k: v for k, v in request.headers.items()
        if k in WANTED_HEADERS or k.startswith('X-')
    }
    
    # Основные интересующие нас данные
    debug_info = {
        "method": request.method,
        # "content_type": request.content_type,
        "custom_headers": filtered_headers,
        # "query_params": dict(request.args),
        "json_data": request.json,
        # "form_data": dict(request.form)
    }
    
    print("\n=== Важные данные ===")
    for k, v in debug_info.items():
        print(f"{k}: {v}")
    
    return jsonify({
        "status": "success",
        "data": debug_info
    })