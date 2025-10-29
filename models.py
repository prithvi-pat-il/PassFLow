from datetime import datetime
import string
import random
import json

# Excel file location
EXCEL_FILE_PATH = 'routes and price data.xlsx'

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
