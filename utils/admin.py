from flask import abort
from flask_login import current_user

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Cek apakah user sudah login dan status is_admin nya True
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403) # Forbidden error
            
        return f(*args, **kwargs)
    
    return decorated_function