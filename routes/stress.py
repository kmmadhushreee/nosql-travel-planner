
from flask import Blueprint, request, jsonify, session
from models import get_db
import datetime

stress_bp = Blueprint('stress', __name__)

@stress_bp.route('/api/stress_log', methods=['POST'])
def stress_log():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
        
    db = get_db()
    log_entry = {
        'user_id': session.get('user_id'), # May be None if not logged in
        'click_count': data.get('click_count', 0),
        'time_spent_sec': data.get('time_spent_sec', 0),
        'repeated_searches_count': data.get('repeated_searches_count', 0),
        'timestamp': datetime.datetime.utcnow()
    }
    
    db.stress_logs.insert_one(log_entry)
    
    # Simple logic to determine if high stress (example heuristic)
    is_stressed = False
    if log_entry['click_count'] > 20 or log_entry['repeated_searches_count'] > 3:
        is_stressed = True
        
    return jsonify({'status': 'success', 'stressed': is_stressed})
