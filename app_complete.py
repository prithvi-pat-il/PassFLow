import os
import secrets
import string
import random
import json
import io
import base64
import smtplib
import threading
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from PIL import Image
from werkzeug.utils import secure_filename
import qrcode

# Excel file location
EXCEL_FILE_PATH = 'routes and price data.xlsx'

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
# Support both SQLite and PostgreSQL (for Render)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///bus_pass_system.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Template context
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'date': date}

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')  # student or admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    passes = db.relationship('Pass', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prn = db.Column(db.String(20), unique=True)
    pass_no = db.Column(db.String(20), unique=True)
    photo = db.Column(db.String(200))
    location = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    semester_end_date = db.Column(db.Date)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'))
    bus_number = db.Column(db.String(20))
    is_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def generate_pass_no(self):
        """Generate unique pass number"""
        while True:
            pass_no = 'BP' + ''.join(random.choices(string.digits, k=8))
            if not Profile.query.filter_by(pass_no=pass_no).first():
                return pass_no

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bus_number = db.Column(db.String(20), nullable=False)
    stops = db.Column(db.Text)  # JSON string of stops with coordinates
    timings = db.Column(db.Text)  # JSON string of timing information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profiles = db.relationship('Profile', backref='route', lazy=True)
    passes = db.relationship('Pass', backref='route', lazy=True)
    
    def get_stops(self):
        """Return stops as Python list"""
        return json.loads(self.stops) if self.stops else []
    
    def set_stops(self, stops_list):
        """Set stops from Python list"""
        self.stops = json.dumps(stops_list)
    
    def get_timings(self):
        """Return timings as Python dict"""
        return json.loads(self.timings) if self.timings else {}
    
    def set_timings(self, timings_dict):
        """Set timings from Python dict"""
        self.timings = json.dumps(timings_dict)

