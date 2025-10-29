from app_complete import app, db, bcrypt, AlertConfiguration, User


def initialize_database():
    """Create tables and seed default data for production deployments."""
    with app.app_context():
        # Create all tables
        db.create_all()

        # Ensure default admin user exists
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


if __name__ == "__main__":
    initialize_database()



