import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Excel file location
EXCEL_FILE_PATH = 'routes and price data.xlsx'

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bus_pass_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

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
    
    app.run(debug=True)