class Pricing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Pass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    issue_date = db.Column(db.Date, default=datetime.utcnow().date)
    expiry_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payment = db.relationship('Payment', backref='bus_pass', uselist=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pass_id = db.Column(db.Integer, db.ForeignKey('pass.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='Mock Payment')
    transaction_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default='Completed')  # Completed, Failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def generate_transaction_id(self):
        """Generate unique transaction ID"""
        while True:
            trans_id = 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            if not Payment.query.filter_by(transaction_id=trans_id).first():
                return trans_id

class AlertConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "7 Days Before Expiry"
    days_before = db.Column(db.Integer, nullable=False)  # Days before expiry to send alert
    email_template = db.Column(db.Text, nullable=False)
    sms_template = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pass_id = db.Column(db.Integer, db.ForeignKey('pass.id'), nullable=False)
    alert_config_id = db.Column(db.Integer, db.ForeignKey('alert_configuration.id'), nullable=False)
    notification_type = db.Column(db.String(10), nullable=False)  # 'email' or 'sms'
    recipient = db.Column(db.String(200), nullable=False)  # email or phone number
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    bus_pass = db.relationship('Pass', backref='notifications')
    alert_config = db.relationship('AlertConfiguration', backref='notifications')

# Initialize database on startup (for production deployments)
def init_db():
    """Initialize database tables and default data"""
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                name='Administrator',
                email='admin@example.com',
                phone='1234567890',
                password=admin_password,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        # Ensure default alert configurations exist
        defaults = [
            ("3 Weeks Before Expiry", 21),
            ("1 Week Before Expiry", 7),
        ]
        for name, days in defaults:
            cfg = AlertConfiguration.query.filter_by(days_before=days).first()
            if not cfg:
                cfg = AlertConfiguration(
                    name=name,
                    days_before=days,
                    email_template=(
                        "Hello {name}, your bus pass ({pass_no}) for {route_name} "
                        "expires on {expiry_date} (in {days_until_expiry} days). "
                        "Please renew to avoid interruption."
                    ),
                    sms_template=(
                        "Bus Pass {pass_no} expires in {days_until_expiry} days (on {expiry_date}). "
                        "Renew soon."
                    ),
                    is_active=True
                )
                db.session.add(cfg)
        db.session.commit()

# Run initialization when app is imported (for production)
if os.environ.get('FLASK_ENV') == 'production':
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization skipped: {e}")

# Utility functions
def login_required(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def resize_image(filepath, max_size=(600, 600)):
    """Resize image to maximum dimensions"""
    try:
        with Image.open(filepath) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(filepath, optimize=True, quality=85)
    except Exception as e:
        print(f"Error resizing image: {e}")

def is_pass_expired(bus_pass):
    """Check if a pass is expired"""
    return date.today() > bus_pass.expiry_date

def get_days_until_expiry(bus_pass):
    """Get number of days until pass expires"""
    return (bus_pass.expiry_date - date.today()).days

def format_template(template, user, bus_pass):
    """Format notification template with user and pass data"""
    days_until_expiry = get_days_until_expiry(bus_pass)
    
    replacements = {
        '{name}': user.name,
        '{email}': user.email,
        '{phone}': user.phone,
        '{pass_no}': user.profile.pass_no if user.profile else 'N/A',
        '{route_name}': bus_pass.route.name if bus_pass.route else 'N/A',
        '{bus_number}': bus_pass.route.bus_number if bus_pass.route else 'N/A',
        '{issue_date}': bus_pass.issue_date.strftime('%d/%m/%Y'),
        '{expiry_date}': bus_pass.expiry_date.strftime('%d/%m/%Y'),
        '{days_until_expiry}': str(days_until_expiry),
        '{amount_paid}': f'₹{bus_pass.amount_paid:.2f}'
    }
    
    formatted_message = template
    for placeholder, value in replacements.items():
        formatted_message = formatted_message.replace(placeholder, value)
    
    return formatted_message

def send_email_notification(to_email, subject, message):
    """Send email notification (mock implementation)"""
    try:
        # Mock email sending - in production, use actual SMTP settings
        print(f"EMAIL SENT TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"MESSAGE: {message}")
        print("-" * 50)
        return True, None
    except Exception as e:
        return False, str(e)

def send_sms_notification(to_phone, message):
    """Send SMS notification.
    If Twilio env vars are present, send real SMS. Otherwise, fallback to console log.
    Required env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM
    """
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_FROM')
        if account_sid and auth_token and from_number:
            try:
                from twilio.rest import Client  # type: ignore
                client = Client(account_sid, auth_token)
                client.messages.create(body=message, from_=from_number, to=to_phone)
                return True, None
            except Exception as twilio_err:
                # Fallback to console if Twilio fails
                print(f"Twilio send failed: {twilio_err}. Falling back to console log.")
        # Fallback mock
        print(f"SMS SENT TO: {to_phone}")
        print(f"MESSAGE: {message}")
        print("-" * 50)
        return True, None
    except Exception as e:
        return False, str(e)

def create_notification_log(user_id, pass_id, alert_config_id, notification_type, recipient, message):
    """Create a notification log entry"""
    notification = NotificationLog(
        user_id=user_id,
        pass_id=pass_id,
        alert_config_id=alert_config_id,
        notification_type=notification_type,
        recipient=recipient,
        message=message
    )
    return notification

def send_expiry_alerts():
    """Check for passes that need expiry alerts and send them"""
    try:
        with app.app_context():
            # Get active alert configurations
            alert_configs = AlertConfiguration.query.filter_by(is_active=True).all()
            
            for config in alert_configs:
                # Find passes that expire in the configured number of days
                target_date = date.today() + timedelta(days=config.days_before)
                
                # Get passes expiring on target date that haven't received this alert yet
                passes_to_alert = Pass.query.filter(
                    Pass.expiry_date == target_date,
                    Pass.status == 'Approved'
                ).all()
                
                for bus_pass in passes_to_alert:
                    user = bus_pass.user
                    
                    # Check if alert already sent for this pass and config
                    existing_log = NotificationLog.query.filter_by(
                        pass_id=bus_pass.id,
                        alert_config_id=config.id,
                        status='sent'
                    ).first()
                    
                    if existing_log:
                        continue  # Already sent
                    
                    # Send email notification
                    email_message = format_template(config.email_template, user, bus_pass)
                    email_success, email_error = send_email_notification(
                        user.email, 
                        f"Bus Pass Expiry Alert - {config.name}", 
                        email_message
                    )
                    
                    # Log email notification
                    email_log = create_notification_log(
                        user.id, bus_pass.id, config.id, 'email', 
                        user.email, email_message
                    )
                    if email_success:
                        email_log.status = 'sent'
                        email_log.sent_at = datetime.utcnow()
                    else:
                        email_log.status = 'failed'
                        email_log.error_message = email_error
                    
                    db.session.add(email_log)
                    
                    # Send SMS notification
                    sms_message = format_template(config.sms_template, user, bus_pass)
                    sms_success, sms_error = send_sms_notification(user.phone, sms_message)
                    
                    # Log SMS notification
                    sms_log = create_notification_log(
                        user.id, bus_pass.id, config.id, 'sms', 
                        user.phone, sms_message
                    )
                    if sms_success:
                        sms_log.status = 'sent'
                        sms_log.sent_at = datetime.utcnow()
                    else:
                        sms_log.status = 'failed'
                        sms_log.error_message = sms_error
                    
                    db.session.add(sms_log)
                    
            db.session.commit()
            print(f"Expiry alerts check completed at {datetime.now()}")
            
    except Exception as e:
        print(f"Error sending expiry alerts: {e}")

def start_alert_scheduler():
    """Start background thread for checking expiry alerts"""
    def run_scheduler():
        import time
        while True:
            send_expiry_alerts()
            # Check every hour (3600 seconds)
            time.sleep(3600)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("Alert scheduler started")

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not all([name, email, phone, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        
        # Create user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, phone=phone, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        # Create empty profile
        profile = Profile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    profile = user.profile
    
    # Create profile if it doesn't exist
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Get pricing information
    pricing = {p.location: p.price for p in Pricing.query.all()}
    
    # Get routes information
    routes = Route.query.all()
    
    # Get latest pass
    latest_pass = Pass.query.filter_by(user_id=user.id).order_by(Pass.created_at.desc()).first()
    days_until_expiry = None
    if latest_pass and latest_pass.status == 'Approved' and latest_pass.expiry_date >= date.today():
        days_until_expiry = (latest_pass.expiry_date - date.today()).days
    
    return render_template('dashboard.html', 
                         user=user, 
                         profile=profile, 
                         pricing=pricing, 
                         routes=routes, 
                         latest_pass=latest_pass,
                         days_until_expiry=days_until_expiry)

@app.route('/profile/complete', methods=['GET', 'POST'])
@login_required
def complete_profile():
    user = User.query.get(session['user_id'])
    profile = user.profile
    
    # Create profile if it doesn't exist
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    if request.method == 'POST':
        # Handle form data
        profile.prn = request.form['prn']
        profile.location = request.form['location']
        profile.semester = request.form['semester']
        profile.semester_end_date = datetime.strptime(request.form['semester_end_date'], '%Y-%m-%d').date()
        profile.route_id = request.form['route_id']
        profile.bus_number = request.form['bus_number']
        
        # Generate pass number if not exists
        if not profile.pass_no:
            profile.pass_no = profile.generate_pass_no()
        
        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Save and resize image
                file.save(filepath)
                resize_image(filepath)
                profile.photo = filename
        
        profile.is_complete = True
        db.session.commit()
        
        flash('Profile completed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    routes = Route.query.all()
    pricing = Pricing.query.all()
    return render_template('complete_profile.html', profile=profile, routes=routes, pricing=pricing)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.get(session['user_id'])
        
        if not bcrypt.check_password_hash(user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('change_password.html')
        
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        flash('Password updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html')

@app.route('/create_pass', methods=['GET', 'POST'])
@login_required
def create_pass():
    user = User.query.get(session['user_id'])
    profile = user.profile
    
    if not profile.is_complete:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('complete_profile'))
    
    if request.method == 'POST':
        selected_location = request.form.get('location')
        selected_route_id = request.form.get('route_id')
        
        if not selected_location or not selected_route_id:
            flash('Please select both location and route.', 'danger')
            return redirect(url_for('create_pass'))
        
        # Get pricing for selected location
        pricing = Pricing.query.filter_by(location=selected_location).first()
        if not pricing:
            flash('Pricing not available for selected location.', 'danger')
            return redirect(url_for('create_pass'))
        
        # Store selection in session for payment
        session['pass_data'] = {
            'location': selected_location,
            'route_id': int(selected_route_id),
            'amount': pricing.price
        }
        
        return redirect(url_for('payment_gateway'))
    
    # Get all available locations from pricing
    pricing_all = Pricing.query.all()
    locations = [p.location for p in pricing_all]
    pricing_data = {p.location: p.price for p in pricing_all}
    
    return render_template('create_pass.html', 
                         profile=profile, 
                         locations=locations, 
                         pricing_data=pricing_data)

@app.route('/pass/<int:pass_id>')
@login_required
def pass_detail(pass_id):
    user = User.query.get(session['user_id'])
    bus_pass = Pass.query.get_or_404(pass_id)
    
    # Check if user owns this pass or is admin
    if bus_pass.user_id != user.id and user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check expiry status
    expired = is_pass_expired(bus_pass)
    days_until_expiry = get_days_until_expiry(bus_pass) if not expired else 0
    
    return render_template('pass_detail.html', 
                         bus_pass=bus_pass, 
                         expired=expired, 
                         days_until_expiry=days_until_expiry)

@app.route('/pass/<int:pass_id>/print')
@login_required
def print_pass(pass_id):
    user = User.query.get(session['user_id'])
    bus_pass = Pass.query.get_or_404(pass_id)
    
    # Check if user owns this pass or is admin
    if bus_pass.user_id != user.id and user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Generate QR code for pass verification
    qr_data = f"PASS:{bus_pass.id}:{bus_pass.user.profile.pass_no}:{bus_pass.status}"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    qr_code_b64 = base64.b64encode(img_io.read()).decode('utf-8')
    qr_code_data = f"data:image/png;base64,{qr_code_b64}"
    
    return render_template('printable_pass.html', 
                         bus_pass=bus_pass, 
                         user=bus_pass.user,
                         qr_code_data=qr_code_data)

@app.route('/route_map')
@login_required
def route_map():
    routes = Route.query.all()
    return render_template('route_map.html', routes=routes)

@app.route('/api/routes_by_location/<location>')
@login_required
def get_routes_by_location(location):
    """Get routes that serve a particular location"""
    routes = Route.query.all()
    matching_routes = []
    
    for route in routes:
        stops = route.get_stops()
        stop_names = [stop['name'] for stop in stops]
        if location in stop_names:
            matching_routes.append({
                'id': route.id,
                'name': route.name,
                'bus_number': route.bus_number,
                'stops': stops
            })
    
    return jsonify(matching_routes)

@app.route('/generate_qr')
@login_required
def generate_qr():
    """Generate QR code for payment"""
    if 'pass_data' not in session:
        return '', 404
    
    pass_data = session['pass_data']
    
    # Create UPI payment string (demo)
    upi_string = f"upi://pay?pa=demo@paytm&pn=PassFlow&am={pass_data['amount']}&cu=INR&tn=Bus Pass Payment for {pass_data['location']}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_string)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    img_b64 = base64.b64encode(img_io.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_b64}"

@app.route('/payment_gateway')
@login_required
def payment_gateway():
    """Demo payment gateway with QR code"""
    if 'pass_data' not in session:
        flash('Invalid payment session. Please select route again.', 'danger')
        return redirect(url_for('create_pass'))
    
    pass_data = session['pass_data']
    route = Route.query.get(pass_data['route_id'])
    
    return render_template('payment_gateway.html', 
                         pass_data=pass_data, 
                         route=route)

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """Process the demo payment and create pass"""
    if 'pass_data' not in session:
        flash('Invalid payment session.', 'danger')
        return redirect(url_for('create_pass'))
    
    user = User.query.get(session['user_id'])
    profile = user.profile
    pass_data = session['pass_data']
    
    payment_method = request.form.get('payment_method', 'UPI')
    
    # Create pass with auto-approval
    new_pass = Pass(
        user_id=user.id,
        route_id=pass_data['route_id'],
        amount_paid=pass_data['amount'],
        expiry_date=profile.semester_end_date,
        status='Approved'  # Auto-approve after payment
    )
    db.session.add(new_pass)
    db.session.commit()
    
    # Create payment record
    payment = Payment(
        user_id=user.id,
        pass_id=new_pass.id,
        amount=pass_data['amount'],
        payment_method=payment_method
    )
    payment.transaction_id = payment.generate_transaction_id()
    db.session.add(payment)
    
    # Update profile with selected route
    profile.location = pass_data['location']
    profile.route_id = pass_data['route_id']
    route = Route.query.get(pass_data['route_id'])
    if route:
        profile.bus_number = route.bus_number
    
    db.session.commit()
    
    # Clear session data
    session.pop('pass_data', None)
    
    flash('Payment successful! Your bus pass has been created and approved.', 'success')
    return redirect(url_for('pass_detail', pass_id=new_pass.id))

@app.route('/payment_success')
@login_required
def payment_success():
    """Payment success page"""
    return render_template('payment_success.html')

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.filter_by(role='student').count()
    pending_passes = Pass.query.filter_by(status='Pending').count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    
    # Get recent activity
    recent_passes = Pass.query.order_by(Pass.created_at.desc()).limit(5).all()
    pending_payments = Pass.query.filter_by(status='Pending').all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         pending_passes=pending_passes,
                         total_revenue=total_revenue,
                         recent_passes=recent_passes,
                         pending_payments=pending_payments)

@app.route('/admin/approve_pass/<int:pass_id>')
@admin_required
def approve_pass(pass_id):
    bus_pass = Pass.query.get_or_404(pass_id)
    bus_pass.status = 'Approved'
    db.session.commit()
    flash(f'Pass for {bus_pass.user.name} approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/data_management')
@admin_required
def data_management():
    """View imported data statistics and management"""
    routes = Route.query.all()
    pricing = Pricing.query.all()
    
    # Calculate statistics
    total_stops = sum(len(route.get_stops()) for route in routes)
    avg_price = sum(p.price for p in pricing) / len(pricing) if pricing else 0
    
    return render_template('admin/data_management.html',
                         routes=routes,
                         pricing=pricing,
                         total_stops=total_stops,
                         avg_price=avg_price)

@app.route('/admin/reject_pass/<int:pass_id>')
@admin_required
def reject_pass(pass_id):
    bus_pass = Pass.query.get_or_404(pass_id)
    bus_pass.status = 'Rejected'
    db.session.commit()
    flash(f'Pass for {bus_pass.user.name} rejected.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/routes')
@admin_required
def admin_routes():
    routes = Route.query.all()
    return render_template('admin/routes.html', routes=routes)

@app.route('/admin/routes/add', methods=['GET', 'POST'])
@admin_required
def add_route():
    if request.method == 'POST':
        route = Route(
            name=request.form['name'],
            bus_number=request.form['bus_number']
        )
        
        # Parse stops (expecting JSON format)
        try:
            stops_data = request.form['stops']
            if stops_data:
                route.set_stops(json.loads(stops_data))
        except json.JSONDecodeError:
            flash('Invalid stops format. Please use valid JSON.', 'danger')
            return render_template('admin/add_route.html')
        
        # Parse timings
        try:
            timings_data = request.form['timings']
            if timings_data:
                route.set_timings(json.loads(timings_data))
        except json.JSONDecodeError:
            flash('Invalid timings format. Please use valid JSON.', 'danger')
            return render_template('admin/add_route.html')
        
        db.session.add(route)
        db.session.commit()
        flash('Route added successfully!', 'success')
        return redirect(url_for('admin_routes'))
    
    return render_template('admin/add_route.html')

@app.route('/admin/pricing')
@admin_required
def admin_pricing():
    pricing = Pricing.query.all()
    return render_template('admin/pricing.html', pricing=pricing)

@app.route('/admin/pricing/add', methods=['GET', 'POST'])
@admin_required
def add_pricing():
    if request.method == 'POST':
        location = request.form['location']
        price = float(request.form['price'])
        
        # Check if location already exists
        existing = Pricing.query.filter_by(location=location).first()
        if existing:
            existing.price = price
        else:
            pricing = Pricing(location=location, price=price)
            db.session.add(pricing)
        
        db.session.commit()
        flash('Pricing updated successfully!', 'success')
        return redirect(url_for('admin_pricing'))
    
    return render_template('admin/add_pricing.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(role='student').all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/payments')
@admin_required
def admin_payments():
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return render_template('admin/payments.html', payments=payments)

@app.route('/admin/print_passes')
@admin_required
def admin_print_passes():
    """Admin interface to manage bulk pass printing"""
    # Get statistics for different pass statuses
    approved_passes = Pass.query.filter_by(status='Approved').all()
    pending_passes = Pass.query.filter_by(status='Pending').all()
    all_passes = Pass.query.all()
    
    # Get filter options
    routes = Route.query.all()
    locations = [p.location for p in Pricing.query.all()]
    
    return render_template('admin/print_passes.html',
                         approved_passes=approved_passes,
                         pending_passes=pending_passes,
                         all_passes=all_passes,
                         routes=routes,
                         locations=locations)

@app.route('/admin/bulk_print')
@admin_required
def admin_bulk_print():
    """Generate bulk printable passes for admin"""
    status_filter = request.args.get('status', 'Approved')
    route_filter = request.args.get('route')
    location_filter = request.args.get('location')
    
    # Build query based on filters
    query = Pass.query
    
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
    
    if route_filter and route_filter != 'All':
        query = query.filter_by(route_id=int(route_filter))
    
    if location_filter and location_filter != 'All':
        # Filter by user profile location
        query = query.join(User).join(Profile).filter(Profile.location == location_filter)
    
    passes = query.all()
    
    # Generate QR codes for all passes
    passes_with_qr = []
    for bus_pass in passes:
        qr_data = f"PASS:{bus_pass.id}:{bus_pass.user.profile.pass_no}:{bus_pass.status}"
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        qr_code_b64 = base64.b64encode(img_io.read()).decode('utf-8')
        qr_code_data = f"data:image/png;base64,{qr_code_b64}"
        
        passes_with_qr.append({
            'pass': bus_pass,
            'user': bus_pass.user,
            'qr_code': qr_code_data
        })
    
    return render_template('admin/bulk_print.html', passes_with_qr=passes_with_qr)

@app.route('/admin/alerts')
@admin_required
def admin_alerts():
    """Admin interface to manage expiry alerts"""
    alert_configs = AlertConfiguration.query.all()
    recent_notifications = NotificationLog.query.order_by(NotificationLog.created_at.desc()).limit(20).all()
    
    return render_template('admin/alerts.html',
                         alert_configs=alert_configs,
                         recent_notifications=recent_notifications)

@app.route('/admin/alerts/add', methods=['GET', 'POST'])
@admin_required
def add_alert_config():
    """Add new alert configuration"""
    if request.method == 'POST':
        config = AlertConfiguration(
            name=request.form['name'],
            days_before=int(request.form['days_before']),
            email_template=request.form['email_template'],
            sms_template=request.form['sms_template'],
            is_active=bool(request.form.get('is_active'))
        )
        db.session.add(config)
        db.session.commit()
        flash('Alert configuration added successfully!', 'success')
        return redirect(url_for('admin_alerts'))
    
    return render_template('admin/add_alert.html')

@app.route('/admin/alerts/edit/<int:config_id>', methods=['GET', 'POST'])
@admin_required
def edit_alert_config(config_id):
    """Edit alert configuration"""
    config = AlertConfiguration.query.get_or_404(config_id)
    
    if request.method == 'POST':
        config.name = request.form['name']
        config.days_before = int(request.form['days_before'])
        config.email_template = request.form['email_template']
        config.sms_template = request.form['sms_template']
        config.is_active = bool(request.form.get('is_active'))
        config.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Alert configuration updated successfully!', 'success')
        return redirect(url_for('admin_alerts'))
    
    return render_template('admin/edit_alert.html', config=config)

@app.route('/admin/alerts/toggle/<int:config_id>')
@admin_required
def toggle_alert_config(config_id):
    """Toggle alert configuration active status"""
    config = AlertConfiguration.query.get_or_404(config_id)
    config.is_active = not config.is_active
    config.updated_at = datetime.utcnow()
    db.session.commit()
    
    status = 'activated' if config.is_active else 'deactivated'
    flash(f'Alert configuration {status} successfully!', 'success')
    return redirect(url_for('admin_alerts'))

@app.route('/admin/test_alerts')
@admin_required
def test_alerts():
    """Manually trigger alert check for testing"""
    send_expiry_alerts()
    flash('Alert check completed! Check the console for sent notifications.', 'info')
    return redirect(url_for('admin_alerts'))

@app.route('/admin/import_data')
@admin_required
def import_excel_data():
    """Import data from Excel file"""
    try:
        import pandas as pd
        import math
        
        # Read the Excel file
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Monthly Price')
        
        # Clear existing data
        Route.query.delete()
        Pricing.query.delete()
        db.session.commit()
        
        routes_imported = 0
        pricing_imported = 0
        current_route = None
        route_stops = []
        
        for index, row in df.iterrows():
            if index == 0:  # Skip header
                continue
            
            # Check for route header
            route_header = str(row.iloc[1])
            if 'Route No.' in route_header:
                # Save previous route
                if current_route and route_stops:
                    route = Route(name=current_route['name'], bus_number=current_route['bus_number'])
                    stops_for_json = [{'name': stop['name'], 'lat': stop['lat'], 'lng': stop['lng']} for stop in sorted(route_stops, key=lambda x: x['order'])]
                    route.set_stops(stops_for_json)
                    route.set_timings({'First Bus': '06:00 AM', 'Last Bus': '09:00 PM', 'Frequency': 'Every 45-60 minutes'})
                    db.session.add(route)
                    routes_imported += 1
                    route_stops = []
                
                # Extract new route info
                route_parts = route_header.split('Route No.')
                if len(route_parts) > 1:
                    route_name = route_parts[0].strip()
                    route_number = route_parts[1].strip()
                    current_route = {
                        'name': f"{route_name} - Route {route_number}",
                        'bus_number': f"BUS{route_number.zfill(2)}"
                    }
                continue
            
            # Process station data
            try:
                sr_no = row.iloc[1]
                station_name = row.iloc[2]
                price_per_month = row.iloc[4]
                
                if not pd.isna(sr_no) and not pd.isna(station_name) and not pd.isna(price_per_month):
                    sr_no = int(sr_no)
                    station_name = str(station_name).strip()
                    price_per_month = float(price_per_month)
                    
                    if 'SIT COE' not in station_name and price_per_month > 0:
                        # Add pricing
                        existing_pricing = Pricing.query.filter_by(location=station_name).first()
                        if not existing_pricing:
                            pricing = Pricing(location=station_name, price=price_per_month)
                            db.session.add(pricing)
                            pricing_imported += 1
                        
                        # Add to route stops
                        if current_route:
                            # Generate coordinates around Kolhapur
                            base_lat, base_lng = 16.7050, 74.2433
                            angle = (sr_no * 30) % 360
                            radius = 0.01 + (sr_no * 0.005)
                            lat = base_lat + (radius * math.cos(math.radians(angle)))
                            lng = base_lng + (radius * math.sin(math.radians(angle)))
                            
                            route_stops.append({
                                'name': station_name,
                                'lat': round(lat, 6),
                                'lng': round(lng, 6),
                                'order': sr_no
                            })
            except (ValueError, TypeError):
                continue
        
        # Save last route
        if current_route and route_stops:
            route = Route(name=current_route['name'], bus_number=current_route['bus_number'])
            stops_for_json = [{'name': stop['name'], 'lat': stop['lat'], 'lng': stop['lng']} for stop in sorted(route_stops, key=lambda x: x['order'])]
            route.set_stops(stops_for_json)
            route.set_timings({'First Bus': '06:00 AM', 'Last Bus': '09:00 PM', 'Frequency': 'Every 45-60 minutes'})
            db.session.add(route)
            routes_imported += 1
        
        db.session.commit()
        flash(f'Data imported successfully! {routes_imported} routes and {pricing_imported} pricing locations added.', 'success')
        
    except FileNotFoundError:
        flash(f'Excel file "{EXCEL_FILE_PATH}" not found in current directory.', 'danger')
    except Exception as e:
        flash(f'Error importing data: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                name='Administrator',
                email='admin@example.com',
                phone='1234567890',
                password=admin_password,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created!")
        # Ensure default alert configurations (21 and 7 days) exist
        defaults = [
            ("3 Weeks Before Expiry", 21),
            ("1 Week Before Expiry", 7),
        ]
        for name, days in defaults:
            cfg = AlertConfiguration.query.filter_by(days_before=days).first()
            if not cfg:
                cfg = AlertConfiguration(
                    name=name,
                    days_before=days,
                    email_template=(
                        "Hello {name}, your bus pass ({pass_no}) for {route_name} "
                        "expires on {expiry_date} (in {days_until_expiry} days). "
                        "Please renew to avoid interruption."
                    ),
                    sms_template=(
                        "Bus Pass {pass_no} expires in {days_until_expiry} days (on {expiry_date}). "
                        "Renew soon."
                    ),
                    is_active=True,
                )
                db.session.add(cfg)
        db.session.commit()
        # Start background scheduler for expiry alerts
        start_alert_scheduler()
    
    app.run(debug=True)
