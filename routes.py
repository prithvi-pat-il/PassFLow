from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from datetime import datetime, date
import os
from PIL import Image
from werkzeug.utils import secure_filename
import json

# Excel file location
EXCEL_FILE_PATH = 'routes and price data.xlsx'

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
    
    # Get pricing information
    pricing = {p.location: p.price for p in Pricing.query.all()}
    
    # Get routes information
    routes = Route.query.all()
    
    # Get latest pass
    latest_pass = Pass.query.filter_by(user_id=user.id).order_by(Pass.created_at.desc()).first()
    
    return render_template('dashboard.html', 
                         user=user, 
                         profile=profile, 
                         pricing=pricing, 
                         routes=routes, 
                         latest_pass=latest_pass)

@app.route('/profile/complete', methods=['GET', 'POST'])
@login_required
def complete_profile():
    user = User.query.get(session['user_id'])
    profile = user.profile
    
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

def resize_image(filepath, max_size=(600, 600)):
    """Resize image to maximum dimensions"""
    try:
        with Image.open(filepath) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(filepath, optimize=True, quality=85)
    except Exception as e:
        print(f"Error resizing image: {e}")

@app.route('/create_pass', methods=['GET', 'POST'])
@login_required
def create_pass():
    user = User.query.get(session['user_id'])
    profile = user.profile
    
    if not profile.is_complete:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('complete_profile'))
    
    if request.method == 'POST':
        # Get pricing for user's location
        pricing = Pricing.query.filter_by(location=profile.location).first()
        if not pricing:
            flash('Pricing not available for your location.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Create pass
        new_pass = Pass(
            user_id=user.id,
            route_id=profile.route_id,
            amount_paid=pricing.price,
            expiry_date=profile.semester_end_date
        )
        db.session.add(new_pass)
        db.session.commit()
        
        # Create mock payment
        payment = Payment(
            user_id=user.id,
            pass_id=new_pass.id,
            amount=pricing.price,
            transaction_id=payment.generate_transaction_id()
        )
        db.session.add(payment)
        db.session.commit()
        
        flash('Pass created successfully! Awaiting admin approval.', 'success')
        return redirect(url_for('pass_detail', pass_id=new_pass.id))
    
    # Get pricing for user's location
    pricing = Pricing.query.filter_by(location=profile.location).first()
    return render_template('create_pass.html', profile=profile, pricing=pricing)

@app.route('/pass/<int:pass_id>')
@login_required
def pass_detail(pass_id):
    user = User.query.get(session['user_id'])
    bus_pass = Pass.query.get_or_404(pass_id)
    
    # Check if user owns this pass or is admin
    if bus_pass.user_id != user.id and user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('pass_detail.html', bus_pass=bus_pass)

@app.route('/route_map')
@login_required
def route_map():
    routes = Route.query.all()
    return render_template('route_map.html', routes=routes)

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
