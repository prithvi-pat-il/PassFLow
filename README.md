# PassFlow

A comprehensive web application for managing student bus passes with Flask backend, SQLite database, and Bootstrap frontend.

## Features

### Student Features
- ✅ User registration and login with secure password hashing
- ✅ Profile completion with PRN, photo upload, location, semester details
- ✅ Dashboard showing location-wise pricing and bus routes
- ✅ Bus pass creation with mock payment processing
- ✅ Pass details view with status tracking
- ✅ Interactive route map using Leaflet + OpenStreetMap
- ✅ Password management system

### Admin Features
- ✅ Admin dashboard with system statistics
- ✅ Approve/reject student bus pass applications
- ✅ Manage bus routes, timings, and stops
- ✅ Update location-wise pricing
- ✅ View all users and their pass history
- ✅ Payment records and revenue tracking

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Maps**: Leaflet.js with OpenStreetMap
- **Authentication**: Flask-Bcrypt for password hashing
- **File Upload**: PIL/Pillow for image processing

## Installation

1. **Clone or download the project**
   ```bash
   cd bus_pass_system
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database (optional - includes sample data)**
   ```bash
   python setup.py
   ```

4. **Run the application**
   ```bash
   python app_complete.py
   ```

5. **Access the application**
   Open your browser and go to: `http://127.0.0.1:5000`

## Default Credentials

- **Admin Login**: 
  - Email: `admin@example.com`
  - Password: `admin123`

## Project Structure

```
bus_pass_system/
├── app_complete.py          # Main Flask application
├── requirements.txt         # Python dependencies
├── setup.py                # Database setup script
├── README.md               # This file
├── static/
│   ├── uploads/            # User uploaded photos
│   ├── css/               # Custom CSS (if needed)
│   └── js/                # Custom JavaScript (if needed)
└── templates/
    ├── base.html           # Base template with Bootstrap
    ├── index.html          # Homepage
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── dashboard.html      # Student dashboard
    ├── complete_profile.html # Profile completion form
    ├── create_pass.html    # Pass creation page
    ├── pass_detail.html    # Pass details view
    ├── change_password.html # Password change form
    ├── route_map.html      # Interactive route map
    └── admin/
        ├── dashboard.html   # Admin dashboard
        ├── routes.html      # Route management
        ├── add_route.html   # Add new route
        ├── pricing.html     # Pricing management
        ├── add_pricing.html # Add new pricing
        ├── users.html       # User management
        └── payments.html    # Payment records
```

## Database Schema

### Tables
1. **User** - User accounts (students and admin)
2. **Profile** - Student profile information
3. **Route** - Bus routes with stops and timings
4. **Pricing** - Location-wise pricing
5. **Pass** - Bus pass records
6. **Payment** - Payment transaction records

## Usage Guide

### For Students

1. **Register**: Create a new account with basic information
2. **Complete Profile**: Add PRN, photo, location, semester details
3. **Create Pass**: Select route and make mock payment
4. **View Pass**: Check pass status and details
5. **Route Map**: View interactive bus route map

### For Admin

1. **Login**: Use admin credentials to access admin panel
2. **Approve Passes**: Review and approve/reject student applications
3. **Manage Routes**: Add new bus routes with stops and timings
4. **Set Pricing**: Configure location-wise pricing
5. **Monitor System**: View users, payments, and system statistics

## API Endpoints

### Public Routes
- `GET /` - Homepage
- `GET /register` - Registration form
- `POST /register` - Process registration
- `GET /login` - Login form
- `POST /login` - Process login
- `GET /logout` - Logout user

### Student Routes (Login Required)
- `GET /dashboard` - Student dashboard
- `GET /profile/complete` - Profile completion form
- `POST /profile/complete` - Process profile completion
- `GET /create_pass` - Pass creation form
- `POST /create_pass` - Process pass creation
- `GET /pass/<id>` - Pass details
- `GET /route_map` - Interactive route map
- `GET /change_password` - Password change form
- `POST /change_password` - Process password change

### Admin Routes (Admin Access Required)
- `GET /admin` - Admin dashboard
- `GET /admin/approve_pass/<id>` - Approve pass
- `GET /admin/reject_pass/<id>` - Reject pass
- `GET /admin/routes` - Route management
- `GET /admin/routes/add` - Add route form
- `POST /admin/routes/add` - Process route addition
- `GET /admin/pricing` - Pricing management
- `GET /admin/pricing/add` - Add pricing form
- `POST /admin/pricing/add` - Process pricing addition
- `GET /admin/users` - User management
- `GET /admin/payments` - Payment records

## Security Features

- ✅ Password hashing with bcrypt
- ✅ Session-based authentication
- ✅ Role-based access control (student/admin)
- ✅ File upload validation and resizing
- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ CSRF protection via Flask session management

## Mobile Responsiveness

The application is fully responsive and works well on:
- ✅ Desktop browsers
- ✅ Tablets
- ✅ Mobile phones

## Development Notes

- No demo/sample user data is included by default
- Photos are resized to max 600x600 pixels automatically
- Mock payment system simulates real transactions
- Admin can manage all aspects of the system
- SQLite database for easy deployment and testing

## Troubleshooting

### Common Issues

1. **Module not found errors**: Install dependencies with `pip install -r requirements.txt`
2. **Permission errors**: Ensure write permissions for the upload folder
3. **Database errors**: Delete `bus_pass_system.db` and run setup again
4. **Image upload issues**: Check file size (max 16MB) and format

### Development Mode

The application runs in debug mode by default. For production:
1. Set `app.run(debug=False)`
2. Use a production WSGI server like Gunicorn
3. Configure proper secret keys and database settings

## License

This project is created for educational purposes and is open source.
