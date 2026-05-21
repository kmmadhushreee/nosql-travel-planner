
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import get_db
from datetime import datetime
import string
import random
from bson.objectid import ObjectId

booking_bp = Blueprint('booking', __name__)

def generate_ticket_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Confidence Score Logic
def calculate_confidence(train_id, journey_date):
    db = get_db()
    
    # 1. Seat Availability (Weight: 50%)
    MAX_SEATS = 50
    current_bookings = db.bookings.count_documents({'train_id': train_id, 'journey_date': journey_date})
    availability_ratio = max(0, (MAX_SEATS - current_bookings) / MAX_SEATS)
    
    # 2. Server Load / Traffic (Weight: 30%)
    # Simulating load between 0.1 (low) and 0.9 (high)
    # In reality, this would check system metrics
    current_load = random.uniform(0.1, 0.6) 
    load_factor = 1.0 - current_load # Higher load = Lower confidence
    
    # 3. Historical Success Rate (Weight: 20%)
    # Mocking historical data for demo effects
    historical_success = 0.95 
    
    # Weighted Score
    score = (availability_ratio * 0.5) + (load_factor * 0.3) + (historical_success * 0.2)
    score_percent = round(score * 100)
    
    return {
        'score': score_percent,
        'availability': round(availability_ratio * 100),
        'server_load': round(current_load * 100),
        'history': round(historical_success * 100)
    }

@booking_bp.context_processor
def inject_now():
    return {'get_today_date': lambda: datetime.now().strftime('%Y-%m-%d')}

@booking_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@booking_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html', username=session.get('username'))

@booking_bp.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    trains = []
    if request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        date = request.form.get('date')
        
        # Determine train time based on destination for demo variety
        time = "10:00 AM" if len(source) > 5 else "02:30 PM"
        
        # Mock results
        trains = [
            {'sys_id': '101', 'name': 'Rajdhani Express', 'time': time, 'date': date, 'price': 1500},
            {'sys_id': '102', 'name': 'Shatabdi Express', 'time': '06:00 AM', 'date': date, 'price': 1200},
            {'sys_id': '103', 'name': 'Duronto Express', 'time': '08:45 PM', 'date': date, 'price': 1800}
        ]
    return render_template('search.html', trains=trains)

@booking_bp.route('/book/<train_id>', methods=['GET', 'POST'])
def book(train_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Calculate Confidence Score before rendering or booking
    journey_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    confidence = calculate_confidence(train_id, journey_date)

    if request.method == 'POST':
        db = get_db()
        ticket_id = generate_ticket_id()
        
        booking_data = {
            'ticket_id': ticket_id,
            'user_id': session['user_id'],
            'train_id': train_id,
            'journey_date': request.form.get('journey_date'),
            'journey_time': request.form.get('journey_time'),
            'passenger_name': request.form.get('passenger_name'),
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'num_passengers': request.form.get('num_passengers'),
            'stress_level': request.form.get('stress_level', 'unknown'),
            'booking_confidence': confidence['score'], # Log the score at time of booking
            'status': 'Booked',
            'created_at': datetime.now()
        }
        
        db.bookings.insert_one(booking_data)
        flash(f'Booking Confirmed! Your Ticket ID is {ticket_id}')
        return redirect(url_for('booking.feedback'))
        
    return render_template('booking.html', train_id=train_id, confidence=confidence)

@booking_bp.route('/feedback')
def feedback():
    return render_template('feedback.html')

@booking_bp.route('/lock_plan/<train_id>', methods=['POST'])
def lock_plan(train_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    journey_date = request.form.get('journey_date')
    
    # Calculate initial confidence to store
    initial_confidence = calculate_confidence(train_id, journey_date)
    
    plan_data = {
        'user_id': session['user_id'],
        'train_id': train_id,
        'journey_date': journey_date,
        'journey_time': request.form.get('journey_time'),
        'passenger_name': request.form.get('passenger_name'),
        'age': request.form.get('age'),
        'gender': request.form.get('gender'),
        'num_passengers': request.form.get('num_passengers'),
        'stress_level': request.form.get('stress_level', 'unknown'),
        'initial_confidence': initial_confidence['score'],
        'status': 'Locked',
        'created_at': datetime.now()
    }
    
    db.locked_plans.insert_one(plan_data)
    flash('Travel Plan Locked! We will notify you when conditions improve.')
    return redirect(url_for('booking.locked_plans'))

@booking_bp.route('/locked_plans')
def locked_plans():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    plans_cursor = db.locked_plans.find({'user_id': session['user_id'], 'status': 'Locked'}).sort('created_at', -1)
    
    plans = []
    for plan in plans_cursor:
        # Re-calculate current confidence
        current_confidence = calculate_confidence(plan['train_id'], plan['journey_date'])
        
        # Check for improvement
        # In a real app, we might use a threshold (e.g., +5% improvement)
        is_improved = current_confidence['score'] > plan['initial_confidence']
        
        plan['current_confidence'] = current_confidence['score']
        plan['is_improved'] = is_improved
        plan['details'] = current_confidence # pass full details for UI if needed
        plans.append(plan)
        
    return render_template('locked_plans.html', plans=plans)

@booking_bp.route('/convert_lock/<plan_id>', methods=['POST'])
def convert_lock(plan_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    db = get_db()
    
    # Get the plan
    plan = db.locked_plans.find_one({'_id': ObjectId(plan_id), 'user_id': session['user_id']})
    if not plan:
        flash('Plan not found')
        return redirect(url_for('booking.locked_plans'))
        
    # Create booking from plan
    ticket_id = generate_ticket_id()
    booking_data = {
        'ticket_id': ticket_id,
        'user_id': session['user_id'],
        'train_id': plan['train_id'],
        'journey_date': plan['journey_date'],
        'journey_time': plan['journey_time'],
        'passenger_name': plan['passenger_name'],
        'age': plan['age'],
        'gender': plan['gender'],
        'num_passengers': plan['num_passengers'],
        'stress_level': plan['stress_level'],
        'booking_confidence': plan.get('current_confidence', plan['initial_confidence']), # Use best available
        'status': 'Booked',
        'created_at': datetime.now()
    }
    
    db.bookings.insert_one(booking_data)
    db.locked_plans.update_one({'_id': ObjectId(plan_id)}, {'$set': {'status': 'Booked'}})
    
    flash(f'Plan Converted to Booking! Ticket ID: {ticket_id}')
    return redirect(url_for('booking.feedback'))


@booking_bp.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    # Find bookings for this user, sort by new
    bookings = list(db.bookings.find({'user_id': session['user_id']}).sort('created_at', -1))
    return render_template('history.html', bookings=bookings)

@booking_bp.route('/cancel/<ticket_id>', methods=['POST'])
def cancel(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    db = get_db()
    db.bookings.delete_one({'ticket_id': ticket_id, 'user_id': session['user_id']})
    flash('Ticket cancelled successfully.')
    return redirect(url_for('booking.history'))
