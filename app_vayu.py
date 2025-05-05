import os
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify, send_from_directory, jsonify
import requests
import mysql.connector
from mysql.connector import errorcode
from datetime import timedelta, datetime
import warnings
warnings.filterwarnings('ignore')
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import time
from flask_mail import Mail, Message
import uuid
from werkzeug.utils import secure_filename
import secrets
from dateutil.relativedelta import relativedelta
from werkzeug.datastructures import ImmutableMultiDict
import json
from datetime import date
from flask_session import Session
import ast
from jinja2 import Environment
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from redis import Redis
from permissions import get_permissions
import qrcode
from io import BytesIO
import base64
from PIL import Image
import hashlib
import bcrypt
import math
import ast 
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False  # Session lasts as long as the browser is open
app.config['SESSION_USE_SIGNER'] = True  # Adds a signature to session data for security
app.config['SESSION_KEY_PREFIX'] = 'IOMS_'  # Shared prefix for session keys
app.config['SESSION_REDIS'] = Redis(host='localhost', port=6379, db=0)  # Same Redis instance
app.config['SECRET_KEY'] = 'shared_secret_key'  # Same secret key for signing sessions
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

Session(app)


# Customize Jinja2 environment to include zip
def jinja2_zip(*args):
    return zip(*args)

app.jinja_env.globals['zip'] = jinja2_zip


db_config = {
    'host': 'localhost',
    'user': 'yt',
    'password': 'yt',
    'database': 'vayu_asset_management',
     'port': 3306  # Added port explicitly
}

# Database configuration for Big_App_Login_Users
big_app_db_config = {
    'host': 'localhost',
    'user': 'yt',
    'password': 'yt',
    'database': 'Big_App_Login_Users',
    'port': 3306
}



UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}


# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = 'nivetha@tapmobi.in'  # Update this
SMTP_PASSWORD = "Tapmobi@07"  # Update this
to_mail ='nivetha@tapmobi.in'



def get_big_app_db_connection():
    try:
        conn = mysql.connector.connect(**big_app_db_config)
        return conn
    except mysql.connector.Error as err:
        print(err)
        return None




@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles login for Asset Tracker (8000).
    If redirected from IOMS (8835), extracts session details.
    """


    if request.args.get('username') and request.args.get('role'):
        session['username'] = request.args.get('username')
        session['role_id'] = request.args.get('role')
        session['emp_id'] = session.get('IOMS_emp_id')
        print(f"User {session['username']} logged in with role {session['role_id']} and id {session['emp_id']}")
        return redirect(url_for('home'))

    # return render_template('login.html')
    return redirect('http://192.168.2.48:8835/login')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))  # Redirect to login if not logged in
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
def logout():
    session.clear()
    return redirect('http://192.168.2.48:8835/login')


@app.route('/qr_login', methods=['GET', 'POST'])
def custom_login():
    """
    Handles QR code specific login with bcrypt and multiple identifiers,
    redirects to asset details based on permissions
    """
    asset_id = request.args.get('asset_id')
    
    if not asset_id:
        return "Invalid QR code", 400

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()

        # Validate input presence
        if not identifier or not password:
            flash('Please enter both username/email/phone and password.', 'custom_login')
            return render_template('qr_login.html', asset_id=asset_id)

        try:
            conn = get_big_app_db_connection()
            if not conn:
                flash('Database connection failed', 'custom_login')
                return render_template('qr_login.html', asset_id=asset_id)

            cursor = conn.cursor(dictionary=True)

            try:
                # Query user with multiple identifiers
                cursor.execute(
                    """SELECT username, password_hash, 
                              can_create_Bills_Document_Manager,
                              can_read_Bills_Document_Manager,
                              can_update_Bills_Document_Manager,
                              can_delete_Bills_Document_Manager
                       FROM User 
                       WHERE username = %s OR email = %s OR phone = %s""",
                    (identifier, identifier, identifier)
                )
                user = cursor.fetchone()

                # Verify credentials
                if user and bcrypt.checkpw(
                    password.encode('utf-8'),
                    user['password_hash'].encode('utf-8')
                ):
                    # Determine role based on permissions
                    create = user['can_create_Bills_Document_Manager']
                    read = user['can_read_Bills_Document_Manager']
                    update = user['can_update_Bills_Document_Manager']
                    delete = user['can_delete_Bills_Document_Manager']

                    if create == 1 and read == 1 and update == 1 and delete == 1:
                        role = 'admin'
                    elif create == 1 and read == 1 and update == 1 and delete == 0:
                        role = 'manager'
                    elif create == 0 and read == 1 and update == 0 and delete == 0:
                        role = 'employee'
                    else:
                        role = 'none'

                    if role in ['admin', 'manager']:
                        session['username'] = user['username']
                        session['role_id'] = role
                        session['qr_login'] = True  # Flag to indicate QR-based login
                        session['IOMS_can_create_Bills_Document_Manager']=create
                        session['IOMS_can_read_Bills_Document_Manager']=read
                        session['IOMS_can_update_Bills_Document_Manager']=update
                        session['IOMS_can_delete_Bills_Document_Manager']=delete

                        print(f"User {user['username']} logged in via QR with role {role}")
                        return redirect(url_for('view_asset_details', asset_id=asset_id))
                    else:
                        flash('No access permission for asset details', 'custom_login')
                        return render_template('qr_login.html', asset_id=asset_id)
                else:
                    flash('Invalid credentials', 'custom_login')
                    return render_template('qr_login.html', asset_id=asset_id)

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            flash(f'Login error: {str(e)}', 'custom_login')
            return render_template('qr_login.html', asset_id=asset_id)

    return render_template('qr_login.html', asset_id=asset_id)

@app.route('/qr_logout')
def custom_logout():
    """
    Handles logout for QR-based sessions
    """
    session.clear()
    return redirect('http://192.168.2.48:8835/login')


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect('http://192.168.2.48:8835/login')
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database()
            conn = mysql.connector.connect(**db_config)
            return conn
        else:
            print(err)
            return None

def create_database():
    try:
        conn = mysql.connector.connect(
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.close()
        conn.close()
        print(f"Database '{db_config['database']}' is ready.")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

def create_tables():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            #create
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS it_assets(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    asset_id VARCHAR(255) UNIQUE NOT NULL,
                    product_type VARCHAR(255) NOT NULL,
                    product_name VARCHAR(255) NOT NULL,
                    serial_no VARCHAR(255) NOT NULL,
                    make VARCHAR(255) NOT NULL,
                    model VARCHAR(255) NOT NULL,
                    part_no VARCHAR(255) NOT NULL,     
                    purchase_date DATE,      
                    vendor_name VARCHAR(255) ,
                    vendor_id VARCHAR(255) NOT NULL,
                    company_name VARCHAR(255) , 
                    location VARCHAR(255) NOT NULL,      
                    asset_type VARCHAR(255),
                    purchase_value DECIMAL(10, 2),
                    image_path VARCHAR(255),
                    purchase_bill_path VARCHAR(255),      
                    warranty_checked VARCHAR(255),
                    warranty_exists VARCHAR(255),
                    warranty_start DATE,
                    warranty_period VARCHAR(255),
                    warranty_end DATE,      
                    extended_warranty_exists  VARCHAR(255),
                    extended_warranty_period VARCHAR(255),
                    extended_warranty_end DATE,
                    adp_production VARCHAR(255),           
                    insurance VARCHAR(255),      
                    description TEXT,
                    remarks TEXT,       
                    product_age VARCHAR(255),
                    product_condition VARCHAR(255),
                    modified_by VARCHAR(255), 
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    has_user_details BOOLEAN,
                    asset_category VARCHAR(255) NOT NULL,
                    archieved VARCHAR(255),
                    has_amc VARCHAR(255),
                    recurring_alert_for_amc VARCHAR(255),
                    status_check_frequency VARCHAR(10) DEFAULT '3M',  -- New column: '3M' or '6M'
                    last_status_check DATE,                          -- New column: Date of last status check
                    next_status_check DATE,
                    under_audit VARCHAR(10) DEFAULT 'No',
                    audit_remarks TEXT
                    
                )
            """)

            #asset users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(100),
                    created_at DATETIME,
                    assignment_code VARCHAR(255) UNIQUE NOT NULL,
                    asset_id VARCHAR(255) NOT NULL,
                    assigned_user VARCHAR(255) NOT NULL,
                    employee_code VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    effective_date DATE,
			        end_date DATE,
                    modified_by VARCHAR(100),
                    modified_at DATETIME,
                    remarks TEXT,
                    confirmation_status VARCHAR(255),
                    acceptance_status VARCHAR(255),
                    token VARCHAR(255),
                    token_expiration DATETIME,
                    archieved VARCHAR(255),
                    overall_archieved VARCHAR(255) 
                )
            """)

            #vendor details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendor_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vendor_id VARCHAR(255) UNIQUE NOT NULL,
                vendor_name VARCHAR(255) NOT NULL,
                address TEXT,
                phone_number VARCHAR(20),
                email VARCHAR(255) NOT NULL,
                modified_by VARCHAR(100),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                remarks TEXT,
                archieved VARCHAR(255)
            )
            """)

            #service details
            cursor.execute("""
               CREATE TABLE IF NOT EXISTS service_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                service_id VARCHAR(255) UNIQUE NOT NULL,                 
                ticket_id VARCHAR(255) NOT NULL,
                asset_id VARCHAR(255) NOT NULL,
                reference_name VARCHAR(500),
                warranty_type VARCHAR(255) NOT NULL,
                service_case_id VARCHAR(255),    
                technician_source  VARCHAR(255) NOT NULL,
                technician_name VARCHAR(255) NOT NULL,
                technician_id VARCHAR(255) NOT NULL,
                work_done TEXT,
                next_service_date DATE,
                service_charge DECIMAL(10, 2),
                modified_by VARCHAR(100),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                remarks TEXT,
                multiple_service_bill_path VARCHAR(1000),
                multiple_service_id_no VARCHAR(255), 
                service_bill_path VARCHAR(1000),
                service_photo_path VARCHAR(1000),
                archieved VARCHAR(255),
                overall_archieved VARCHAR(255) 
            )

            """)

            #technician details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS technician_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    technician_id VARCHAR(255) UNIQUE NOT NULL,
                    technician_type VARCHAR(255) NOT NULL,
                    technician_name VARCHAR(255) UNIQUE NOT NULL,       
                    phone_number VARCHAR(20),
                    address TEXT,
                    email_address VARCHAR(255),
                    modified_by VARCHAR(100),
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    remarks TEXT,
                    archieved VARCHAR(255)     
                )
            """)
            
            #extended warranty details
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extended_warranty_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    warranty_asset_id VARCHAR(255) UNIQUE NOT NULL,
                    asset_id VARCHAR(255) NOT NULL,     
                    extended_warranty_start DATE,
                    extended_warranty_period VARCHAR(255),    
                    extended_warranty_end_date DATE,
                    warranty_provider_type VARCHAR(255),
                    warranty_provider_name VARCHAR(255),
                    warranty_provider_ph_no VARCHAR(255),
                    warranty_provider_location VARCHAR(255),
                    warranty_value DECIMAL(10, 2),
                    adp_protection VARCHAR(255) NOT NULL,
                    extended_warranty_bill_path VARCHAR(255),
                    product_condition VARCHAR(255),                           
                    modified_by VARCHAR(255), 
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    remarks TEXT,
                    archieved VARCHAR(255),
                    overall_archieved VARCHAR(255) 
                )
            """)

            #raised tickets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raised_tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ticket_id VARCHAR(255) UNIQUE NOT NULL,
                    asset_id VARCHAR(255) NOT NULL, 
                    raised_by VARCHAR(255) NOT NULL,
                    raised_emp_id VARCHAR(255) NOT NULL,
                    problem_description TEXT,                              
                    modified_by VARCHAR(255), 
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    ticket_status VARCHAR(255),
                    ignore_reason TEXT,
                    progress_notes TEXT,
                    replacement_issued VARCHAR(255),
                    replacement_asset_id VARCHAR(255),
                    replacement_reason VARCHAR(255),
                    remarks TEXT,
                    reraised_ticket VARCHAR(255) NOT NULL,
                    archieved VARCHAR(255),
                    overall_archieved VARCHAR(255)
                )
            """)

            #insurance
            cursor.execute("""
               CREATE TABLE IF NOT EXISTS insurance_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    insurance_id VARCHAR(255) UNIQUE NOT NULL,   
                    asset_id VARCHAR(255) NOT NULL,
                    policy_number VARCHAR(255) UNIQUE NOT NULL,
                    insurance_value DECIMAL(10, 2),
                    insurance_start DATE,
                    insurance_period VARCHAR(255),
                    insurance_end DATE,
                    insurance_bill_path VARCHAR(1500),
                    modified_by VARCHAR(255), 
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    remarks TEXT,
                    archieved VARCHAR(255),
                    overall_archieved VARCHAR(255) 
                )
            """)


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reraised_ticket_services (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    service_id VARCHAR(255) UNIQUE NOT NULL,
                    ticket_id VARCHAR(255) NOT NULL,
                    asset_id VARCHAR(255) NOT NULL,
                    reference_name VARCHAR(500),
                    warranty_type VARCHAR(255) NOT NULL,
                    service_case_id VARCHAR(255),
                    technician_name VARCHAR(255) NOT NULL,
                    technician_source VARCHAR(255) NOT NULL,
                    technician_id VARCHAR(255) NOT NULL,
                    work_done TEXT,
                    next_service_date DATE,
                    service_charge DECIMAL(10, 2),
                    modified_by VARCHAR(100),
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    remarks TEXT,
                    multiple_service_bill_path VARCHAR(1000),
                    multiple_service_id_no VARCHAR(255),
                    service_bill_path VARCHAR(1000),
                    service_photo_path VARCHAR(1000),
                    archieved VARCHAR(255),
                    overall_archieved VARCHAR(255),
                    FOREIGN KEY (ticket_id) REFERENCES raised_tickets(ticket_id),
                    FOREIGN KEY (asset_id) REFERENCES it_assets(asset_id)
                )
               """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_requests (
                    request_id VARCHAR(36) PRIMARY KEY, -- UUID for unique request ID
                    user_id VARCHAR(50) NOT NULL, -- Employee ID from session
                    username VARCHAR(100) NOT NULL, -- Username from session
                    product_needed TEXT NOT NULL, -- What product is needed
                    reason TEXT NOT NULL, -- Why the product is needed
                    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, rejected
                    rejection_reason TEXT, -- Reason for rejection, if any
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP NULL,
                    token VARCHAR(36), -- Verification token
                    token_expiration TIMESTAMP, -- Token expiration time
                    archieved VARCHAR(255) DEFAULT 'No',
                    overall_archieved VARCHAR(255) DEFAULT 'No'
                )
               """)
  
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wfh_asset_requests (
                request_id VARCHAR(36) PRIMARY KEY, -- UUID for unique request ID
                user_id VARCHAR(50) NOT NULL, -- Employee ID from session
                username VARCHAR(100) NOT NULL, -- Username from session
                asset_id VARCHAR(50) NOT NULL, -- Asset ID selected
                duration_days INT NOT NULL, -- Number of days
                start_date DATE NOT NULL, -- Start date
                end_date DATE NOT NULL, -- End date
                reason TEXT NOT NULL, -- Why the asset is needed for WFH
                status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, rejected
                rejection_reason TEXT, -- Reason for rejection, if any
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP NULL,
                token VARCHAR(36), -- Verification token
                token_expiration TIMESTAMP, -- Token expiration time
                archieved VARCHAR(255) DEFAULT 'No',
                overall_archieved VARCHAR(255) DEFAULT 'No'
                )
               """)
            

 
            
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            conn.close()
    else:
        print("Database connection failed.")


def generate_unique_id(prefix, count=1):
    if prefix == 'IT':
        table_name = 'it_assets'
    elif prefix == 'EW':
        table_name = 'extended_warranty_info'
    elif prefix == 'AU':
        table_name = 'assets_users'
    elif prefix == 'VD':
        table_name = 'vendor_details'
    elif prefix == 'SI':
        table_name = 'service_details'    
    elif prefix == 'TI':
        table_name = 'technician_details'
    elif prefix == 'RT':
        table_name = 'raised_tickets'
    elif prefix == 'INS':
        table_name = 'insurance_details'
    elif prefix == 'RTS':
        table_name = 'reraised_ticket_services'
    elif prefix == 'PR':
        table_name = 'product_requests'
    elif prefix == 'WFH':
        table_name = 'wfh_asset_requests'
    else:
        raise ValueError(f"Unsupported prefix: {prefix}")

    if prefix != 'SI':
        order_column = 'created_at'
    elif prefix == 'SI':
        order_column = 'service_id'

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the latest record
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY {order_column} DESC LIMIT 1")
    last_record = cursor.fetchone()

    current_date = datetime.now().strftime("%Y%m%d")
    new_ids = []

    if last_record is None:
        # If no records exist, start from 01
        last_number = 0
    else:
        # Assuming the unique key (e.g., service_id) is at index 3
        last_unique_key = last_record[3]
        last_number = int(last_unique_key[-2:])  # Extract last 2 digits

    # Generate the required number of IDs
    for i in range(count):
        new_number = last_number + i + 1
        new_id = f"{prefix}{current_date}-{new_number:02d}"
        new_ids.append(new_id)

    cursor.close()
    conn.close()

    return new_ids if count > 1 else new_ids[0]


def generate_qr_code(asset_id):
    """Generate a QR code pointing to the custom QR login page."""
    qr_url = f"http://192.168.2.48:8000/qr_login?asset_id={asset_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return qr_base64


# Email configuration (adjust as per your SMTP settings)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""



def send_verification_email(assignment_code, asset_id, assigned_user, email, to_email):
    # Generate a unique token
    token = str(uuid.uuid4())
    expiration_time = datetime.utcnow() + timedelta(days=2)  # Token expires in 2 days

    # Save token and expiration to the database
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            UPDATE assets_users 
            SET token = %s, token_expiration = %s, confirmation_status = NULL 
            WHERE assignment_code = %s
        """
        cursor.execute(query, (token, expiration_time, assignment_code))
        conn.commit()
        cursor.close()
        conn.close()

    # Generate verification URLs
    accept_url = url_for('confirm_user_asset', assignment_code=assignment_code, token=token, action='accept', _external=True)
    reject_url = url_for('confirm_user_asset', assignment_code=assignment_code, token=token, action='reject', _external=True)

    # HTML email template with night blue text and styled buttons
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: #191970;
                color: #ffffff;
                padding: 10px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                padding: 20px;
                color: #191970; /* Night blue text */
            }}
            .button {{
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                display: inline-block;
                margin: 5px;
            }}
            .accept {{
                background-color: #28a745; /* Green */
                color: #ffffff;
            }}
            .reject {{
                background-color: #dc3545; /* Red */
                color: #ffffff;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #666;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Asset Assignment Verification</h2>
            </div>
            <div class="content">
                <p>Dear {assigned_user},</p>
                <p>You have been assigned a new asset. Please confirm your acceptance or rejection by clicking one of the buttons below:</p>
                <p><strong>Asset ID:</strong> {asset_id}</p>
                <p><strong>Assignment Code:</strong> {assignment_code}</p>
                <p>
                    <a href="{accept_url}" class="button accept">Accept Asset</a>
                    <a href="{reject_url}" class="button reject">Reject Asset</a>
                </p>
                <p>This link will expire in 2 days. Please respond promptly.</p>
            </div>
            <div class="footer">
                Regards,<br>Asset Management Team
            </div>
        </div>
    </body>
    </html>
    """

    # Send the email
    subject = "Asset Assignment Verification"
    send_email_with_cc(to_email, subject, html_body, cc_email='nivetha@tapmobi.in')



def send_email_with_cc(to_email, subject, html_body, cc_email=None):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = 'nivetha@tapmobi.in'
    SMTP_PASSWORD = 'btiuophjhxobtpet'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    # Handle CC list or string
    if cc_email:
        if isinstance(cc_email, list):
            msg['Cc'] = ', '.join(cc_email)
            cc_list = cc_email
        else:
            msg['Cc'] = cc_email
            cc_list = [cc_email]
    else:
        cc_list = []

    # Plain text fallback
    plain_body = "This email requires HTML support to view properly.\n\n"
    for line in html_body.split('\n'):
        if '<td>' in line and '</td>' in line:
            parts = line.split('<td>')
            if len(parts) > 2:
                key = parts[1].replace('</td>', '').strip()
                value = parts[2].replace('</td>', '').strip()
                plain_body += f"{key}: {value}\n"

    msg.attach(MIMEText(plain_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    # Send email to both To and CC recipients
    recipients = [to_email] + cc_list

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, recipients, msg.as_string())


# Existing send_confirmation_email function (assumed to be present)
def send_confirmation_email(action, entity_type, entity_id, details, to_email='nivetha@tapmobi.in', cc_email=None):
    action_map = {
        'create': 'Created',
        'edit': 'Updated',
        'ignore': 'Ignored'
    }
    action_text = action_map.get(action, action.capitalize())
    entity_display = entity_type.replace('_', ' ').capitalize()
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 20px; color: #191970; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f0f0f0; color: #191970; }}
            .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{entity_display} {action_text}</h2>
            </div>
            <div class="content">
                <p>Dear {'User' if entity_type == 'user_asset' else 'Admin'},</p>
                <p>The following {entity_display.lower()} has been {action_text.lower()}:</p>
                <table>
                    <tr><th>Field</th><th>Value</th></tr>
                    <tr><td>{entity_display} ID</td><td>{entity_id}</td></tr>
    """
    for key, value in details.items():
        html_body += f"<tr><td>{key.replace('_', ' ').capitalize()}</td><td>{value}</td></tr>"
    html_body += """
                </table>
            </div>
            <div class="footer">
                Regards,<br>Asset Management Team
            </div>
        </div>
    </body>
    </html>
    """
    subject = f"{entity_display} {action_text} Confirmation"
    send_email_with_cc(to_email, subject, html_body, cc_email)

# New send_verification_email function using existing send_email_with_cc
def send_verification_email(assignment_code, asset_id, assigned_user, to_email):
    token = str(uuid.uuid4())
    expiration_time = datetime.utcnow() + timedelta(days=2)

    # Save token and expiration to the database
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            UPDATE assets_users 
            SET token = %s, token_expiration = %s, confirmation_status = NULL 
            WHERE assignment_code = %s
        """
        cursor.execute(query, (token, expiration_time, assignment_code))
        conn.commit()
        cursor.close()
        conn.close()

    # Generate verification URLs
    accept_url = url_for('confirm_user_asset', assignment_code=assignment_code, token=token, action='accept', _external=True)
    reject_url = url_for('confirm_user_asset', assignment_code=assignment_code, token=token, action='reject', _external=True)

    # HTML email template with styled buttons
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 20px; color: #191970; }}
            .button {{ padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 5px; }}
            .accept {{ background-color: #28a745; color: #ffffff; }}
            .reject {{ background-color: #dc3545; color: #ffffff; }}
            .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Asset Assignment Verification</h2>
            </div>
            <div class="content">
                <p>Dear {assigned_user},</p>
                <p>You have been assigned a new asset. Please confirm your acceptance or rejection:</p>
                <p><strong>Asset ID:</strong> {asset_id}</p>
                <p><strong>Assignment Code:</strong> {assignment_code}</p>
                <p>
                    <a href="{accept_url}" class="button accept">Accept Asset</a>
                    <a href="{reject_url}" class="button reject">Reject Asset</a>
                </p>
                <p>This link will expire in 2 days.</p>
            </div>
            <div class="footer">
                Regards,<br>Asset Management Team
            </div>
        </div>
    </body>
    </html>
    """

    subject = "Asset Assignment Verification"
    send_email_with_cc(to_email, subject, html_body, cc_email=['nivetha@tapmobi.in'])


@app.route('/confirm_user_asset/<assignment_code>/<token>/<action>', methods=['GET'])
def confirm_user_asset(assignment_code, token, action):
    conn = get_db_connection()
    if not conn:
        return render_template('response_message.html', message="Database connection failed.")

    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT token, token_expiration, confirmation_status, asset_id, assigned_user, email 
        FROM assets_users 
        WHERE assignment_code = %s
    """, (assignment_code,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="Invalid assignment code.")

    stored_token = result['token']
    token_expiration = result['token_expiration']
    confirmation_status = result['confirmation_status']
    asset_id = result['asset_id']
    assigned_user = result['assigned_user']
    to_email = result['email'] if result['email'] else 'nivetha@tapmobi.in'

    if stored_token != token:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="Invalid or incorrect token.")

    current_time = datetime.utcnow()
    if current_time > token_expiration:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="This verification link has expired. Please contact IT support.")

    if confirmation_status is not None:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="This asset assignment has already been responded to.")

    # Determine acceptance status
    acceptance_status = 'accepted' if action == 'accept' else 'rejected'
    confirmation_status = '1' if action == 'accept' else '0'

    # Update the assets_users table
    cursor.execute("""
        UPDATE assets_users 
        SET confirmation_status = %s, 
            acceptance_status = %s, 
            token = NULL, 
            token_expiration = NULL 
        WHERE assignment_code = %s
    """, (confirmation_status, acceptance_status, assignment_code))
    conn.commit()

    # Prepare email details
    details = {
        'assignment_code': assignment_code,
        'asset_id': asset_id,
        'assigned_user': assigned_user,
        'acceptance_status': acceptance_status,
        'response_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Send email notification
    send_confirmation_email(
        action='update', 
        entity_type='asset_assignment', 
        entity_id=assignment_code, 
        details=details, 
        to_email=to_email,  # Send to assigned user's email
        cc_email='nivetha@tapmobi.in'  # CC to admin
    )

    cursor.close()
    conn.close()
    return render_template('response_message.html', message=f"Thank you for your response. The asset assignment has been {acceptance_status}.")

@app.route('/')
@login_required
def home():
    permissions = get_permissions(session)
    role = permissions.get('role')

    if role == 'admin' or role == 'manager':
        return redirect(url_for('it_dashboard'))
    elif role == 'employee':
        return redirect(url_for('view_assets'))
    else:
        return redirect(url_for('login'))  # Redirect to login if no role is found

@app.route('/add_new_option', methods=['POST'])
@login_required
def add_new_option():
    if request.method == 'POST':
        data = request.json
        option_type = data.get('type')
        new_option = data.get('newValue')

        if option_type and new_option:
            try:
                if option_type == 'asset_category':
                    column_name = 'asset_category'

                elif option_type == 'product_type':
                    column_name = 'product_type'

                elif option_type == 'company_name':
                    column_name = 'company_name'

                elif option_type == 'asset_type':
                    column_name = 'asset_type'

                elif option_type == 'location':
                    column_name = 'location'

                elif option_type == 'product_condition':
                    column_name = 'product_condition'

                else:
                    return jsonify({'error': 'Invalid option type'}), 400
                
                conn = get_db_connection()
                cursor = conn.cursor()
                print(column_name, new_option)
                cursor.execute(f"INSERT INTO dropdown_attributes ({column_name}) VALUES (%s)", (new_option,))
                conn.commit()
                cursor.close()
                return jsonify({'message': f'New {option_type} added successfully'}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Invalid request'}), 400

@app.route('/delete_option', methods=['POST'])
@login_required
def delete_option():
    if request.method == 'POST':
        data = request.json
        option_type = data.get('type')
        option_value = data.get('value')

        if option_type and option_value:
            try:
                if option_type == 'asset_category':
                    column_name = 'asset_category'

                elif option_type == 'product_type':
                    column_name = 'product_type'

                elif option_type == 'company_name':
                    column_name = 'company_name'

                elif option_type == 'asset_type':
                    column_name = 'asset_type'

                elif option_type == 'location':
                    column_name = 'location'

                elif option_type == 'product_condition':
                    column_name = 'product_condition'

                else:
                    return jsonify({'error': 'Invalid option type'}), 400

                conn = get_db_connection()
                cursor = conn.cursor()
                print(column_name, option_value)
                cursor.execute(
                    f"DELETE FROM dropdown_attributes WHERE {column_name} = %s",
                    (option_value,)
                )
                conn.commit()
                cursor.close()
                return jsonify({'message': f'{option_type} option deleted successfully'}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Invalid request'}), 400


def display_drop_down(page):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if page == 'Create_Asset':
        cursor.execute("""
            SELECT DISTINCT product_type, company_name, asset_category, asset_type, product_condition, location
            FROM dropdown_attributes
        """)

        product_types, companies, asset_categories, asset_types,locations, product_conditions  = set(), set(), set(), set(), set(), set()
        dropdown = cursor.fetchall()

        for row in dropdown:
            if row['product_type']:
                product_types.add(row['product_type'])
            if row['company_name']:
                companies.add(row['company_name'])
            if row['asset_category']:
                asset_categories.add(row['asset_category'])
            if row['asset_type']:
                asset_types.add(row['asset_type'])
            if row['product_condition']:
                product_conditions.add(row['product_condition'])
            if row['location']:
                locations.add(row['location'])

        result = {
            "product_types": list(product_types),
            "companies": list(companies),
            "asset_categories": list(asset_categories),
            "asset_types": list(asset_types),
            "locations":list(locations),
            "product_conditions":list(product_conditions),
        }

    elif page == 'Create_Vendor':
        cursor.execute("""
            SELECT vendor_id, vendor_name FROM vendor_details
        """)

        vendors = cursor.fetchall()

        result = {
            "vendors": vendors  # List of dictionaries with 'vendor_id' & 'vendor_name'
        }

    elif page == 'Create_Technician':
        cursor.execute("""
            SELECT technician_id, technician_name FROM technician_details
        """)

        technicians = cursor.fetchall()

        result = {
            "technicians": technicians  # List of dictionaries with 'technician_id' & 'technician_name'
        }

    elif page == 'Create_Extended_Warranty':
        cursor.execute("""
            SELECT product_condition FROM dropdown_attributes
        """)


        # product_conditions = [row[0] for row in cursor.fetchall() if row[0] is not None]
        product_conditions = [row for row in cursor.fetchall() if row is not None]

        result = {
            "product_conditions": product_conditions  # List of dictionaries with 'technician_id' & 'technician_name'
        }
    

    # Close the cursor & connection AFTER fetching the data
    cursor.close()
    conn.close()

    return result

@app.route('/create_asset', methods=['GET', 'POST'])
@login_required
def create_asset():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_assets')
    header_perms = get_permissions(session, 'header')

    dropdown_data = display_drop_down('Create_Asset')
    product_types, companies, asset_categories, asset_types,locations, product_conditions  = dropdown_data.values()
    vendors_data = display_drop_down('Create_Vendor')
    vendors = vendors_data['vendors']

    cursor.close()
    conn.close()

    # Only use form_state if redirected from save_form_state or create_vendor
    if request.referrer and ('save_form_state' in request.referrer or 'create_vendor' in request.referrer):
        form_state = session.get('form_state', {})
    else:
        form_state = {}
        if 'form_state' in session:
            session.pop('form_state')  # Clear session on fresh load

    

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection failed!", "create_asset")
                return redirect(url_for('create_asset'))
            
            cursor = conn.cursor()
            created_by = session['username']
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            asset_id = generate_unique_id('IT')
            product_type = request.form['product_type']
            product_name = request.form['product_name']
            serial_no = request.form['serial_no']
            make = request.form['make']
            model = request.form['model']
            part_no = request.form['part_no']

            purchase_date = request.form['purchase_date']
            vendor_name = request.form['vendor_name']
            vendor_id = request.form.get('vendor_id')  # Get from hidden input, not hardcoded
            company_name = request.form['company_name']
            asset_type = request.form['asset_type']
            purchase_value = request.form['purchase_value']
            location = request.form['location']
            under_audit = request.form['under_audit']

            # Validate vendor_id
            if not vendor_id:
                flash("Vendor ID is required!", "create_asset")
                return redirect(url_for('create_asset'))

            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            asset_images_folder = os.path.join(asset_folder, 'Asset_Images')
            purchase_bills_folder = os.path.join(asset_folder, 'Purchase_Bills')

            os.makedirs(asset_images_folder, exist_ok=True)
            os.makedirs(purchase_bills_folder, exist_ok=True)

            # Handle Asset Image Uploads
            asset_images = []
            if 'asset_image[]' in request.files:
                files = request.files.getlist('asset_image[]')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(asset_images_folder, filename)
                        file.save(filepath)
                        asset_images.append(filename)

            # Handle Purchase Bill Uploads
            purchase_bills = []
            if 'purchase_bill[]' in request.files:
                files = request.files.getlist('purchase_bill[]')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(purchase_bills_folder, filename)
                        file.save(filepath)
                        purchase_bills.append(filename)

            asset_images_str = ','.join(asset_images)
            purchase_bills_str = ','.join(purchase_bills)

            warranty_checked = request.form.get('warranty_checked', 'No')
            warranty_exists = request.form.get('warranty_exists', 'No')
            warranty_start = request.form.get('warranty_start') or None

            warranty_period_dict = {
                "years": int(request.form.get("warranty_period_years", 0) or 0),
                "months": int(request.form.get("warranty_period_months", 0) or 0),
                "days": int(request.form.get("warranty_period_days", 0) or 0),
            }
            warranty_period = json.dumps(warranty_period_dict)
            warranty_end = request.form.get('warranty_end') or None

            extended_warranty_exists = request.form.get('extended_warranty_exists', 'No')
            extended_warranty_period_dict = {
                "years": int(request.form.get("extended_warranty_period_years", 0) or 0),
                "months": int(request.form.get("extended_warranty_period_months", 0) or 0),
                "days": int(request.form.get("extended_warranty_period_days", 0) or 0),
            }
            extended_warranty_period = json.dumps(extended_warranty_period_dict)
            extended_warranty_end = request.form.get('extended_warranty_end') or None
            
            adp_production = request.form.get('adp_production')
            insurance = request.form.get('insurance')
            description = request.form.get('description')
            remarks = request.form.get('remarks')
            product_age = request.form.get('product_age')
            product_condition = request.form.get('product_condition')
            asset_category = request.form['asset_category']
            
            archieved = request.form.get('archieved', 'No')
            has_user_details = request.form.get('has_user_details', 'No') == 'Yes'
            has_amc = request.form.get('has_amc', 'No') == 'Yes'
            
            recurring_alert_keys = request.form.getlist('recurring_alert_key[]')
            recurring_alert_values = request.form.getlist('recurring_alert_value[]')
            recurring_alert_units = request.form.getlist('recurring_alert_unit[]')
            recurring_alert_for_amc = str(list(zip(recurring_alert_keys, recurring_alert_values, recurring_alert_units)))

           

            query = """
                INSERT INTO it_assets (
                    created_by, created_at, asset_id, product_type, product_name, serial_no, make, model, part_no, 
                    purchase_date, vendor_name, vendor_id, company_name, asset_type, purchase_value, 
                    warranty_checked, warranty_exists, warranty_start, warranty_period, warranty_end,
                    extended_warranty_exists, extended_warranty_period, extended_warranty_end,
                    adp_production, insurance, description, remarks, product_age, product_condition,
                    asset_category, archieved, has_user_details, has_amc, recurring_alert_for_amc,
                    image_path, purchase_bill_path, under_audit, location
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                created_by, created_at, asset_id, product_type, product_name, serial_no, make, model, part_no, 
                purchase_date, vendor_name, vendor_id, company_name, asset_type, purchase_value, 
                warranty_checked, warranty_exists, warranty_start, warranty_period, warranty_end,
                extended_warranty_exists, extended_warranty_period, extended_warranty_end,
                adp_production, insurance, description, remarks, product_age, product_condition,
                asset_category, archieved, has_user_details, has_amc, recurring_alert_for_amc,
                asset_images_str, purchase_bills_str,under_audit, location
            )

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            if 'form_state' in session:
                session.pop('form_state')

            details = {
                'asset_id': asset_id,
                'product_type': product_type,
                'product_name': product_name,
                'serial_no': serial_no,
                'make': make,
                'model': model,
                'purchase_date': purchase_date,
                'vendor_name': vendor_name,
                'vendor_id': vendor_id,
                'company_name': company_name,
                'asset_type': asset_type,
                'purchase_value': purchase_value if purchase_value else 'Not Set',
                'location': location,
                'warranty_exists': warranty_exists,
                'warranty_start': warranty_start if warranty_start else 'Not Set',
                'warranty_period': f"{warranty_period_dict['years']} years, {warranty_period_dict['months']} months, {warranty_period_dict['days']} days",
                'warranty_end': warranty_end if warranty_end else 'Not Set',
                'extended_warranty_exists': extended_warranty_exists,
                'extended_warranty_end': extended_warranty_end if extended_warranty_end else 'Not Set',
                'image_path': asset_images_str,
                'purchase_bill_path': purchase_bills_str,
                'created_by': created_by,
                'created_at': created_at,
                'remarks': remarks if remarks else 'None'
            }
            send_confirmation_email('create', 'asset', asset_id, details)
            send_confirmation_email('create', 'asset', asset_id, details)

            flash("Asset successfully created!", "create_asset")
            return redirect(url_for('create_asset'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'create_asset')
            cursor.close()
            conn.close()
            return redirect(url_for('create_asset'))

    return render_template('create_asset.html', 
                           product_types=product_types, 
                           companies=companies,
                           asset_categories=asset_categories,
                           asset_types=asset_types,
                           product_conditions = product_conditions,
                           locations = locations,
                           vendors=vendors,
                           form_state=form_state,
                            permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
                        )

@app.route('/edit_asset/<asset_id>', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_assets')
    header_perms = get_permissions(session, 'header')

    product_types, companies, asset_categories, asset_types, locations, product_conditions = display_drop_down('Create_Asset').values()
    vendors_data = display_drop_down('Create_Vendor')
    vendors = vendors_data['vendors']

    if request.method == 'POST':
        try:
            # Fetch existing file paths (filenames only)
            cursor.execute("SELECT image_path, purchase_bill_path FROM it_assets WHERE asset_id = %s", (asset_id,))
            existing_data = cursor.fetchone()
            existing_images = existing_data['image_path'].split(',') if existing_data['image_path'] else []
            existing_bills = existing_data['purchase_bill_path'].split(',') if existing_data['purchase_bill_path'] else []

            # Get removed files from form (filenames only)
            removed_images = request.form.get('removed_images', '').split(',') if request.form.get('removed_images') else []
            removed_bills = request.form.get('removed_bills', '').split(',') if request.form.get('removed_bills') else []

            # Update file lists by removing specified files
            asset_images = [img for img in existing_images if img not in removed_images]
            purchase_bills = [bill for bill in existing_bills if bill not in removed_bills]

            # Handle new Asset Image Uploads
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            asset_images_folder = os.path.join(asset_folder, 'Asset_Images')
            os.makedirs(asset_images_folder, exist_ok=True)
            if 'asset_image[]' in request.files:
                files = request.files.getlist('asset_image[]')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(asset_images_folder, filename)
                        file.save(filepath)
                        if filename not in asset_images:
                            asset_images.append(filename)

            # Handle new Purchase Bill Uploads
            purchase_bills_folder = os.path.join(asset_folder, 'Purchase_Bills')
            os.makedirs(purchase_bills_folder, exist_ok=True)
            if 'purchase_bill[]' in request.files:
                files = request.files.getlist('purchase_bill[]')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(purchase_bills_folder, filename)
                        file.save(filepath)
                        if filename not in purchase_bills:
                            purchase_bills.append(filename)

            asset_images_str = ','.join(asset_images) if asset_images else ''
            purchase_bills_str = ','.join(purchase_bills) if purchase_bills else ''

            # Rest of the form data
            product_type = request.form['product_type']
            product_name = request.form['product_name']
            serial_no = request.form['serial_no']
            make = request.form['make']
            model = request.form['model']
            part_no = request.form['part_no']
            purchase_date = request.form['purchase_date']
            vendor_name = request.form['vendor_name']
            vendor_id = request.form['vendor_id']
            company_name = request.form['company_name']
            asset_type = request.form['asset_type']
            purchase_value = request.form['purchase_value']
            location = request.form['location']

            warranty_checked = request.form.get('warranty_checked', 'No')
            warranty_exists = request.form.get('warranty_exists', 'No')
            warranty_start = request.form.get('warranty_start') or None
            warranty_period_dict = {
                "years": int(request.form.get("warranty_period_years", 0) or 0),
                "months": int(request.form.get("warranty_period_months", 0) or 0),
                "days": int(request.form.get("warranty_period_days", 0) or 0),
            }
            warranty_period = json.dumps(warranty_period_dict)
            warranty_end = request.form.get('warranty_end') or None

            extended_warranty_exists = request.form.get('extended_warranty_exists', 'No')
            extended_warranty_period_dict = {
                "years": int(request.form.get("extended_warranty_period_years", 0) or 0),
                "months": int(request.form.get("extended_warranty_period_months", 0) or 0),
                "days": int(request.form.get("extended_warranty_period_days", 0) or 0),
            }
            extended_warranty_period = json.dumps(extended_warranty_period_dict)
            extended_warranty_end = request.form.get('extended_warranty_end') or None

            adp_production = request.form['adp_production']
            insurance = request.form['insurance']
            description = request.form['description']
            remarks = request.form['remarks']
            product_age = request.form['product_age']
            product_condition = request.form['product_condition']
            asset_category = request.form['asset_category']
            archieved = request.form.get('archieved', 'No')
            has_user_details = request.form.get('has_user_details', 'No') == 'Yes'
            has_amc = request.form.get('has_amc', 'No') == 'Yes'
            under_audit = request.form['under_audit']

            recurring_alert_keys = request.form.getlist('recurring_alert_key[]')
            recurring_alert_values = request.form.getlist('recurring_alert_value[]')
            recurring_alert_units = request.form.getlist('recurring_alert_unit[]')
            recurring_alert_for_amc = str(list(zip(recurring_alert_keys, recurring_alert_values, recurring_alert_units)))

            modified_by = session.get('username')

            update_query = """
                UPDATE it_assets SET 
                    product_type=%s, product_name=%s, serial_no=%s, make=%s, model=%s, part_no=%s, 
                    purchase_date=%s, vendor_name=%s, vendor_id=%s, company_name=%s, asset_type=%s, 
                    purchase_value=%s, warranty_checked=%s, warranty_exists=%s, warranty_start=%s, 
                    warranty_period=%s, warranty_end=%s, extended_warranty_exists=%s, 
                    extended_warranty_period=%s, extended_warranty_end=%s, adp_production=%s, 
                    insurance=%s, description=%s, remarks=%s, product_age=%s, product_condition=%s, 
                    asset_category=%s, archieved=%s, has_user_details=%s, has_amc=%s, 
                    recurring_alert_for_amc=%s, image_path=%s, purchase_bill_path=%s, under_audit=%s, location=%s,
                    modified_by=%s, modified_at=NOW()
                WHERE asset_id=%s
            """
            values = (
                product_type, product_name, serial_no, make, model, part_no, purchase_date, 
                vendor_name, vendor_id, company_name, asset_type, purchase_value, warranty_checked, 
                warranty_exists, warranty_start, warranty_period, warranty_end, extended_warranty_exists, 
                extended_warranty_period, extended_warranty_end, adp_production, insurance, 
                description, remarks, product_age, product_condition, asset_category, archieved, 
                has_user_details, has_amc, recurring_alert_for_amc, asset_images_str, purchase_bills_str, under_audit, location,
                modified_by, asset_id
            )

            cursor.execute(update_query, values)
            conn.commit()

            details = {
                'asset_id': asset_id,
                'product_type': product_type,
                'product_name': product_name,
                'serial_no': serial_no,
                'make': make,
                'model': model,
                'purchase_date': purchase_date,
                'vendor_name': vendor_name,
                'vendor_id': vendor_id,
                'company_name': company_name,
                'asset_type': asset_type,
                'purchase_value': purchase_value if purchase_value else 'Not Set',
                'location': location,
                'warranty_exists': warranty_exists,
                'warranty_start': warranty_start if warranty_start else 'Not Set',
                'warranty_period': f"{warranty_period_dict['years']} years, {warranty_period_dict['months']} months, {warranty_period_dict['days']} days",
                'warranty_end': warranty_end if warranty_end else 'Not Set',
                'extended_warranty_exists': extended_warranty_exists,
                'extended_warranty_end': extended_warranty_end if extended_warranty_end else 'Not Set',
                'image_path': asset_images_str,
                'purchase_bill_path': purchase_bills_str,
                'modified_by': modified_by,
                'modified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'remarks': remarks if remarks else 'None'
            }
            send_confirmation_email('edit', 'asset', asset_id, details)

            flash("Asset successfully updated!", "edit_asset")
            cursor.close()
            conn.close()
            return redirect(url_for('view_assets'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'edit_asset')
            cursor.close()
            conn.close()

    # GET request: Fetch asset details
    cursor.execute("SELECT * FROM it_assets WHERE asset_id = %s", (asset_id,))
    asset = cursor.fetchone()
    if not asset:
        flash('Asset not found!', 'view_assets')
        cursor.close()
        conn.close()
        return redirect(url_for('view_assets'))

    asset['has_amc'] = 'Yes' if str(asset['has_amc']) in ('1', 'True', 1, True) else 'No'

    from_create_vendor = request.referrer and 'create_vendor' in request.referrer
    if from_create_vendor:
        asset['vendor_name'] = None
        asset['vendor_id'] = None
        print('Returning from create_vendor, cleared vendor_name and vendor_id')

    form_state = session.get('form_state', {}) if request.referrer and 'create_vendor' in request.referrer else {}
    if from_create_vendor and 'form_state' in session:
        form_state['vendor_name'] = ['']
        form_state['vendor_id'] = ['']
        session['form_state'] = form_state

    cursor.close()
    conn.close()

    warranty_period_dict = json.loads(asset['warranty_period']) if asset['warranty_period'] else {"years": 0, "months": 0, "days": 0}
    extended_warranty_period_dict = json.loads(asset['extended_warranty_period']) if asset['extended_warranty_period'] else {"years": 0, "months": 0, "days": 0}
    recurring_alert_list = ast.literal_eval(asset['recurring_alert_for_amc']) if asset['recurring_alert_for_amc'] else []
    return render_template('edit_asset.html', 
                           asset=asset, 
                           product_types=product_types, 
                           companies=companies,
                           asset_categories=asset_categories,
                           asset_types=asset_types,
                           product_conditions=product_conditions,
                           locations=locations,
                           vendors=vendors,
                           warranty_period_dict=warranty_period_dict,
                           extended_warranty_period_dict=extended_warranty_period_dict,
                           recurring_alert_list=recurring_alert_list,
                           form_state=form_state,
                           permissions=page_perms['permissions'],
                           role=page_perms['role'],
                           header_permissions=header_perms['permissions'],
                           asset_id=asset_id  # Pass asset_id explicitly
                           )


@app.route('/view_assets', methods=['GET'])
@login_required
def view_assets():
    permissions = get_permissions(session, 'view_assets')
    user_id = session.get('IOMS_emp_id')

    print('user_id view',user_id )

    conn = get_db_connection()
    cursor = conn.cursor()
    filter_type = request.args.get('filter')

    # Base query for all assets
    base_query = """
        WITH latest_user_assignments AS (
            SELECT *
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY created_at DESC) AS rn
                FROM vayu_asset_management.assets_users
                WHERE archieved = 'No' AND overall_archieved = 'No'
            ) sub
            WHERE rn = 1
        )

        SELECT 
            ia.id, ia.created_by, ia.created_at, ia.asset_id, ia.product_type, ia.product_name, 
            ia.serial_no, ia.make, ia.model, ia.part_no, ia.purchase_date, ia.vendor_name, 
            ia.vendor_id, ia.company_name, ia.asset_type, ia.purchase_value, ia.image_path,
            ia.purchase_bill_path, ia.warranty_checked, ia.warranty_exists, 
            ia.warranty_start, ia.warranty_period, ia.warranty_end, 
            ia.extended_warranty_exists, ia.extended_warranty_period, 
            ia.extended_warranty_end, ia.adp_production, ia.insurance, ia.description,
            ia.remarks, ia.product_age, ia.product_condition, ia.modified_by, 
            ia.modified_at, ia.has_user_details, ia.asset_category, ia.archieved,
            ia.has_amc, ia.recurring_alert_for_amc,
            
            au.effective_date, au.end_date, au.confirmation_status, au.assignment_code

        FROM vayu_asset_management.it_assets ia
        LEFT JOIN latest_user_assignments au ON ia.asset_id = au.asset_id;

    """

    # Modify query based on role
    if permissions['role'] == 'employee' and user_id:
        print('view page role', user_id, 'employee')
        # For employees, only show assets assigned to them
        query = f"""
            {base_query}
            WHERE (ia.archieved != 'yes' OR ia.archieved IS NULL)
            AND au.employee_code = %s
            AND au.confirmation_status = 1
            AND (au.end_date IS NULL OR au.end_date > CURRENT_DATE)
        """
        cursor.execute(query, (user_id,))
    else:
        print('view page role', user_id, 'else loop')
        # For admin and manager, show all non-archived assets
        query = f"""
            {base_query}
            WHERE (ia.archieved != 'yes' OR ia.archieved IS NULL)
        """
        cursor.execute(query)

    all_assets = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    assets_list = [dict(zip(columns, asset)) for asset in all_assets]

    filtered_assets = []
    for asset in assets_list:
        effective_date = asset['effective_date']
        end_date = asset['end_date']
        confirmation_status = int(asset['confirmation_status']) if asset['confirmation_status'] is not None else None
        
        if filter_type == "assigned":
            if effective_date and not end_date and confirmation_status == 1:
                filtered_assets.append(asset)

        elif filter_type == "unauthorized":
            if effective_date and not end_date and confirmation_status is None:
                filtered_assets.append(asset)
            
        elif filter_type == "unassigned":
            if (
                (effective_date is None and end_date is None) or
                (effective_date and end_date is not None) or
                (not (effective_date and not end_date and confirmation_status == 1)) and
                (not (effective_date and not end_date and confirmation_status is None))
            ):
                filtered_assets.append(asset)
            
            

        elif filter_type in [None, "all"]:
            filtered_assets.append(asset)



    for asset in filtered_assets:
        if permissions['role'] in ['admin', 'manager']:
            asset['qr_code_base64'] = generate_qr_code(asset['asset_id'])
        else:
            asset['qr_code_base64'] = None

    cursor.close()
    conn.close()

    today = date.today()
    header_perms = get_permissions(session, 'header')
    return render_template(
        'view_assets.html',
        all_assets=filtered_assets,
        today=today,
        permissions=permissions,
        header_permissions=header_perms['permissions']
    )

@app.route('/view_asset_details/<asset_id>', methods=['GET'])
@login_required
def view_asset_details(asset_id):
    """Render a page with detailed information about a specific asset."""
    permissions = get_permissions(session, 'view_assets')

    if not permissions['permissions'].get('view_details', False):
        return "Unauthorized", 403
    
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT ia.id, ia.created_by, ia.created_at, ia.asset_id, ia.product_type, ia.product_name, 
               ia.serial_no, ia.make, ia.model, ia.part_no, ia.purchase_date, ia.vendor_name, 
               ia.vendor_id,ia.location, ia.company_name, ia.asset_type, ia.purchase_value, ia.image_path,
               ia.purchase_bill_path, ia.warranty_checked, ia.warranty_exists, 
               ia.warranty_start, ia.warranty_period, ia.warranty_end, 
               ia.extended_warranty_exists, ia.extended_warranty_period, 
               ia.extended_warranty_end, ia.adp_production, ia.insurance, ia.description,
               ia.remarks, ia.product_age, ia.product_condition, ia.modified_by, 
               ia.modified_at, ia.has_user_details, ia.asset_category, ia.archieved,
               ia.has_amc, ia.recurring_alert_for_amc
        FROM vayu_asset_management.it_assets ia
        WHERE ia.asset_id = %s AND (ia.archieved != 'yes' OR ia.archieved IS NULL)
    """
    cursor.execute(query, (asset_id,))
    asset = cursor.fetchone()
    print(asset)

    asset = list(asset)

    # Safely parse the last field if it's a string that looks like a list of tuples
    if asset[-1] and isinstance(asset[-1], str):
        try:
            parsed = ast.literal_eval(asset[-1])
            
            if isinstance(parsed, list) and all(isinstance(item, tuple) for item in parsed):
                # For each tuple (event, number, unit), format the string accordingly
                alert_descriptions = [
                    f"Alert for {event} triggered {num} {unit} once \n" for event, num, unit in parsed
                ]
                # Join all the alerts together if there are multiple
                asset[-1] = ', '.join(alert_descriptions)
        except (ValueError, SyntaxError):
            # Fallback in case the string isn't valid Python literal
            pass

    # Then continue with:


    

    print(asset)

    if not asset:
        cursor.close()
        conn.close()
        abort(404)

    columns = [desc[0] for desc in cursor.description]
    asset_dict = dict(zip(columns, asset))

    related_data = {
        'service_details': [],
        'raised_tickets': [],
        'extended_warranty_info': [],
        'insurance_details': []
    }

    # Fetch service details with archive conditions
    cursor.execute("""
        SELECT 
            sd.service_id, sd.warranty_type, sd.ticket_id, sd.work_done, 
            sd.next_service_date, sd.service_charge
        FROM service_details sd
        WHERE sd.asset_id = %s
            AND (sd.archieved != 'yes' OR sd.archieved IS NULL)
            AND sd.overall_archieved = 'No'

        UNION

        SELECT 
            rts.service_id, rts.warranty_type, rts.ticket_id, rts.work_done, 
            rts.next_service_date, rts.service_charge
        FROM reraised_ticket_services rts
        WHERE rts.asset_id = %s
            AND (rts.archieved != 'yes' OR rts.archieved IS NULL)
            AND rts.overall_archieved = 'No'
    """, (asset_id, asset_id))
    service_details = cursor.fetchall()
    service_columns = [desc[0] for desc in cursor.description]
    related_data['service_details'] = [dict(zip(service_columns, row)) for row in service_details]

    # Fetch raised tickets with archive conditions
    cursor.execute("""
        SELECT rt.ticket_id, rt.problem_description, rt.ticket_status, rt.replacement_asset_id
        FROM raised_tickets rt
        WHERE rt.asset_id = %s
        AND (rt.archieved != 'yes' OR rt.archieved IS NULL)
        AND rt.overall_archieved = 'No'
    """, (asset_id,))
    raised_tickets = cursor.fetchall()
    ticket_columns = [desc[0] for desc in cursor.description]
    related_data['raised_tickets'] = [dict(zip(ticket_columns, row)) for row in raised_tickets]

    # Fetch extended warranty info with archive conditions
    cursor.execute("""
        SELECT ew.warranty_asset_id, ew.extended_warranty_start, ew.extended_warranty_period, ew.extended_warranty_end_date, ew.warranty_value
        FROM extended_warranty_info ew
        WHERE ew.asset_id = %s
        AND (ew.archieved != 'yes' OR ew.archieved IS NULL)
        AND ew.overall_archieved = 'No'
    """, (asset_id,))
    extended_warranty_info = cursor.fetchall()
    warranty_columns = [desc[0] for desc in cursor.description]
    related_data['extended_warranty_info'] = [dict(zip(warranty_columns, row)) for row in extended_warranty_info]

    # Fetch insurance details with archive conditions
    cursor.execute("""
        SELECT id.policy_number, id.insurance_value, id.insurance_start, id.insurance_period, id.insurance_end
        FROM insurance_details id
        WHERE id.asset_id = %s
        AND (id.archieved != 'yes' OR id.archieved IS NULL)
        AND id.overall_archieved = 'No'
    """, (asset_id,))
    insurance_details = cursor.fetchall()
    insurance_columns = [desc[0] for desc in cursor.description]
    related_data['insurance_details'] = [dict(zip(insurance_columns, row)) for row in insurance_details]

    cursor.close()
    conn.close()



    today = date.today()
    is_qr_login = session.get('qr_login', False)
    logout_url = url_for('custom_logout') if is_qr_login else url_for('logout')

    header_perms = get_permissions(session, 'header')
    
    return render_template(
        'view_asset_details.html',
        asset=asset_dict,
        related_data=related_data,
        permissions=permissions,
        today=today,
        logout_url=logout_url,
        is_qr_login=is_qr_login,
        header_permissions=header_perms['permissions']
    )



@app.route('/get_asset_details/<asset_id>', methods=['GET'])
@login_required
def get_asset_details(asset_id):
    # print(f"Entering get_asset_details for asset_id: {asset_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # print("Database connection established")

        # Fetch service details
        cursor.execute("""
            SELECT service_id, warranty_type , ticket_id, work_done, 
                   next_service_date, service_charge 
            FROM service_details 
            WHERE asset_id = %s AND (archieved IS NULL OR archieved = 'No')
        """, (asset_id,))
        service_details = cursor.fetchall()
        # print(f"Service details fetched: {service_details}")

        # Fetch raised tickets
        cursor.execute("""
            SELECT ticket_id, problem_description, ticket_status 
            FROM raised_tickets 
            WHERE asset_id = %s AND (archieved IS NULL OR archieved = 'No')
        """, (asset_id,))
        raised_tickets = cursor.fetchall()
        # print(f"Raised tickets fetched: {raised_tickets}")

        # Fetch extended warranty info
        cursor.execute("""
            SELECT warranty_asset_id, extended_warranty_start AS warranty_purchase_date, 
                   extended_warranty_period AS extended_warranty, 
                       extended_warranty_end_date as warranty_end_date, warranty_value AS value 
            FROM extended_warranty_info 
            WHERE asset_id = %s AND (archieved IS NULL OR archieved = 'No')
        """, (asset_id,))
        extended_warranty_info = cursor.fetchall()
        # print(f"Extended warranty info fetched: {extended_warranty_info}")

        # Fetch insurance details
        cursor.execute("""
            SELECT policy_number, insurance_value, insurance_start, insurance_period, 
                   insurance_end 
            FROM insurance_details 
            WHERE asset_id = %s AND (archieved IS NULL OR archieved = 'No')
        """, (asset_id,))
        insurance_details = cursor.fetchall()
        # print(f"Insurance details fetched: {insurance_details}")

        cursor.close()
        conn.close()
        # print("Database connection closed")

        # Return the related data as JSON
        response = {
            'service_details': service_details,
            'raised_tickets': raised_tickets,
            'extended_warranty_info': extended_warranty_info,
            'insurance_details': insurance_details
        }
        # print(f"Returning response: {response}")
        return jsonify(response)

    except Exception as e:
        print(f"Error in get_asset_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_asset/<string:id>', methods=['POST'])
@login_required
def delete_asset(id):
    data = request.get_json()  # Get JSON data from the request body
    table_name = data.get('table')  # Extract table name from request body

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if table_name == 'it_assets':
            # Update the `archieved` column in `it_assets`
            cursor.execute("UPDATE it_assets SET archieved = 'yes' WHERE asset_id = %s", (id,))
            
            # Update `overall_archieved` column in related tables
            related_tables = [
                'assets_users',
                'raised_tickets',
                'service_details',
                'insurance_details',
                'extended_warranty_info',
                'product_requests',
                'wfh_asset_requests'
            ]
            
            for table in related_tables:
                cursor.execute(f"UPDATE {table} SET overall_archieved = 'Yes' WHERE asset_id = %s", (id,))

            conn.commit()
            return jsonify({"message": "Asset deleted successfully and related records archived"}), 200
        else:
            return jsonify({"error": "Invalid table name"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Function to fetch purchase_date for an asset_id
def get_purchase_date(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT purchase_date 
        FROM it_assets 
        WHERE asset_id = %s
    """, (asset_id,))
    asset = cursor.fetchone()
    cursor.close()
    conn.close()
    return asset['purchase_date'] if asset else None

# Function to fetch the latest assignment_code and end_date for an asset_id
def get_latest_assignment_code_and_end_date(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT assignment_code, end_date 
        FROM assets_users 
        WHERE asset_id = %s 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (asset_id,))
    latest = cursor.fetchone()
    cursor.close()
    conn.close()
    return latest if latest else {'assignment_code': None, 'end_date': None}

# Function to fetch the latest end_date for an asset_id
def get_latest_end_date(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT end_date 
        FROM assets_users 
        WHERE asset_id = %s AND end_date IS NOT NULL
        ORDER BY end_date DESC 
        LIMIT 1
    """, (asset_id,))
    latest = cursor.fetchone()

    cursor.execute("""
            SELECT COUNT(*) AS row_count
            FROM assets_users
            WHERE asset_id = %s AND end_date IS NOT NULL
        """, (asset_id,))
        
    row_count = cursor.fetchone()['row_count']
    is_disabled = row_count >= 1 and latest['end_date'] is None

    cursor.close()
    conn.close()
    return (latest['end_date'] if latest else None, is_disabled)


@app.route('/create_user_asset/<asset_id>', methods=['GET', 'POST'])
@app.route('/create_user_asset_replacement/<ticket_id>/<asset_id>', methods=['GET', 'POST'])
@login_required
def create_user_asset(asset_id, ticket_id=None):
    # Debug: Log the full request URL and route parameters
    print(f"Request URL: {request.url}")
    print(f"Route ticket_id: {ticket_id}, asset_id: {asset_id}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_users')
    header_perms = get_permissions(session, 'header')

    # Fetch purchase_date and latest end_date for the asset
    purchase_date = get_purchase_date(asset_id)
    if not purchase_date:
        flash("Asset not found or purchase date not available.", "create_user_asset")
        cursor.close()
        conn.close()
        return redirect(url_for('view_user_details', asset_id=asset_id))

    latest_end_date, is_disabled = get_latest_end_date(asset_id)

    if request.method == 'POST':
        # Get ticket_id from form data
        form_ticket_id = request.form.get('ticket_id')
        print(f"Form ticket_id: {form_ticket_id}")

        # Use form_ticket_id if provided, otherwise fallback to route ticket_id
        active_ticket_id = form_ticket_id if form_ticket_id else ticket_id
        print(f"Active ticket_id for POST: {active_ticket_id}")

        assignment_code = generate_unique_id('AU')
        created_by = session['username']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        assigned_user_data = request.form['assigned_user']
        assigned_user, employee_code = assigned_user_data.split('|')
        effective_date_str = request.form['effective_date']
        remarks = request.form.get('remarks', '')
        archieved = request.form.get('archieved', 'No')

        # Convert dates for comparison
        effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()

        # Validate effective_date
        if effective_date < purchase_date:
            flash(f"Effective date cannot be earlier than the purchase date ({purchase_date}).", "create_user_asset")
            cursor.close()
            conn.close()
            return render_template('create_user_asset.html', 
                                 employees=cursor.execute("SELECT id, username, employee_id, email, phone, designation FROM Big_App_Login_Users.User").fetchall(),
                                 asset_id=asset_id, 
                                 purchase_date=purchase_date, 
                                 latest_end_date=latest_end_date,
                                 is_disabled=is_disabled,
                                 permissions=page_perms['permissions'],
                                 role=page_perms['role'],
                                 header_permissions=header_perms['permissions'],
                                 ticket_id=active_ticket_id)  # Pass ticket_id back

        if latest_end_date and effective_date < latest_end_date:
            flash(f"Effective date cannot be earlier than the latest end date ({latest_end_date}).", "create_user_asset")
            cursor.close()
            conn.close()
            return render_template('create_user_asset.html', 
                                 employees=cursor.execute("SELECT id, username, employee_id, email, phone, designation FROM Big_App_Login_Users.User").fetchall(),
                                 asset_id=asset_id, 
                                 purchase_date=purchase_date, 
                                 latest_end_date=latest_end_date,
                                 is_disabled=is_disabled,
                                 permissions=page_perms['permissions'],
                                 role=page_perms['role'],
                                 header_permissions=header_perms['permissions'],
                                 ticket_id=active_ticket_id)  # Pass ticket_id back

        cursor.execute("""
            SELECT email FROM Big_App_Login_Users.User 
            WHERE employee_id = %s
        """, (employee_code,))
        user = cursor.fetchone()
        email = user['email'] if user else None

        if not email:
            flash("No email found for the assigned user.", "create_user_asset")
            cursor.close()
            conn.close()
            return render_template('create_user_asset.html', 
                                 employees=cursor.execute("SELECT id, username, employee_id, email, phone, designation FROM Big_App_Login_Users.User").fetchall(),
                                 asset_id=asset_id, 
                                 purchase_date=purchase_date, 
                                 latest_end_date=latest_end_date,
                                 is_disabled=is_disabled,
                                 permissions=page_perms['permissions'],
                                 role=page_perms['role'],
                                 header_permissions=header_perms['permissions'],
                                 ticket_id=active_ticket_id)  # Pass ticket_id back

        # Insert into assets_users table
        cursor.execute("""
            INSERT INTO assets_users (
                created_by, created_at, assignment_code, asset_id, assigned_user, 
                effective_date, remarks, email, archieved, employee_code, overall_archieved,
                confirmation_status, token, token_expiration
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (created_by, created_at, assignment_code, asset_id, assigned_user, 
              effective_date, remarks, email, archieved, employee_code, 'No', 
              None, None, None))

        cursor.execute("""
            UPDATE it_assets 
            SET has_user_details = 1 
            WHERE asset_id = %s
        """, (asset_id,))

        # If ticket_id is present, update the raised_tickets table
        if active_ticket_id:
            print(f"Updating raised_tickets with ticket_id: {active_ticket_id}, asset_id: {asset_id}")
            cursor.execute("""
                UPDATE raised_tickets
                SET replacement_issued = 'Yes', replacement_asset_id = %s
                WHERE ticket_id = %s
            """, (asset_id, active_ticket_id))
            print(f"Rows updated in raised_tickets: {cursor.rowcount}")
            if cursor.rowcount == 0:
                flash("No matching ticket found or ticket already updated.", "create_user_asset")

        conn.commit()

        # Send confirmation email
        details = {
            'asset_id': asset_id,
            'assignment_code': assignment_code,
            'assigned_user': assigned_user,
            'employee_code': employee_code,
            'effective_date': effective_date_str,
            'remarks': remarks if remarks else 'None',
            'created_by': created_by,
            'created_at': created_at
        }
        send_confirmation_email('create', 'user_asset', assignment_code, details, to_email=email, cc_email='nivetha@tapmobi.in')

        # Send verification email
        send_verification_email(assignment_code, asset_id, assigned_user, email)

        cursor.close()
        conn.close()

        flash("User asset assigned successfully! A verification email has been sent.", "create_user_asset")
        return redirect(url_for('view_user_details', asset_id=asset_id))

    # GET request: fetch employees
    cursor.execute("""
        SELECT id, username, employee_id, email, phone, designation 
        FROM Big_App_Login_Users.User
    """)
    employees = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('create_user_asset.html', 
                           employees=employees, 
                           asset_id=asset_id, 
                           purchase_date=purchase_date, 
                           latest_end_date=latest_end_date,
                           is_disabled=is_disabled,
                           permissions=page_perms['permissions'],
                           role=page_perms['role'],
                           header_permissions=header_perms['permissions'],
                           ticket_id=ticket_id)



@app.route('/edit_user_asset/<assignment_code>', methods=['GET', 'POST'])
@login_required
def edit_user_asset(assignment_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_users')
    header_perms = get_permissions(session, 'header')

    # Fetch asset_id and existing assignment details
    cursor.execute("""
        SELECT asset_id, effective_date, end_date, employee_code 
        FROM assets_users 
        WHERE assignment_code = %s
    """, (assignment_code,))
    assignment = cursor.fetchone()
    if not assignment:
        flash("Assignment not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('index'))  # Redirect to a safe page since asset_id is undefined here

    asset_id = assignment['asset_id']
    original_employee_code = assignment['employee_code']  # Store the original employee_code
    purchase_date = get_purchase_date(asset_id)
    if not purchase_date:
        flash("Asset not found or purchase date not available.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('view_user_details', asset_id=asset_id))

    if request.method == 'POST':
        assigned_user_data = request.form['assigned_user']
        assigned_user, employee_code = assigned_user_data.split('|')
        effective_date_str = request.form['effective_date']
        end_date_str = request.form.get('end_date', None)
        remarks = request.form.get('remarks', '')

        # Convert dates for comparison
        effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

        # Validate effective_date
        if effective_date < purchase_date:
            flash(f"Effective date cannot be earlier than the purchase date ({purchase_date}).", "edit_user_asset")
            return redirect(url_for('edit_user_asset', assignment_code=assignment_code))
        if end_date and effective_date > end_date:
            flash("Effective date cannot be later than the end date.", "edit_user_asset")
            return redirect(url_for('edit_user_asset', assignment_code=assignment_code))

        cursor.execute("""
            SELECT email FROM Big_App_Login_Users.User 
            WHERE employee_id = %s
        """, (employee_code,))
        user = cursor.fetchone()
        email = user['email'] if user else None

        modified_by = session.get('username')  # Use .get() to avoid KeyError if username is not set

        # Update assets_users table
        cursor.execute("""
            UPDATE assets_users 
            SET assigned_user = %s, email = %s, effective_date = %s, end_date = %s, remarks = %s, employee_code = %s,
                modified_by = %s, modified_at = %s
            WHERE assignment_code = %s
        """, (assigned_user, email, effective_date, end_date, remarks, employee_code, modified_by, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), assignment_code))

        # Update has_user_details in it_assets table
        if end_date:
            cursor.execute("""
                UPDATE it_assets 
                SET has_user_details = 0 
                WHERE asset_id = %s
            """, (asset_id,))
        else:
            cursor.execute("""
                UPDATE it_assets 
                SET has_user_details = 1 
                WHERE asset_id = %s
            """, (asset_id,))

        if not email:
            flash("No email found for the assigned user.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('edit_user_asset', assignment_code=assignment_code))

        # Check if employee_code has changed
        if employee_code != original_employee_code:
            send_verification_email(assignment_code, asset_id, assigned_user, email)

        # Send confirmation email to the assigned user with CC to nivetha@tapmobi.in
        details = {
            'asset_id': asset_id,
            'assignment_code': assignment_code,
            'assigned_user': assigned_user,
            'employee_code': employee_code,
            'effective_date': effective_date_str,
            'end_date': end_date_str if end_date_str else 'Not Set',
            'remarks': remarks if remarks else 'None',
            'modified_by': modified_by,
            'modified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        send_confirmation_email('edit', 'user_asset', assignment_code, details, to_email=email, cc_email='nivetha@tapmobi.in')

        conn.commit()

        cursor.close()
        conn.close()
        flash("User asset updated successfully!", "create_user_asset")
        return redirect(url_for('view_user_details', asset_id=asset_id))

    # GET request: fetch employees and last user data
    cursor.execute("""
        SELECT id, username, employee_id, email, phone, designation 
        FROM Big_App_Login_Users.User
    """)
    employees = cursor.fetchall()

    cursor.execute("""
        SELECT assigned_user, employee_code, effective_date, end_date, remarks 
        FROM assets_users 
        WHERE assignment_code = %s
    """, (assignment_code,))
    last_user = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template('edit_user_asset.html', 
                           employees=employees, 
                           assignment_code=assignment_code, 
                           last_user=last_user, 
                           purchase_date=purchase_date,
                           permissions=page_perms['permissions'],
                           role=page_perms['role'],
                           header_permissions=header_perms['permissions']
                           )

# Route for viewing user details
@app.route('/view_user_details/<asset_id>', methods=['GET'])
@login_required
def view_user_details(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch minimal data for the table
    cursor.execute("""
        SELECT assignment_code, assigned_user, email, effective_date, end_date, remarks, acceptance_status
        FROM assets_users WHERE archieved = 'No' and overall_archieved ='No' and asset_id = %s 
    """, (asset_id,))
    assignments = cursor.fetchall()

    # Get the latest assignment_code and end_date
    latest_assignment = get_latest_assignment_code_and_end_date(asset_id)
    latest_assignment_code = latest_assignment['assignment_code']
    latest_end_date = latest_assignment['end_date']

    # Check if full details are requested
    assignment_code = request.args.get('assignment_code', None)
    full_details = None
    if assignment_code:
        cursor.execute("""
            SELECT id, created_by, created_at, assignment_code, asset_id, assigned_user, 
                   email, effective_date, end_date, modified_by, modified_at, remarks, 
                   confirmation_status, token, token_expiration, archieved
            FROM assets_users
            WHERE assignment_code = %s
        """, (assignment_code,))
        full_details = cursor.fetchone()

    cursor.close()
    conn.close()

    page_perms = get_permissions(session, 'view_users')
    header_perms = get_permissions(session, 'header')

    return render_template('view_user_details.html', assignments=assignments, 
                           full_details=full_details, asset_id=asset_id, 
                           latest_assignment_code=latest_assignment_code, 
                           latest_end_date=latest_end_date,
                           permissions=page_perms['permissions'],
                            role=page_perms['role'],
                            header_permissions=header_perms['permissions']
                            )

@app.route('/delete_user_asset/<assignment_code>', methods=['POST'])
@login_required
def delete_user_asset(assignment_code):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch asset_id before deletion for redirect
    cursor.execute("SELECT asset_id FROM assets_users WHERE assignment_code = %s", (assignment_code,))
    asset_id_data = cursor.fetchone()
    asset_id = asset_id_data[0]

    # Delete the assignment by assignment_code
    cursor.execute("""
        UPDATE assets_users SET archieved = 'yes'
        WHERE assignment_code = %s
    """, (assignment_code,))
    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('view_user_details', asset_id=asset_id))


@app.route('/create_vendor', methods=['GET', 'POST'])
@login_required
def create_vendor():
    header_perms = get_permissions(session, 'header')

    if request.method == 'POST':
        vendor_id = generate_unique_id('VD')
        vendor_name = request.form.get('vendor_name')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        remarks = request.form.get('remarks')
        created_by = session['username']
        modified_by = created_by

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vendor_details 
                (vendor_id, vendor_name, address, phone_number, email, remarks, created_by, modified_by) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (vendor_id, vendor_name, address, phone_number, email, remarks, created_by, modified_by))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Vendor added successfully!", "success")
            
            # Determine redirect based on session
            return_to = session.get('return_to', 'create_asset')  # Default to create_asset
            if return_to == 'edit_asset' and 'asset_id' in session:
                asset_id = session['asset_id']
                # Optionally clear form_state if not needed
                if 'form_state' in session:
                    session.pop('form_state')
                return redirect(url_for('edit_asset', asset_id=asset_id))
            else:
                return redirect(url_for('create_asset'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
            return render_template('create_vendor.html')

    return render_template('create_vendor.html',
                        header_permissions=header_perms['permissions']
                           )


# Function to fetch asset details from it_assets table
def fetch_it_assets(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM it_assets 
        WHERE asset_id = %s
    """, (asset_id,))
    asset = cursor.fetchone()
    cursor.close()
    conn.close()
    return asset


@app.route('/create_raise_ticket/<asset_id>', methods=['GET', 'POST'])
@login_required
def create_raise_ticket(asset_id):
    asset = fetch_it_assets(asset_id)
    page_perms = get_permissions(session, 'view_tickets')
    header_perms = get_permissions(session, 'header')

    if not asset:
        flash("Asset not found.", "raise_ticket")
        return redirect(url_for('view_assets'))

    user_name = session.get('username')  # Set raised_by as session username

    # Fetch the latest assigned_user and acceptance_status from assets_users
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT assigned_user, employee_code, email, acceptance_status 
        FROM assets_users 
        WHERE asset_id = %s AND end_date IS NULL 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (asset_id,))
    asset_user = cursor.fetchone()

    last_user = asset_user[0] if asset_user else None
    employee_code = asset_user[1] if asset_user else None
    assigned_email = asset_user[2] if asset_user else None
    acceptance_status = asset_user[3] if asset_user else None

    # Check if acceptance_status is 'rejected'
    if acceptance_status == 'rejected':
        cursor.close()
        conn.close()
        return render_template('create_raise_ticket.html', 
                              asset_id=asset['asset_id'], 
                              product_name=asset['product_name'], 
                              serial_no=asset['serial_no'], 
                              user_name=user_name,
                              last_user=last_user,
                              acceptance_status=acceptance_status,
                              permissions=page_perms['permissions'],
                              role=page_perms['role'],
                              header_permissions=header_perms['permissions'])

    if request.method == 'POST':
        created_by = session['username']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ticket_id = generate_unique_id('RT')
        raised_by = request.form['raised_by']
        problem_description = request.form['problem_description']
        remarks = request.form.get('remarks', '')
        ticket_status = 'Open'
        archieved = 'No'
        reraised_ticket = 'No'
        
        cursor.execute("""
            INSERT INTO raised_tickets (
                created_by, created_at, ticket_id, asset_id, raised_by, raised_emp_id,
                problem_description, ticket_status, remarks, reraised_ticket, archieved, overall_archieved
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (created_by, created_at, ticket_id, asset_id, raised_by, employee_code,
              problem_description, ticket_status, remarks, reraised_ticket, archieved, 'No'))
        conn.commit()

        # Fetch email using employee_code from User table if not already available
        if employee_code and not assigned_email:
            cursor.execute("""
                SELECT email FROM Big_App_Login_Users.User 
                WHERE employee_id = %s
            """, (employee_code,))
            user = cursor.fetchone()
            to_email = user['email'] if user else 'nivetha@tapmobi.in'
        else:
            to_email = assigned_email if assigned_email else 'nivetha@tapmobi.in'

        # Send email confirmation
        details = {
            'ticket_id': ticket_id,
            'asset_id': asset_id,
            'raised_by': raised_by,
            'problem_description': problem_description,
            'ticket_status': ticket_status,
            'created_by': created_by,
            'created_at': created_at,
            'remarks': remarks if remarks else 'None',
            'last_user': last_user if last_user else 'Not Assigned'
        }
        send_confirmation_email('create', 'ticket', ticket_id, details, 
                              to_email=to_email, 
                              cc_email='nivetha@tapmobi.in')

        flash("Ticket raised successfully!", "raise_ticket")
        cursor.close()
        conn.close()

        return redirect(url_for('view_raised_tickets'))
    
    # GET request: render the form
    cursor.close()
    conn.close()
    return render_template('create_raise_ticket.html', 
                          asset_id=asset['asset_id'], 
                          product_name=asset['product_name'], 
                          serial_no=asset['serial_no'], 
                          user_name=user_name,
                          last_user=last_user,
                          acceptance_status=acceptance_status,
                          permissions=page_perms['permissions'],
                          role=page_perms['role'],
                          header_permissions=header_perms['permissions'])


# Route to view raised tickets
@app.route('/view_raised_tickets', methods=['GET'])
@app.route('/view_raised_tickets/<asset_id>', methods=['GET'])
@login_required
def view_raised_tickets(asset_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if asset_id:
        # Fetch tickets for the specific asset, excluding archived
        cursor.execute("""
                SELECT created_by, ticket_id, raised_by, problem_description, 
                    ticket_status, ignore_reason, replacement_asset_id, asset_id
                FROM raised_tickets 
                WHERE asset_id = %s AND archieved = 'No' AND overall_archieved = 'No'
                ORDER BY 
                FIELD(ticket_status, 'Open', 'Re-Raised', 'In Progress', 'Closed'), 
                created_by ASC,
                modified_by ASC

        """, (asset_id,))
    else:
        # Fetch all tickets when no asset_id is provided, excluding archived
        cursor.execute("""
           SELECT created_by, ticket_id, raised_by, problem_description, 
                ticket_status, ignore_reason, replacement_asset_id, asset_id
            FROM raised_tickets
            WHERE archieved = 'No' AND overall_archieved = 'No'
            ORDER BY 
            FIELD(ticket_status, 'Open', 'Re-Raised', 'In Progress', 'Closed'), 
            created_by ASC,
            modified_by ASC

        """)

    tickets = cursor.fetchall()
    cursor.close()
    conn.close()

    # Get permissions for the current page and header
    page_perms = get_permissions(session, 'view_tickets')
    print(page_perms)
    
    header_perms = get_permissions(session, 'header')

    return render_template('view_raised_tickets.html', 
                         tickets=tickets, 
                         asset_id=asset_id,
                         ticket_is_processed=ticket_is_processed,
                         permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
                        )


# Route to fetch ticket details for the view popup
@app.route('/ticket_details/<ticket_id>', methods=['GET'])
@login_required
def ticket_details(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, created_by, created_at, ticket_id, asset_id, raised_by, 
               problem_description, modified_by, modified_at, ticket_status, 
               ignore_reason, progress_notes, replacement_issued, 
               replacement_asset_id, replacement_reason, remarks, archieved,reraised_ticket
        FROM raised_tickets 
        WHERE ticket_id = %s
    """, (ticket_id,))
    ticket = cursor.fetchone()

    cursor.close()
    conn.close()

    if ticket:
        return jsonify(ticket)
    else:
        return jsonify({'error': 'Ticket not found'}), 404
    


@app.route('/create_reraised_ticket/<ticket_id>', methods=['GET', 'POST'])
@login_required
def create_reraised_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch ticket details
    cursor.execute("""
        SELECT ticket_id, asset_id, raised_by, problem_description, ticket_status
        FROM raised_tickets 
        WHERE ticket_id = %s
    """, (ticket_id,))
    ticket = cursor.fetchone()
    
    if not ticket:
        flash("Ticket not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('view_raised_tickets'))
    
    page_perms = get_permissions(session, 'view_tickets')
    header_perms = get_permissions(session, 'header')
    
    if request.method == 'POST':
        modified_by = session['username']
        modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_reason = request.form.get('reraised_reason', '')
        
        # Fetch current problem_description
        current_description = ticket['problem_description'] or ''
        
        # Append new reason
        updated_description = f"{current_description}\nRe-raise Reason: {new_reason}" if current_description else f"Re-raise Reason: {new_reason}"
        reraised_ticket = 'Yes'
        
        # Update ticket
        cursor.execute("""
            UPDATE raised_tickets 
            SET ticket_status = 'Re-raised',
                problem_description = %s,
                reraised_ticket = %s,    
                modified_by = %s,
                modified_at = %s
            WHERE ticket_id = %s
        """, (updated_description, reraised_ticket, modified_by, modified_at, ticket_id))
        
        # Send email confirmation
        details = {
            'ticket_id': ticket_id,
            'asset_id': ticket['asset_id'],
            'raised_by': ticket['raised_by'],
            'problem_description': updated_description,
            'ticket_status': 'Re-raised',
            'modified_by': modified_by,
            'modified_at': modified_at,
            'reraised_reason': new_reason if new_reason else 'No additional reason provided'
        }
        send_confirmation_email('reraised', 'ticket', ticket_id, details, 
                              to_email='nivetha@tapmobi.in', 
                              cc_email='nivetha@tapmobi.in')
        
        conn.commit()
        flash("Ticket re-raised successfully! Please create a new service.", "create_reraised_ticket")
        cursor.close()
        conn.close()
        # return redirect(url_for('create_reraised_service', ticket_id=ticket_id, asset_id=ticket['asset_id']))
        return redirect(url_for('view_raised_tickets', asset_id=ticket['asset_id']))
    
    
    # GET request: Render the re-raise form
    cursor.close()
    conn.close()
    return render_template('create_reraised_ticket.html', 
                         ticket=ticket,
                         permissions=page_perms['permissions'],
                         role=page_perms['role'],
                         header_permissions=header_perms['permissions'])



@app.route('/create_reraised_service/<ticket_id>/<asset_id>', methods=['GET', 'POST'])
@app.route('/create_reraised_service/<ticket_id>/', methods=['GET', 'POST'])
@login_required
def create_reraised_service(ticket_id, asset_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    # Check if asset_id is None or empty
    if asset_id is None or asset_id == '':
        print("asset_id is None or empty, fetching from raised_tickets")
        cursor.execute("""
            SELECT asset_id FROM raised_tickets 
            WHERE ticket_id = %s
            LIMIT 1
        """, (ticket_id,))
        ticket_record = cursor.fetchone()

        if ticket_record:
            asset_id = ticket_record['asset_id']
            print(f"Fetched asset_id from raised_tickets: {asset_id}")
        else:
            print(f"No asset_id found for ticket_id={ticket_id} in raised_tickets")
            flash("No asset found for this ticket.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('view_raised_tickets'))

    # Fetch service history for the ticket_id
    cursor.execute("""
        SELECT service_id, ticket_id, asset_id, technician_name, work_done, created_at, modified_at, service_bill_path
        FROM service_details 
        WHERE ticket_id = %s AND archieved = 'No' AND overall_archieved = 'No'
        UNION
        SELECT service_id, ticket_id, asset_id, technician_name, work_done, created_at, modified_at, service_bill_path
        FROM reraised_ticket_services 
        WHERE ticket_id = %s AND archieved = 'No' AND overall_archieved = 'No'
        ORDER BY created_at DESC
    """, (ticket_id, ticket_id))
    service_history = cursor.fetchall()
  

    if request.method == 'POST':
        service_id = generate_unique_id('RTS')
        created_by = session['username']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        technician_source = request.form['technician_source']

        print('technician_source', technician_source)
        
        # Set technician_name and technician_id based on technician_source
        if technician_source == 'inhouse':
            technician_name = session['username']
            technician_id = session['emp_id']
        else:  # outhouse
            technician_name = request.form['technician_name']
            technician_id = request.form['technician_id']

        work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)
        warranty_type = in_warranty_out_warranty(asset_id)
        reference_name = None  # Not provided in form, set to None
        multiple_service_id_no = None  # Not provided in form, set to None

        # Handle multiple file uploads
        service_bill_paths = []
        if 'service_bill' in request.files:
            files = request.files.getlist('service_bill')
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            service_bills_folder = os.path.join(asset_folder, 'service_bills')
            os.makedirs(service_bills_folder, exist_ok=True)
            for file in files:
                if file and allowed_file(file.filename):
                    filename = f"{service_id}_{file.filename}"
                    file_path = os.path.join(service_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'service_bills', filename)
                    service_bill_paths.append(relative_path)
        service_bill_path = ','.join(service_bill_paths) if service_bill_paths else None
        multiple_service_bill_path = service_bill_path  # Set to same as service_bill_path, as form doesn't distinguish

        # Insert into reraised_ticket_services
        cursor.execute("""
            INSERT INTO reraised_ticket_services (
                service_id, ticket_id, asset_id, reference_name, warranty_type, service_case_id, technician_source,
                technician_name, technician_id, work_done, next_service_date, service_charge, 
                remarks, multiple_service_bill_path, multiple_service_id_no, service_bill_path, 
                created_by, created_at, archieved, overall_archieved
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            service_id, ticket_id, asset_id, reference_name, warranty_type, service_case_id,technician_source,
            technician_name, technician_id, work_done, next_service_date, service_charge,
            remarks, multiple_service_bill_path, multiple_service_id_no, service_bill_path,
            created_by, created_at, 'No', 'No'
        ))

        if ticket_id:
            cursor.execute("""
                UPDATE raised_tickets 
                SET ticket_status = 'Closed' 
                WHERE ticket_id = %s
            """, (ticket_id,))

        conn.commit()

        # Send email confirmation
        details = {
            'asset_id': asset_id,
            'ticket_id': ticket_id,
            'service_id': service_id,
            'technician_name': technician_name,
            'technician_id': technician_id,
            'work_done': work_done,
            'next_service_date': next_service_date if next_service_date else 'Not Set',
            'service_charge': service_charge if service_charge else 'Not Set',
            'service_bill_path': service_bill_path if service_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'service_case_id': service_case_id if service_case_id else 'None',
            'warranty_type': warranty_type,
            'created_by': created_by,
            'created_at': created_at
        }
        send_confirmation_email('create', 'service', service_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        cursor.close()
        conn.close()
        flash("Service created successfully!", "create_reraised_service")
        return redirect(url_for('view_service'))

    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('create_reraised_service.html', ticket_id=ticket_id, asset_id=asset_id, 
                           service_history=service_history, technicians=technicians,
                           permissions=page_perms['permissions'], role=page_perms['role'],
                           header_permissions=header_perms['permissions'])


@app.route('/service_exists/<ticket_id>', methods=['GET'])
@login_required
def service_exists(ticket_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check service_details first
        cursor.execute(
            "SELECT service_id FROM service_details WHERE ticket_id = %s AND archieved = 'No' AND overall_archieved = 'No'",
            (ticket_id,)
        )
        service = cursor.fetchone()
        
        if service and 'service_id' in service:
            cursor.close()
            conn.close()
            return jsonify({'service_id': service['service_id'], 'table': 'service_details'})
        
        # Check reraised_ticket_services for the latest entry
        cursor.execute("""
            SELECT service_id FROM reraised_ticket_services 
            WHERE ticket_id = %s AND archieved = 'No' AND overall_archieved = 'No'
            ORDER BY created_at DESC LIMIT 1
        """, (ticket_id,))
        service = cursor.fetchone()
        
        if service and 'service_id' in service:
            cursor.close()
            conn.close()
            return jsonify({'service_id': service['service_id'], 'table': 'reraised_ticket_services'})
        
        cursor.close()
        conn.close()
        return jsonify({'service_id': None})
    
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print(f"Error in service_exists: {str(e)}")
        return jsonify({'service_id': None, 'error': 'Internal server error'}), 500

# Modified ignore_ticket route to append ignore reason
@app.route('/ignore_ticket/<ticket_id>', methods=['POST'])
@login_required
def ignore_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    new_ignore_reason = request.form['ignore_reason']
    modified_by = session['username']
    modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Fetch current ignore reason
    cursor.execute("SELECT ignore_reason FROM raised_tickets WHERE ticket_id = %s", (ticket_id,))
    current_reason = cursor.fetchone()[0]
    
    # Append new reason
    updated_reason = f"{current_reason}\n{new_ignore_reason}" if current_reason else new_ignore_reason

    cursor.execute("""
        UPDATE raised_tickets 
        SET ignore_reason = %s, ticket_status = 'Closed', 
            modified_by = %s, modified_at = %s
        WHERE ticket_id = %s
    """, (updated_reason, modified_by, modified_at, ticket_id))
    conn.commit()

    # Fetch additional ticket details for email
    cursor.execute("""
        SELECT asset_id, raised_by, problem_description 
        FROM raised_tickets 
        WHERE ticket_id = %s
    """, (ticket_id,))
    ticket = cursor.fetchone()

    # Send email confirmation
    details = {
        'ticket_id': ticket_id,
        'asset_id': ticket[0] if ticket else 'Unknown',
        'raised_by': ticket[1] if ticket else 'Unknown',
        'problem_description': ticket[2] if ticket else 'Unknown',
        'ignore_reason': updated_reason,
        'ticket_status': 'Closed',
        'modified_by': modified_by,
        'modified_at': modified_at
    }
    send_confirmation_email('ignore', 'ticket', ticket_id, details, 
                          to_email='nivetha@tapmobi.in', 
                          cc_email='nivetha@tapmobi.in')

    # Fetch asset_id for redirect
    asset_id = ticket[0] if ticket else None

    cursor.close()
    conn.close()

    referrer = request.referrer
    if referrer and "ignore_ticket" not in referrer and "delete_ticket" not in referrer:
        return redirect(referrer)

    flash("Ticket ignored successfully!", "ignore_ticket")
    return redirect(url_for('view_raised_tickets', asset_id=asset_id))

# Modified ticket_is_processed function to enable buttons for re-raised tickets
def ticket_is_processed(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT ticket_status 
        FROM raised_tickets 
        WHERE ticket_id = %s
    """, (ticket_id,))
    ticket = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # Allow buttons if ticket is Re-raised
    return ticket['ticket_status'] not in ['Open', 'Re-raised']


@app.route('/delete_ticket/<ticket_id>', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch asset_id before deletion for redirect
    cursor.execute("SELECT asset_id FROM raised_tickets WHERE ticket_id = %s", (ticket_id,))
    asset_id_data = cursor.fetchone()
    asset_id = asset_id_data[0]

    # Delete the assignment by ticket_id
    cursor.execute("""
        UPDATE raised_tickets SET archieved = 'yes'
        WHERE ticket_id = %s
    """, (ticket_id,))
    conn.commit()

    cursor.close()
    conn.close()


    # Get referrer and prevent infinite redirect loop
    referrer = request.referrer
    if referrer and "ignore_ticket" not in referrer and "delete_ticket" not in referrer:
        return redirect(referrer)  # Redirect to the same page only if it’s not looping
    
    flash("Ticket deleted successfully!", "success")
    return redirect(url_for('view_raised_tickets', asset_id=asset_id))

@app.route('/create_replacement', methods=['GET'])
@login_required
def fetch_unassigned_assets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    ticket_id = request.args.get('ticket_id')


    header_perms = get_permissions(session, 'header')

    # Fetch unassigned assets where has_user_details = 0
    cursor.execute("""
        SELECT * 
        FROM it_assets 
        WHERE has_user_details = 0
    """)
    unassigned_assets = cursor.fetchall()

    # Fetch distinct product types for the filter
    cursor.execute("""
        SELECT DISTINCT product_type 
        FROM it_assets 
        WHERE has_user_details = 0
    """)
    product_types = [row['product_type'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template('create_replacement.html', assets=unassigned_assets, product_types=product_types,
                            header_permissions=header_perms['permissions'],
                            ticket_id = ticket_id
                           )


@app.route('/create_service/<ticket_id>/<asset_id>', methods=['GET', 'POST'])
@app.route('/create_service/<ticket_id>/', methods=['GET', 'POST'])
@login_required
def create_service(ticket_id, asset_id=None):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    # Check if asset_id is None or an empty string
    if asset_id is None or asset_id == '':
        print("asset_id is None or empty, fetching from raised_tickets")
        cursor.execute("""
            SELECT asset_id FROM raised_tickets 
            WHERE ticket_id = %s
            LIMIT 1
        """, (ticket_id,))
        ticket_record = cursor.fetchone()

        if ticket_record:
            asset_id = ticket_record['asset_id']
            print(f"Fetched asset_id from raised_tickets: {asset_id}")
        else:
            print(f"No asset_id found for ticket_id={ticket_id} in raised_tickets")
            flash("No asset found for this ticket. Please select an asset.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('some_default_route'))  # Replace with your default route

    if request.method == 'POST':
        service_id = generate_unique_id('SI')
        created_by = session['username']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


        # Get technician_source from form
        technician_source = request.form['technician_source']
        
        # Set technician_name and technician_id based on technician_source
        if technician_source == 'inhouse':
            technician_name = session['username']
            technician_id = session['emp_id']
        else:  # outhouse
            technician_name = request.form['technician_name']
            technician_id = request.form['technician_id']

        work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)


        # warranty_type = request.form['warranty_type']  # New field
        warranty_type = in_warranty_out_warranty(asset_id)


        # Handle multiple file uploads
        service_bill_paths = []
        if 'service_bill' in request.files:
            files = request.files.getlist('service_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    # Define the upload path: UPLOAD_FOLDER/asset_id/service_bills/
                    asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
                    service_bills_folder = os.path.join(asset_folder, 'service_bills')
                    
                    # Create folders if they don't exist
                    os.makedirs(service_bills_folder, exist_ok=True)
                    
                    # Define the filename with service_id prefix
                    filename = f"{service_id}_{file.filename}"
                    file_path = os.path.join(service_bills_folder, filename)
                    
                    # Save the file
                    file.save(file_path)
                    # Store the relative path from UPLOAD_FOLDER
                    relative_path = os.path.join(asset_id, 'service_bills', filename)
                    service_bill_paths.append(relative_path)
            service_bill_path = ','.join(service_bill_paths) if service_bill_paths else None
        else:
            service_bill_path = None

        # Handle Asset Image Uploads
        service_images = []
        if 'service_image[]' in request.files:
            files = request.files.getlist('service_image[]')
            for file in files:
                if file and allowed_file(file.filename):
                    asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
                    service_bills_folder = os.path.join(asset_folder, 'service_bills')
                    
                    # Create folders if they don't exist
                    os.makedirs(service_bills_folder, exist_ok=True)

                    filename = secure_filename(file.filename)
                    filepath = os.path.join(service_bills_folder, filename)
                    file.save(filepath)
                    service_images.append(filename)

            service_images_str = ','.join(service_images)
        else:
            service_images_str = None


        cursor.execute("""
            INSERT INTO service_details (service_id, ticket_id, asset_id, service_case_id, technician_source, technician_name, technician_id, 
                                 work_done, next_service_date, service_charge, remarks, service_bill_path, service_photo_path,
                                 created_by, created_at, warranty_type, archieved, overall_archieved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (service_id, ticket_id, asset_id, service_case_id, technician_source, technician_name, technician_id, work_done, 
              next_service_date, service_charge, remarks, service_bill_path, service_images_str, created_by, created_at, warranty_type, 'No', 'No'))
        
        if ticket_id:  # Ensure ticket_id is not None
            cursor.execute("""
                UPDATE raised_tickets 
                SET ticket_status = 'Closed' 
                WHERE ticket_id = %s
            """, (ticket_id,))

        conn.commit()

        # Send email confirmation
        details = {
            'asset_id': asset_id,
            'ticket_id': ticket_id,
            'technician_name': technician_name,
            'work_done': work_done,
            'next_service_date': next_service_date if next_service_date else 'Not Set',
            'service_charge': service_charge if service_charge else 'Not Set',
            'created_at': created_at,
            'created_by': session['username'],
            'remarks': remarks if remarks else 'None'
        }
        send_confirmation_email('create', 'service', service_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        cursor.close()
        conn.close()
        flash("Service created successfully!", "create_service")
        return redirect(url_for('view_service'))

    # GET request: Fetch technicians for dropdown
    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('create_service.html', ticket_id=ticket_id, asset_id=asset_id, technicians=technicians,
                            permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
                           )


@app.route('/edit_service_reraised/<service_id>', methods=['GET', 'POST'])
@login_required
def edit_service_reraised(service_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    # Fetch the latest service for the ticket_id
    cursor.execute("""
        SELECT * FROM reraised_ticket_services 
        WHERE service_id = %s AND archieved = 'No' AND overall_archieved = 'No'
    """, (service_id,))
    service = cursor.fetchone()

    if not service:
        flash("Service record not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('view_service'))

    ticket_id = service['ticket_id']
    asset_id = service['asset_id']

    # Fetch service history for the ticket_id (excluding the latest editable entry)
    cursor.execute("""
        SELECT service_id, ticket_id, asset_id, technician_name, work_done, created_at, modified_at
        FROM service_details 
        WHERE ticket_id = %s AND archieved = 'No' AND overall_archieved = 'No'
        UNION
        SELECT service_id, ticket_id, asset_id, technician_name, work_done, created_at, modified_at
        FROM reraised_ticket_services 
        WHERE ticket_id = %s AND service_id != %s AND archieved = 'No' AND overall_archieved = 'No'
        ORDER BY created_at DESC
    """, (ticket_id, ticket_id, service_id))
    service_history = cursor.fetchall()

    if request.method == 'POST':
        technician_name = request.form['technician_name']
        technician_id = request.form['technician_id']
        new_work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)
        warranty_type = in_warranty_out_warranty(asset_id)
        modified_by = session.get('username')
        modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Fetch existing work_done
        cursor.execute("SELECT work_done FROM reraised_ticket_services WHERE service_id = %s", (service_id,))
        existing_service = cursor.fetchone()
        existing_work_done = existing_service['work_done'] or ''
        
        # Append new work_done with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updated_work_done = f"{existing_work_done}\n{timestamp}: {new_work_done}" if existing_work_done else f"{timestamp}: {new_work_done}"

        # Handle existing bills and removals
        cursor.execute("SELECT service_bill_path FROM reraised_ticket_services WHERE service_id = %s", (service_id,))
        existing_service = cursor.fetchone()
        existing_paths = existing_service['service_bill_path'].split(',') if existing_service['service_bill_path'] else []
        
        removed_bills = request.form.get('removed_bills', '').split(',') if request.form.get('removed_bills') else []
        service_bill_paths = [path for path in existing_paths if path not in removed_bills]

        # Handle new file uploads
        if 'service_bill' in request.files:
            files = request.files.getlist('service_bill')
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            service_bills_folder = os.path.join(asset_folder, 'service_bills')
            os.makedirs(service_bills_folder, exist_ok=True)
            for file in files:
                if file and allowed_file(file.filename):
                    filename = f"{service_id}_{file.filename}"
                    file_path = os.path.join(service_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'service_bills', filename)
                    if relative_path not in service_bill_paths:
                        service_bill_paths.append(relative_path)
        
        service_bill_path = ','.join(service_bill_paths) if service_bill_paths else None

        # Update reraised_ticket_services
        cursor.execute("""
            UPDATE reraised_ticket_services 
            SET technician_name = %s, technician_id = %s, work_done = %s, next_service_date = %s, 
                service_charge = %s, remarks = %s, service_case_id = %s, service_bill_path = %s,
                modified_by = %s, modified_at = %s, warranty_type = %s
            WHERE service_id = %s
        """, (technician_name, technician_id, updated_work_done, next_service_date, service_charge, remarks, 
              service_case_id, service_bill_path, modified_by, modified_at, warranty_type, service_id))
        
        # Send email confirmation
        details = {
            'asset_id': asset_id,
            'ticket_id': ticket_id,
            'service_id': service_id,
            'technician_name': technician_name,
            'technician_id': technician_id,
            'work_done': updated_work_done,
            'next_service_date': next_service_date if next_service_date else 'Not Set',
            'service_charge': service_charge if service_charge else 'Not Set',
            'service_bill_path': service_bill_path if service_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'service_case_id': service_case_id if service_case_id else 'None',
            'warranty_type': warranty_type,
            'modified_by': modified_by,
            'modified_at': modified_at
        }
        send_confirmation_email('edit', 'service', service_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        conn.commit()
        cursor.close()
        conn.close()
        flash("Service updated successfully!", "edit_service_reraised")
        return redirect(url_for('view_service'))

    # GET request: Fetch technicians
    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('edit_service_reraised.html', service=service, service_history=service_history, 
                           technicians=technicians, permissions=page_perms['permissions'], 
                           role=page_perms['role'], header_permissions=header_perms['permissions'])


@app.route('/edit_service/<service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    print('service_id',service_id)

    # Fetch asset_id
    if service_id.startswith('RTS'):
        print('yes rts')
        cursor.execute("SELECT asset_id FROM reraised_ticket_services WHERE service_id = %s", (service_id,))
        table_name = 'reraised_ticket_services'
        services = cursor.fetchone()
        print(services)
    elif service_id.startswith('SI'):
        cursor.execute("SELECT asset_id FROM service_details WHERE service_id = %s", (service_id,))
        table_name = 'service_details'
        services = cursor.fetchone()


    if not services:
        flash("Service record not found.", "edit_service")
        cursor.close()
        conn.close()
        return redirect(url_for('view_service'))

    asset_id = services['asset_id']

    if request.method == 'POST':
        # technician_name = request.form['technician_name']
        # technician_id = request.form['technician_id']

        technician_source = request.form['technician_source']
        
        # Set technician_name and technician_id based on technician_source
        if technician_source == 'inhouse':
            technician_name = session['username']
            technician_id = session['emp_id']
        else:  # outhouse
            technician_name = request.form['technician_name']
            technician_id = request.form['technician_id']

        work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)
        warranty_type = in_warranty_out_warranty(asset_id)
        modified_by = session.get('username')  # Use .get() to avoid KeyError
        modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


        # Handle existing bills and removals
        cursor.execute(f"SELECT service_bill_path, service_photo_path FROM {table_name} WHERE service_id = %s", (service_id,))
        existing_service = cursor.fetchone()
        existing_paths = existing_service['service_bill_path'].split(',') if existing_service['service_bill_path'] else []
        existing_images = existing_service['service_photo_path'].split(',') if existing_service['service_photo_path'] else []

        # Get removed bills and images from form (full paths)
        removed_bills = request.form.get('removed_bills', '').split(',') if request.form.get('removed_bills') else []
        removed_images = request.form.get('removed_images', '').split(',') if request.form.get('removed_images') else []

        # Remove specified bills and images from the existing lists
        service_bill_paths = [path for path in existing_paths if path not in removed_bills]
        service_images_path = [image for image in existing_images if image not in removed_images]

        # Handle new bill uploads (append to filtered list)
        if 'service_bill' in request.files:
            files = request.files.getlist('service_bill')
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            service_bills_folder = os.path.join(asset_folder, 'service_bills')
            os.makedirs(service_bills_folder, exist_ok=True)
            for file in files:
                if file and allowed_file(file.filename):
                    filename = f"{service_id}_{file.filename}"
                    file_path = os.path.join(service_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'service_bills', filename)
                    if relative_path not in service_bill_paths:
                        service_bill_paths.append(relative_path)

        # Join the updated bill paths into a string
        service_bill_path = ','.join(service_bill_paths) if service_bill_paths else None

        # Handle new image uploads (append to filtered list)
        if 'service_image' in request.files:
            photo_files = request.files.getlist('service_image')
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            service_images_folder = os.path.join(asset_folder, 'service_images')
            os.makedirs(service_images_folder, exist_ok=True)
            for file in photo_files:
                if file and allowed_file(file.filename):
                    filename = f"{service_id}_p_{file.filename}"
                    filepath = os.path.join(service_images_folder, filename)
                    file.save(filepath)
                    relative_path = os.path.join(asset_id, 'service_images', filename)
                    if relative_path not in service_images_path:
                        service_images_path.append(relative_path)

        # Join the updated image paths into a string
        service_images_str = ','.join(service_images_path) if service_images_path else ''
        
        # Update services table with warranty_type
        cursor.execute(f"""
            UPDATE {table_name} 
            SET technician_source = %s, technician_name = %s, technician_id = %s, work_done = %s, next_service_date = %s, 
                service_charge = %s, remarks = %s, service_case_id = %s, service_bill_path = %s, service_photo_path=%s,
                modified_by = %s, modified_at = %s, warranty_type = %s
            WHERE service_id = %s
        """, (technician_source, technician_name, technician_id, work_done, next_service_date, service_charge, remarks, 
              service_case_id, service_bill_path,service_images_str, modified_by, modified_at, warranty_type, service_id))
        
        # Send email confirmation
        details = {
            'asset_id': asset_id,
            'service_id': service_id,
            'technician_name': technician_name,
            'work_done': work_done,
            'next_service_date': next_service_date if next_service_date else 'Not Set',
            'service_charge': service_charge if service_charge else 'Not Set',
            'service_bill_path': service_bill_path if service_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'modified_by': modified_by,
            'modified_at': modified_at
        }
        send_confirmation_email('edit', 'service', service_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        conn.commit()

        cursor.close()
        conn.close()
        flash("Service updated successfully!", "edit_service")
        return redirect(url_for('view_service'))

    # GET request: Fetch service details and technicians
    cursor.execute(f"SELECT * FROM {table_name} WHERE service_id = %s", (service_id,))
    service = cursor.fetchone()

    if not service:
        flash("Service record not found.", "edit_service")
        cursor.close()
        conn.close()
        return redirect(url_for('view_service'))

    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('edit_service.html', service=service, technicians=technicians,
                           permissions=page_perms['permissions'],
                           role=page_perms['role'],
                           header_permissions=header_perms['permissions']
                           )


@app.route('/view_service', methods=['GET'])
@login_required
#@app.route('/view_service/<service_id>', methods=['GET'])
def view_service(service_id=None):  # Added default value for clarity
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if service_id:
        cursor.execute("SELECT * FROM service_details WHERE service_id = %s AND archieved = 'No' and overall_archieved ='No'", (service_id,))
        service = cursor.fetchone()
    else:
        # cursor.execute("SELECT * FROM service_details WHERE archieved = 'No' and overall_archieved = 'No' ")
        cursor.execute("""
            SELECT *, 'service_details' AS source 
            FROM service_details 
            WHERE archieved = 'No' AND overall_archieved = 'No'
            UNION ALL
            SELECT *, 'reraised_ticket_services' AS source 
            FROM reraised_ticket_services 
            WHERE archieved = 'No' AND overall_archieved = 'No'
        """)
        service = cursor.fetchall()
        
    cursor.close()
    conn.close()


    page_perms = get_permissions(session, 'view_service')
    print(page_perms)
    header_perms = get_permissions(session, 'header')

    return render_template('view_service.html', service=service,
                           permissions=page_perms['permissions'],
                            role=page_perms['role'],
                            header_permissions=header_perms['permissions']
                            )

# Route to delete a service
@app.route('/delete_service/<service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the 'archieved' column instead of deleting
    cursor.execute("""
        UPDATE service_details 
        SET archieved = 'Yes' 
        WHERE service_id = %s
    """, (service_id,))
    
    conn.commit()
    cursor.close()
    conn.close()

    flash("Service Deleted successfully!", "delete_service")
    return redirect(url_for('view_service'))  # Replace with your desired redirect route

# Function to get purchase date of an asset
def get_purchase_date(asset_id):
    asset = fetch_it_assets(asset_id)
    return asset['purchase_date'] if asset else None

# Function to get the latest insurance end date for an asset
def get_latest_insurance_end_date(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check the count of insurance records for the asset_id
    cursor.execute("""
        SELECT COUNT(*) 
        FROM insurance_details 
        WHERE asset_id = %s AND archieved = 'No'
    """, (asset_id,))
    count = cursor.fetchone()['COUNT(*)']

    # Only fetch the latest end date if there is more than one record
    if count > 1:
        cursor.execute("""
            SELECT insurance_end 
            FROM insurance_details 
            WHERE asset_id = %s AND archieved = 'No'
            ORDER BY insurance_end DESC
            LIMIT 1
        """, (asset_id,))
        insurance = cursor.fetchone()
        latest_end_date = insurance['insurance_end'] if insurance else None
    else:
        latest_end_date = None

    cursor.close()
    conn.close()
    return latest_end_date

# Route to create a new insurance record
@app.route('/create_insurance/<asset_id>', methods=['GET', 'POST'])
@login_required
def create_insurance(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    page_perms = get_permissions(session, 'view_insurance')
    header_perms = get_permissions(session, 'header')

    if request.method == 'POST':
        product_name = request.form['product_name']
        policy_number = request.form['policy_number']
        insurance_value = request.form['insurance_value'] or None
        insurance_start = request.form['insurance_start']
        insurance_period_years = int(request.form['insurance_period_years'] or 0)
        insurance_period_months = int(request.form['insurance_period_months'] or 0)
        insurance_period_days = int(request.form['insurance_period_days'] or 0)
        remarks = request.form.get('remarks', '')

        # Calculate insurance_end date
        insurance_start_date = datetime.strptime(insurance_start, '%Y-%m-%d').date()
        total_days = (insurance_period_years * 365) + (insurance_period_months * 30) + insurance_period_days
        insurance_end = insurance_start_date + timedelta(days=total_days)

        # Handle multiple file uploads
        insurance_bill_paths = []
        if 'insurance_bill' in request.files:
            files = request.files.getlist('insurance_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    # Define the upload path: UPLOAD_FOLDER/asset_id/insurance_bills/
                    asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
                    insurance_bills_folder = os.path.join(asset_folder, 'insurance_bills')
                    
                    # Create folders if they don't exist
                    os.makedirs(insurance_bills_folder, exist_ok=True)
                    
                    # Define the filename with insurance_id prefix
                    insurance_id = generate_unique_id('INS')
                    filename = f"{insurance_id}_{file.filename}"
                    file_path = os.path.join(insurance_bills_folder, filename)
                    
                    # Save the file
                    file.save(file_path)
                    # Store the relative path from UPLOAD_FOLDER
                    relative_path = os.path.join(asset_id, 'insurance_bills', filename)
                    insurance_bill_paths.append(relative_path)
            insurance_bill_path = ','.join(insurance_bill_paths) if insurance_bill_paths else None
        else:
            insurance_bill_path = None

        # Generate insurance_id
        insurance_id = generate_unique_id('INS')
        created_by = session['username']
        created_at = datetime.now()

        # Insert into insurance_details table
        cursor.execute("""
            INSERT INTO insurance_details 
            (insurance_id, asset_id, policy_number, insurance_value, insurance_start, 
             insurance_period, insurance_end, insurance_bill_path, remarks, created_by, created_at, archieved, overall_archieved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (insurance_id, asset_id, policy_number, insurance_value, insurance_start,
              f"{insurance_period_years} years, {insurance_period_months} months, {insurance_period_days} days",
              insurance_end, insurance_bill_path, remarks, created_by, created_at, 'No', 'No'))
        conn.commit()

    # Send email confirmation
        details = {
            'insurance_id': insurance_id,
            'asset_id': asset_id,
            'policy_number': policy_number,
            'insurance_value': insurance_value if insurance_value else 'Not Set',
            'insurance_start': insurance_start,
            'insurance_period': f"{insurance_period_years} years, {insurance_period_months} months, {insurance_period_days} days",
            'insurance_end': insurance_end.strftime('%Y-%m-%d'),
            'insurance_bill_path': insurance_bill_path if insurance_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'created_by': created_by,
            'created_at': created_at
        }
        send_confirmation_email('create', 'insurance', insurance_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        cursor.close()
        conn.close()
        flash("Insurance created successfully!", "create_insurance")
        return redirect(url_for('view_insurance', insurance_id=insurance_id))

    # GET request: Fetch asset info, purchase date, and latest insurance end date
    asset = fetch_it_assets(asset_id)
    if not asset:
        flash("Asset not found.", "create_insurance")
        cursor.close()
        conn.close()
        return redirect(url_for('view_insurance'))  # Replace with your default route

    purchase_date = asset['purchase_date']
    latest_insurance_end = get_latest_insurance_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('create_insurance.html', asset_id=asset_id, product_name=asset['product_name'],
                          purchase_date=purchase_date, latest_insurance_end=latest_insurance_end,
                           permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
                          )


@app.route('/edit_insurance/<insurance_id>', methods=['GET', 'POST'])
@login_required
def edit_insurance(insurance_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_insurance')
    header_perms = get_permissions(session, 'header')

    # Fetch the existing insurance record
    cursor.execute("SELECT * FROM insurance_details WHERE insurance_id = %s", (insurance_id,))
    insurance = cursor.fetchone()

    if not insurance:
        flash("Insurance record not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('view_insurance'))

    asset_id = insurance['asset_id']

    if request.method == 'POST':
        policy_number = request.form['policy_number']
        insurance_value = request.form['insurance_value'] or None
        insurance_start = request.form['insurance_start']
        insurance_period_years = int(request.form['insurance_period_years'] or 0)
        insurance_period_months = int(request.form['insurance_period_months'] or 0)
        insurance_period_days = int(request.form['insurance_period_days'] or 0)
        remarks = request.form.get('remarks', '')
        modified_by = session.get('username')  # Use .get() to avoid KeyError
        modified_at = datetime.now()

        # Calculate insurance_end date
        insurance_start_date = datetime.strptime(insurance_start, '%Y-%m-%d').date()
        total_days = (insurance_period_years * 365) + (insurance_period_months * 30) + insurance_period_days
        insurance_end = insurance_start_date + timedelta(days=total_days)

        # Handle existing bills and removals
        existing_bill_paths = insurance['insurance_bill_path'].split(',') if insurance['insurance_bill_path'] else []
        removed_bills = request.form.get('removed_bills', '').split(',') if request.form.get('removed_bills') else []

        # Remove specified bills from the existing list (using full paths)
        insurance_bill_paths = [path for path in existing_bill_paths if path not in removed_bills]

        # Handle new file uploads (append to filtered list)
        if 'insurance_bill' in request.files:
            files = request.files.getlist('insurance_bill')
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            insurance_bills_folder = os.path.join(asset_folder, 'insurance_bills')
            os.makedirs(insurance_bills_folder, exist_ok=True)
            for file in files:
                if file and allowed_file(file.filename):
                    filename = f"{insurance_id}_{file.filename}"
                    file_path = os.path.join(insurance_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'insurance_bills', filename)
                    if relative_path not in insurance_bill_paths:
                        insurance_bill_paths.append(relative_path)
        
        # Join the updated bill paths into a string
        insurance_bill_path = ','.join(insurance_bill_paths) if insurance_bill_paths else None

        # Update the insurance record
        cursor.execute("""
            UPDATE insurance_details 
            SET policy_number = %s, insurance_value = %s, insurance_start = %s, 
                insurance_period = %s, insurance_end = %s, insurance_bill_path = %s, remarks = %s, 
                modified_by = %s, modified_at = %s
            WHERE insurance_id = %s
        """, (policy_number, insurance_value, insurance_start,
              f"{insurance_period_years} years, {insurance_period_months} months, {insurance_period_days} days",
              insurance_end, insurance_bill_path, remarks, modified_by, modified_at, insurance_id))

        # Send email confirmation
        details = {
            'insurance_id': insurance_id,
            'asset_id': asset_id,
            'policy_number': policy_number,
            'insurance_value': insurance_value if insurance_value else 'Not Set',
            'insurance_start': insurance_start,
            'insurance_period': f"{insurance_period_years} years, {insurance_period_months} months, {insurance_period_days} days",
            'insurance_end': insurance_end.strftime('%Y-%m-%d'),
            'insurance_bill_path': insurance_bill_path if insurance_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'modified_at': modified_at.strftime('%Y-%m-%d %H:%M:%S'),
            'modified_by': modified_by
        }
        send_confirmation_email('edit', 'insurance', insurance_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        conn.commit()

        cursor.close()
        conn.close()
        flash("Insurance updated successfully!", "edit_insurance")
        return redirect(url_for('view_insurance', insurance_id=insurance_id))

    # GET request: Fetch asset info, purchase date, and latest insurance end date
    asset = fetch_it_assets(asset_id)
    purchase_date = asset['purchase_date'] if asset else None
    latest_insurance_end = get_latest_insurance_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('edit_insurance.html', insurance=insurance, asset_id=asset_id,
                          product_name=asset['product_name'] if asset else '',
                          purchase_date=purchase_date, latest_insurance_end=latest_insurance_end,
                          permissions=page_perms['permissions'],
                          role=page_perms['role'],
                          header_permissions=header_perms['permissions']
                          )


@app.route('/view_insurance', methods=['GET'])
@app.route('/view_insurance/<id>', methods=['GET'])
@login_required
def view_insurance(id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if id and id.startswith('INS'):
        # Path 3: Treat id as insurance_id
        cursor.execute("SELECT * FROM insurance_details WHERE insurance_id = %s AND archieved = 'No' and overall_archieved ='No'", (id,))
        insurance = cursor.fetchone()
        if insurance:
            # Fetch product_name from it_assets using asset_id
            asset = fetch_it_assets(insurance['asset_id'])
            insurance['product_name'] = asset['product_name'] if asset else 'N/A'
        else:
            insurance = {}  # If no record is found, set to an empty dict
    elif id and id.startswith('IT'):
        # Path 2: Treat id as asset_id
        cursor.execute("SELECT * FROM insurance_details WHERE asset_id = %s AND archieved = 'No' and overall_archieved ='No'", (id,))
        insurance = cursor.fetchall()
        # If no records are found, set insurance to an empty list
        if insurance is None:
            insurance = []
        else:
            # Fetch product_name for each insurance record
            for ins in insurance:
                asset = fetch_it_assets(ins['asset_id'])
                ins['product_name'] = asset['product_name'] if asset else 'N/A'
    else:
        # Path 1: Fetch all non-archived records
        cursor.execute("SELECT * FROM insurance_details WHERE archieved = 'No' and overall_archieved = 'No'")
        insurance = cursor.fetchall()
        # If no records are found, set insurance to an empty list
        if insurance is None:
            insurance = []
        else:
            # Fetch product_name for each insurance record
            for ins in insurance:
                asset = fetch_it_assets(ins['asset_id'])
                ins['product_name'] = asset['product_name'] if asset else 'N/A'

    cursor.close()
    conn.close()

    page_perms = get_permissions(session, 'view_insurance')
    header_perms = get_permissions(session, 'header')

    return render_template('view_insurance.html', insurance=insurance,
                           permissions=page_perms['permissions'],
                            role=page_perms['role'],
                            header_permissions=header_perms['permissions']
                            )


# Route to delete (archive) an insurance record
@app.route('/delete_insurance/<insurance_id>', methods=['POST'])
@login_required
def delete_insurance(insurance_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the archieved column to 'Yes'
    cursor.execute("""
        UPDATE insurance_details 
        SET archieved = 'Yes', modified_by = %s, modified_at = %s
        WHERE insurance_id = %s
    """, ('nive', datetime.now(), insurance_id))
    conn.commit()

    cursor.close()
    conn.close()
    flash("Insurance record deleted successfully!", "delete_insurance")
    return redirect(url_for('view_insurance'))


def get_latest_extended_warranty_end_date(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # First, fetch the warranty_end date from the it_assets table
    cursor.execute("""
        SELECT warranty_end
        FROM it_assets
        WHERE asset_id = %s
    """, (asset_id,))
    asset = cursor.fetchone()

    # Get the warranty_end from the asset table
    warranty_end = asset['warranty_end'] if asset and asset['warranty_end'] else None

    # Fetch the latest extended warranty end date from the extended_warranty_info table
    cursor.execute("""
        SELECT extended_warranty_end_date
        FROM extended_warranty_info
        WHERE asset_id = %s AND archieved = 'No'
    """, (asset_id,))
    extended_warranties = cursor.fetchall()

    # Collect all the dates
    all_dates = [warranty_end]  # Start with the warranty_end from it_assets
    for warranty in extended_warranties:
        all_dates.append(warranty['extended_warranty_end_date'])

    # Remove None values from the list (if any)
    all_dates = [date for date in all_dates if date]

    # Find the maximum date
    latest_end_date = max(all_dates) if all_dates else None

    cursor.close()
    conn.close()
    return latest_end_date



# Route to create a new extended warranty record
@app.route('/create_extended_warranty/<asset_id>', methods=['GET', 'POST'])
@login_required
def create_extended_warranty(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_extended_warranty')
    header_perms = get_permissions(session, 'header')


    dropdown_data = display_drop_down('Create_Asset')
    product_types, companies, asset_categories, asset_types,locations, product_conditions  = dropdown_data.values()


    if request.method == 'POST':
        extended_warranty_start = request.form['extended_warranty_start']
        extended_warranty_period_years = int(request.form['extended_warranty_period_years'] or 0)
        extended_warranty_period_months = int(request.form['extended_warranty_period_months'] or 0)
        extended_warranty_period_days = int(request.form['extended_warranty_period_days'] or 0)
        warranty_provider_type = request.form['warranty_provider_type']
        warranty_provider_name = request.form.get('warranty_provider_name', '')
        warranty_provider_ph_no = request.form.get('warranty_provider_ph_no', '')
        warranty_provider_location = request.form.get('warranty_provider_location', '')
        warranty_value = request.form['warranty_value'] or None
        adp_protection = request.form['adp_protection']
        product_condition = request.form['product_condition']
        remarks = request.form.get('remarks', '')

        # Calculate extended_warranty_end_date
        extended_warranty_start_date = datetime.strptime(extended_warranty_start, '%Y-%m-%d').date()
        total_days = (extended_warranty_period_years * 365) + (extended_warranty_period_months * 30) + extended_warranty_period_days
        extended_warranty_end_date = extended_warranty_start_date + timedelta(days=total_days)

        # Handle multiple file uploads
        extended_warranty_bill_paths = []
        if 'extended_warranty_bill' in request.files:
            files = request.files.getlist('extended_warranty_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
                    warranty_bills_folder = os.path.join(asset_folder, 'extended_warranty_bills')
                    os.makedirs(warranty_bills_folder, exist_ok=True)
                    warranty_asset_id = generate_unique_id('EW')
                    filename = f"{warranty_asset_id}_{file.filename}"
                    file_path = os.path.join(warranty_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'extended_warranty_bills', filename)
                    extended_warranty_bill_paths.append(relative_path)
            extended_warranty_bill_path = ','.join(extended_warranty_bill_paths) if extended_warranty_bill_paths else None
        else:
            extended_warranty_bill_path = None

        # Generate warranty_asset_id
        warranty_asset_id = generate_unique_id('EW')
        created_by = session['username']
        created_at = datetime.now()

        # Insert into extended_warranty_info table
        cursor.execute("""
            INSERT INTO extended_warranty_info 
            (warranty_asset_id, asset_id, extended_warranty_start, extended_warranty_period, 
             extended_warranty_end_date, warranty_provider_type, warranty_provider_name, 
             warranty_provider_ph_no, warranty_provider_location, warranty_value, adp_protection, 
             extended_warranty_bill_path, product_condition, remarks, created_by, created_at, archieved, overall_archieved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (warranty_asset_id, asset_id, extended_warranty_start,
              f"{extended_warranty_period_years} years, {extended_warranty_period_months} months, {extended_warranty_period_days} days",
              extended_warranty_end_date, warranty_provider_type, warranty_provider_name,
              warranty_provider_ph_no, warranty_provider_location, warranty_value, adp_protection,
              extended_warranty_bill_path, product_condition, remarks, created_by, created_at, 'No', 'No'))
        
    # Send email confirmation
        details = {
            'warranty_asset_id': warranty_asset_id,
            'asset_id': asset_id,
            'extended_warranty_start': extended_warranty_start,
            'extended_warranty_period': f"{extended_warranty_period_years} years, {extended_warranty_period_months} months, {extended_warranty_period_days} days",
            'extended_warranty_end_date': extended_warranty_end_date.strftime('%Y-%m-%d'),
            'warranty_provider_type': warranty_provider_type,
            'warranty_provider_name': warranty_provider_name if warranty_provider_name else 'Not Set',
            'warranty_provider_ph_no': warranty_provider_ph_no if warranty_provider_ph_no else 'Not Set',
            'warranty_provider_location': warranty_provider_location if warranty_provider_location else 'Not Set',
            'warranty_value': warranty_value if warranty_value else 'Not Set',
            'adp_protection': adp_protection,
            'product_condition': product_condition,
            'extended_warranty_bill_path': extended_warranty_bill_path if extended_warranty_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'created_by': created_by,
            'created_at': created_at
        }
        send_confirmation_email('create', 'extended_warranty', warranty_asset_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        conn.commit()

        cursor.close()
        conn.close()
        flash("Extended warranty created successfully!", "create_extended_warranty")
        return redirect(url_for('view_extended_warranty', asset_id=asset_id))

    # GET request: Fetch asset info and latest extended warranty end date
    asset = fetch_it_assets(asset_id)


    purchase_date = asset['purchase_date']
    warranty_end = asset.get('warranty_end', None)  # Assuming warranty_end is a field in it_assets
    latest_extended_warranty_end = get_latest_extended_warranty_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('create_extended_warranty.html', asset_id=asset_id,
                          purchase_date=purchase_date, warranty_end=warranty_end,
                          latest_extended_warranty_end=latest_extended_warranty_end,
                          product_conditions=product_conditions,
                           permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
                          )


@app.route('/edit_extended_warranty/<warranty_asset_id>', methods=['GET', 'POST'])
@login_required
def edit_extended_warranty(warranty_asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_extended_warranty')
    header_perms = get_permissions(session, 'header')

    # Fetch the existing warranty record
    cursor.execute("SELECT * FROM extended_warranty_info WHERE warranty_asset_id = %s", (warranty_asset_id,))
    warranty = cursor.fetchone()

    if not warranty:
        flash("Extended warranty record not found.", "edit_extended_warranty")
        cursor.close()
        conn.close()
        return redirect(url_for('view_extended_warranty'))

    asset_id = warranty['asset_id']

    if request.method == 'POST':
        extended_warranty_start = request.form['extended_warranty_start']
        extended_warranty_period_years = int(request.form['extended_warranty_period_years'] or 0)
        extended_warranty_period_months = int(request.form['extended_warranty_period_months'] or 0)
        extended_warranty_period_days = int(request.form['extended_warranty_period_days'] or 0)
        warranty_provider_type = request.form['warranty_provider_type']
        warranty_provider_name = request.form.get('warranty_provider_name', '')
        warranty_provider_ph_no = request.form.get('warranty_provider_ph_no', '')
        warranty_provider_location = request.form.get('warranty_provider_location', '')
        warranty_value = request.form['warranty_value'] or None
        adp_protection = request.form['adp_protection']
        product_condition = request.form['product_condition']
        remarks = request.form.get('remarks', '')
        modified_by = session.get('username')
        modified_at = datetime.now()

        # Calculate extended_warranty_end_date
        extended_warranty_start_date = datetime.strptime(extended_warranty_start, '%Y-%m-%d').date()
        total_days = (extended_warranty_period_years * 365) + (extended_warranty_period_months * 30) + extended_warranty_period_days
        extended_warranty_end_date = extended_warranty_start_date + timedelta(days=total_days)

        # Handle existing bills and removals
        existing_bill_paths = warranty['extended_warranty_bill_path'].split(',') if warranty['extended_warranty_bill_path'] else []
        removed_bills = request.form.get('removed_bills', '').split(',') if request.form.get('removed_bills') else []
        
        # Remove specified bills from the existing list (using full paths)
        extended_warranty_bill_paths = [path for path in existing_bill_paths if path not in removed_bills]

        # Handle new file uploads (append to filtered list)
        if 'extended_warranty_bill' in request.files:
            files = request.files.getlist('extended_warranty_bill')
            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            warranty_bills_folder = os.path.join(asset_folder, 'extended_warranty_bills')
            os.makedirs(warranty_bills_folder, exist_ok=True)
            for file in files:
                if file and allowed_file(file.filename):
                    filename = f"{warranty_asset_id}_{file.filename}"
                    file_path = os.path.join(warranty_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'extended_warranty_bills', filename)
                    if relative_path not in extended_warranty_bill_paths:
                        extended_warranty_bill_paths.append(relative_path)
        
        # Join the updated bill paths into a string
        extended_warranty_bill_path = ','.join(extended_warranty_bill_paths) if extended_warranty_bill_paths else None

        # Update the warranty record
        cursor.execute("""
            UPDATE extended_warranty_info 
            SET extended_warranty_start = %s, extended_warranty_period = %s, extended_warranty_end_date = %s, 
                warranty_provider_type = %s, warranty_provider_name = %s, warranty_provider_ph_no = %s, 
                warranty_provider_location = %s, warranty_value = %s, adp_protection = %s, 
                extended_warranty_bill_path = %s, product_condition = %s, remarks = %s, 
                modified_by = %s, modified_at = %s
            WHERE warranty_asset_id = %s
        """, (extended_warranty_start,
              f"{extended_warranty_period_years} years, {extended_warranty_period_months} months, {extended_warranty_period_days} days",
              extended_warranty_end_date, warranty_provider_type, warranty_provider_name,
              warranty_provider_ph_no, warranty_provider_location, warranty_value, adp_protection,
              extended_warranty_bill_path, product_condition, remarks, modified_by, modified_at, warranty_asset_id))
        
        # Send email confirmation
        details = {
            'warranty_asset_id': warranty_asset_id,
            'asset_id': asset_id,
            'extended_warranty_start': extended_warranty_start,
            'extended_warranty_period': f"{extended_warranty_period_years} years, {extended_warranty_period_months} months, {extended_warranty_period_days} days",
            'extended_warranty_end_date': extended_warranty_end_date.strftime('%Y-%m-%d'),
            'warranty_provider_type': warranty_provider_type,
            'warranty_provider_name': warranty_provider_name if warranty_provider_name else 'Not Set',
            'warranty_provider_ph_no': warranty_provider_ph_no if warranty_provider_ph_no else 'Not Set',
            'warranty_provider_location': warranty_provider_location if warranty_provider_location else 'Not Set',
            'warranty_value': warranty_value if warranty_value else 'Not Set',
            'adp_protection': adp_protection,
            'product_condition': product_condition,
            'extended_warranty_bill_path': extended_warranty_bill_path if extended_warranty_bill_path else 'None',
            'remarks': remarks if remarks else 'None',
            'modified_by': modified_by,
            'modified_at': modified_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        send_confirmation_email('edit', 'extended_warranty', warranty_asset_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        conn.commit()

        cursor.close()
        conn.close()
        flash("Extended warranty updated successfully!", "edit_extended_warranty")
        return redirect(url_for('view_extended_warranty', asset_id=asset_id))

    # GET request: Fetch asset info and latest extended warranty end date
    asset = fetch_it_assets(asset_id)
    purchase_date = asset['purchase_date'] if asset else None
    warranty_end = asset.get('warranty_end', None) if asset else None
    latest_extended_warranty_end = get_latest_extended_warranty_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('edit_extended_warranty.html', warranty=warranty, asset_id=asset_id,
                          purchase_date=purchase_date, warranty_end=warranty_end,
                          latest_extended_warranty_end=latest_extended_warranty_end,
                          permissions=page_perms['permissions'],
                          role=page_perms['role'],
                          header_permissions=header_perms['permissions']
                          )


@app.route('/view_extended_warranty', methods=['GET'])
@app.route('/view_extended_warranty/<asset_id>', methods=['GET'])  # Updated path for asset_id
@app.route('/view_extended_warranty/warranty/<warranty_asset_id>', methods=['GET'])
@login_required
def view_extended_warranty(asset_id=None, warranty_asset_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if warranty_asset_id:
        # Path 3: Fetch a single record by warranty_asset_id
        cursor.execute("SELECT * FROM extended_warranty_info WHERE warranty_asset_id = %s AND archieved = 'No'  and overall_archieved ='No' ", (warranty_asset_id,))
        warranty = cursor.fetchone()
        if warranty:
            # Fetch product_name from it_assets using asset_id
            asset = fetch_it_assets(warranty['asset_id'])
            warranty['product_name'] = asset['product_name'] if asset else 'N/A'
        else:
            warranty = {}  # If no record is found, set to an empty dict
    elif asset_id:
        # Path 2: Fetch all records for the given asset_id
        cursor.execute("SELECT * FROM extended_warranty_info WHERE asset_id = %s AND archieved = 'No' and overall_archieved ='No'", (asset_id,))
        warranty = cursor.fetchall()
        # If no records are found, set warranty to an empty list
        if warranty is None:
            warranty = []
        else:
            # Fetch product_name for each warranty record
            for w in warranty:
                asset = fetch_it_assets(w['asset_id'])
                w['product_name'] = asset['product_name'] if asset else 'N/A'
    else:
        # Path 1: Fetch all non-archived records
        cursor.execute("SELECT * FROM extended_warranty_info WHERE archieved = 'No'and overall_archieved = 'No'")
        warranty = cursor.fetchall()
        # If no records are found, set warranty to an empty list
        if warranty is None:
            warranty = []
        else:
            # Fetch product_name for each warranty record
            for w in warranty:
                asset = fetch_it_assets(w['asset_id'])
                w['product_name'] = asset['product_name'] if asset else 'N/A'


    #     # Get permissions for the current page and header
    page_perms = get_permissions(session, 'view_extended_warranty')
    header_perms = get_permissions(session, 'header')

    cursor.close()
    conn.close()
    return render_template('view_extended_warranty.html', warranty=warranty,
                           permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
        )


# Route to delete (archive) an extended warranty record
@app.route('/delete_extended_warranty/<warranty_asset_id>', methods=['POST'])
@login_required
def delete_extended_warranty(warranty_asset_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the archieved column to 'Yes'
    cursor.execute("""
        UPDATE extended_warranty_info 
        SET archieved = 'Yes', modified_by = %s, modified_at = %s
        WHERE warranty_asset_id = %s
    """, ('nivi', datetime.now(), warranty_asset_id))
    conn.commit()

    cursor.close()
    conn.close()
    flash("Extended warranty record deleted successfully!", "delete_extended_warranty")
    return redirect(url_for('view_extended_warranty'))


@app.route('/create_technician', methods=['GET', 'POST'])
@login_required
def create_technician():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    if request.method == 'POST':
        technician_name = request.form['technician_name']
        technician_type = request.form['technician_type']
        phone_number = request.form['phone_number']
        email_address = request.form['email']
        remarks = request.form['remarks']
        address = request.form['address']
        
        created_by = session['username']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        modified_by = session['username']
        modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       
        technician_id = generate_unique_id('TI')

        try:
            # Check for duplicates
            cursor.execute("""
                SELECT * FROM technician_details 
                WHERE technician_name = %s OR phone_number = %s OR email_address = %s
            """, (technician_name, phone_number, email_address))
            existing_technician = cursor.fetchone()
            
            if existing_technician:
                flash('Technician with the same name, phone number, or email already exists.', 'create_technician')
                cursor.close()
                conn.close()
                return render_template('create_technician.html')

            # Insert into technician_details table
            cursor.execute("""
                INSERT INTO technician_details 
                (created_by, created_at, technician_name, technician_id, phone_number, email_address, 
                 address, remarks, technician_type, modified_by, modified_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (created_by, created_at, technician_name, technician_id, phone_number, email_address, 
                  address, remarks, technician_type, modified_by, modified_at))
            conn.commit()
            flash('Technician added successfully!', 'create_technician')

            # Redirect logic based on session['return_to']
            return_to = session.get('return_to', 'create_service')  # Default to create_service
            session.pop('return_to', None)  # Clear return_to after use
            session.pop('technician_form_state', None)  # Clear technician_form_state after use

            if return_to == 'edit_service' and 'service_id' in session:
                service_id = session['service_id']
                session.pop('service_id', None)  # Clear service_id
                cursor.close()
                conn.close()
                return redirect(url_for('edit_service', service_id=service_id))
            
            elif return_to == 'create_service' and 'ticket_id' in session and 'asset_id' in session:
                ticket_id = session['ticket_id']
                asset_id = session['asset_id']
                session.pop('ticket_id', None)  # Clear ticket_id
                session.pop('asset_id', None)  # Clear asset_id
                cursor.close()
                conn.close()
                return redirect(url_for('create_service', ticket_id=ticket_id, asset_id=asset_id))
            
            elif return_to == 'create_reraised_service' and 'ticket_id' in session and 'asset_id' in session:
                ticket_id = session.pop('ticket_id', None)
                asset_id = session.pop('asset_id', None)
                cursor.close()
                conn.close()
                return redirect(url_for('create_reraised_service', ticket_id=ticket_id, asset_id=asset_id))
            
            elif return_to == 'create_multiple_services' and 'asset_ids' in session:
                asset_ids = session.pop('asset_ids')
                cursor.close()
                conn.close()
                return redirect(url_for('create_multiple_services', asset_ids=asset_ids))


            # Fallback redirect
            cursor.close()
            conn.close()
            # return redirect(url_for('create_service', ticket_id='default', asset_id='default'))
            flash('Unable to determine where to return after technician creation. Please navigate manually.', 'create_technician')
            return render_template('create_technician.html',
                                permissions=page_perms['permissions'],
                                role=page_perms['role'],
                                header_permissions=header_perms['permissions'])

        except Exception as e:
            conn.rollback()
            flash(f'Error adding technician: {str(e)}', 'create_technician')
            print(f"Exception: {str(e)}")  # Debug print
            cursor.close()
            conn.close()
            return render_template('create_technician.html'
                                   )

    cursor.close()
    conn.close()
    return render_template('create_technician.html',
                            permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions'])

# # Modified save_form_state to handle create_technician
@app.route('/save_form_state', methods=['POST'])
@login_required
def save_form_state():
    form_data = request.form.to_dict(flat=False)
    session['form_state'] = form_data
    
    # Store the referrer to determine return destination
    referrer = request.referrer
    if referrer:
        if 'edit_asset' in referrer:
            session['return_to'] = 'edit_asset'
            session['asset_id'] = referrer.split('/')[-1]
        elif 'create_asset' in referrer:
            session['return_to'] = 'create_asset'
    return redirect(url_for('create_vendor'))

@app.route('/save_form_state_technician', methods=['POST'])
@login_required
def save_form_state_technician():
    try:
        print("Received request to /save_form_state_technician")
        form_data = request.form.to_dict(flat=False)
        
        session['technician_form_state'] = form_data
        
        # Store the referrer to determine return destination
        referrer = request.referrer
        print("Referrer:", referrer)
        if referrer:
            parts = referrer.split('/')
            if 'create_service' in referrer and len(parts) >= 3:
                session['return_to'] = 'create_service'
                session['ticket_id'] = parts[-2]  # Extract ticket_id
                session['asset_id'] = parts[-1]  # Extract asset_id

            elif 'edit_service' in referrer and len(parts) >= 2:
                session['return_to'] = 'edit_service'
                session['service_id'] = parts[-1]  # Extract service_id

            elif 'create_reraised_service' in referrer:
                session['return_to'] = 'create_reraised_service'
                session['ticket_id'] = parts[-2]  # Extract service_id
                session['asset_id'] = parts[-1]  # Extract asset_id

                print('ticket_id', session['ticket_id'], parts[-2])
                print('asset_id', session['asset_id'], parts[-1])

            elif 'edit_reraised_service' in referrer:
                session['return_to'] = 'create_reraised_service'
                session['ticket_id'] = parts[-2]  # Extract service_id
                session['asset_id'] = parts[-1]  # Extract asset_id

                print('ticket_id', session['ticket_id'])
                print('asset_id', session['asset_id'])

            elif 'create_multiple_services' in referrer:
                session['return_to'] = 'create_multiple_services'
                # Optional: save asset_ids from query string
                from urllib.parse import urlparse, parse_qs
                query = urlparse(referrer).query
                asset_ids = parse_qs(query).get('asset_ids', [])
                session['asset_ids'] = asset_ids[0] if asset_ids else ''



            else:
                session['return_to'] = 'create_service'  # Default fallback
        else:
            session['return_to'] = 'create_service'  # Default if no referrer

        # print("Session after update:", session)
        return redirect(url_for('create_technician'))
    except Exception as e:
        print(f"Error in save_form_state_technician: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/check_asset_status', methods=['GET', 'POST'])
@login_required
def check_asset_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    # Handle POST request to update status
    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        new_condition = request.form.get('product_condition')
        frequency = request.form.get('status_check_frequency')
        audit_remarks = request.form.get('audit_remarks')

        # Update the asset's condition, status check dates, and audit remarks
        last_status_check = datetime.now().date()
        if frequency == '3M':
            next_status_check = last_status_check + relativedelta(months=3)
        else:  # 6M
            next_status_check = last_status_check + relativedelta(months=6)

        modified_by =session['username']

        cursor.execute("""
            UPDATE it_assets
            SET product_condition = %s,
                last_status_check = %s,
                next_status_check = %s,
                status_check_frequency = %s,
                audit_remarks = %s,
                modified_by = %s,
                modified_at = NOW()
            WHERE asset_id = %s
        """, (new_condition, last_status_check, next_status_check, frequency, audit_remarks, modified_by, asset_id))
        conn.commit()
        flash('Asset status updated successfully!', 'check_asset_status')

    # Get filter parameters
    selected_employee = request.args.get('employee', '')
    search_query = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of assets per page

    # Build the query for counting total assets (for pagination)
    count_query = """
        SELECT COUNT(DISTINCT ia.asset_id) as total
        FROM it_assets ia
        LEFT JOIN assets_users au ON ia.asset_id = au.asset_id AND au.archieved = 'No'
        WHERE ia.archieved = 'No' AND ia.under_audit = 'Yes'
    """
    count_params = []

    # Build the main query
    query = """
       WITH latest_assignments AS (
            SELECT *
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY created_at DESC) AS rn
                FROM assets_users
                WHERE archieved = 'No'
            ) sub
            WHERE rn = 1
        )
        SELECT ia.*, au.assigned_user, au.employee_code, au.effective_date
        FROM it_assets ia
        LEFT JOIN latest_assignments au ON ia.asset_id = au.asset_id
        WHERE ia.archieved = 'No' AND ia.under_audit = 'Yes'

    """
    params = []

    # Apply employee filter
    if selected_employee:
        query += " AND au.employee_code = %s"
        count_query += " AND au.employee_code = %s"
        params.append(selected_employee)
        count_params.append(selected_employee)

    # Apply search filter
    if search_query:
        query += " AND (ia.asset_id LIKE %s OR ia.product_name LIKE %s OR ia.product_type LIKE %s)"
        count_query += " AND (ia.asset_id LIKE %s OR ia.product_name LIKE %s OR ia.product_type LIKE %s)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern])
        count_params.extend([search_pattern, search_pattern, search_pattern])

    # Get total count for pagination
    cursor.execute(count_query, count_params)
    total_assets = cursor.fetchone()['total']
    total_pages = (total_assets + per_page - 1) // per_page

    # Apply pagination
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])

    # Fetch assets
    cursor.execute(query, params)
    assets = cursor.fetchall()

    # Fetch the earliest last_status_check date
    cursor.execute("SELECT MIN(last_status_check) as first_check FROM it_assets WHERE last_status_check IS NOT NULL AND under_audit = 'Yes'")
    first_check_result = cursor.fetchone()
    first_check_date = first_check_result['first_check'] if first_check_result['first_check'] else None
    one_week_later = first_check_date + timedelta(days=7) if first_check_date else None

    # Process assets
    current_date = datetime.now().date()
    for asset in assets:
        # Determine the first assignment date from assets_users
        first_assignment_date = None
        if asset['effective_date']:
            cursor.execute("""
                SELECT MIN(effective_date) as first_assignment
                FROM assets_users
                WHERE asset_id = %s AND archieved = 'No'
            """, (asset['asset_id'],))
            result = cursor.fetchone()
            first_assignment_date = result['first_assignment'] if result['first_assignment'] else None

        # Set last_status_check and next_status_check for new entries
        if not asset['last_status_check']:
            base_date = first_assignment_date or asset['purchase_date'] or asset['created_at'].date()
            asset['last_status_check'] = None
            frequency = asset['status_check_frequency'] or '3M'
            if frequency == '3M':
                asset['next_status_check'] = base_date + relativedelta(months=3)
            else:
                asset['next_status_check'] = base_date + relativedelta(months=6)
        else:
            if not asset['next_status_check']:
                frequency = asset['status_check_frequency'] or '3M'
                if frequency == '3M':
                    asset['next_status_check'] = asset['last_status_check'] + relativedelta(months=3)
                else:
                    asset['next_status_check'] = asset['last_status_check'] + relativedelta(months=6)

        # Mark if the asset is overdue for a check
        asset['is_overdue'] = asset['next_status_check'] <= current_date if asset['next_status_check'] else False

        # Determine check status for color coding
        asset['is_checked'] = asset['last_status_check'] is not None
        asset['not_checked_within_week'] = False
        asset['not_checked_after_week'] = False
        if first_check_date and one_week_later and not asset['last_status_check']:
            if current_date <= one_week_later:
                asset['not_checked_within_week'] = True
            else:
                asset['not_checked_after_week'] = True

    # Get unique employees for the filter dropdown
    cursor.execute("""
        SELECT DISTINCT assigned_user, employee_code
        FROM assets_users
        WHERE archieved = 'No' and overall_archieved = 'No' AND asset_id IN (
            SELECT asset_id FROM it_assets WHERE under_audit = 'Yes' AND archieved = 'No'
        )
    """)
    employees = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(
        'check_asset_status.html',
        assets=assets,
        employees=employees,
        selected_employee=selected_employee,
        first_check_date=first_check_date,
        page=page,
        total_pages=total_pages,
        search_query=search_query,
        permissions=page_perms['permissions'],
        role=page_perms['role'],
        header_permissions=header_perms['permissions']
    )

def retrieve_asset_data(search_query='', product_type='', location='', page=1, per_page=10):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Build the query for counting total assets (for pagination)
    count_query = """
        SELECT COUNT(*) as total
        FROM it_assets
        WHERE archieved = 'No'
    """
    count_params = []

    # Build the main query
    query = """
        SELECT *
        FROM it_assets
        WHERE archieved = 'No' 
    """
    params = []

    # Apply product_type filter
    if product_type:
        query += " AND product_type = %s"
        count_query += " AND product_type = %s"
        params.append(product_type)
        count_params.append(product_type)

    # Apply location filter
    if location:
        query += " AND location = %s"
        count_query += " AND location = %s"
        params.append(location)
        count_params.append(location)

    # Apply search filter
    if search_query:
        query += " AND (asset_id LIKE %s OR product_name LIKE %s OR serial_no LIKE %s)"
        count_query += " AND (asset_id LIKE %s OR product_name LIKE %s OR serial_no LIKE %s)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern])
        count_params.extend([search_pattern, search_pattern, search_pattern])

    # Get total count for pagination
    cursor.execute(count_query, count_params)
    total_assets = cursor.fetchone()['total']
    total_pages = (total_assets + per_page - 1) // per_page

    # Apply pagination
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])

    # Fetch assets
    cursor.execute(query, params)
    assets = cursor.fetchall()

    cursor.close()
    conn.close()
    return assets, total_pages


from datetime import datetime

def in_warranty_out_warranty(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    current_date = datetime.now().date()
    in_warranty = False

    try:
        # Fetch warranty details from it_assets
        cursor.execute("""
            SELECT warranty_end, extended_warranty_end
            FROM it_assets
            WHERE asset_id = %s
        """, (asset_id,))
        asset = cursor.fetchone()

        if asset:
            # Check warranty_end
            if asset['warranty_end'] and asset['warranty_end'] >= current_date:
                in_warranty = True
            # Check extended_warranty_end in it_assets
            if asset['extended_warranty_end'] and asset['extended_warranty_end'] >= current_date:
                in_warranty = True

        # Consume any remaining results from the first query
        cursor.fetchall()  # Ensure no unread results remain

        # Check extended_warranty_info table
        cursor.execute("""
            SELECT extended_warranty_end_date
            FROM extended_warranty_info
            WHERE asset_id = %s
        """, (asset_id,))
        ext_warranty = cursor.fetchone()

        if ext_warranty and ext_warranty['extended_warranty_end_date'] and ext_warranty['extended_warranty_end_date'] >= current_date:
            in_warranty = True

        # Consume any remaining results from the second query
        cursor.fetchall()  # Ensure no unread results remain

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return 'in_warranty' if in_warranty else 'out_warranty'


@app.route('/all_assets', methods=['GET', 'POST'])
@login_required
def all_assets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_assets')
    header_perms = get_permissions(session, 'header')

    if request.method == 'POST':
        selected_asset_ids = request.form.getlist('selected_assets')
        if not selected_asset_ids:
            flash('Please select at least one asset to create a service.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('all_assets'))

        # Redirect to the new create_multiple_services route with selected asset_ids
        cursor.close()
        conn.close()
        return redirect(url_for('create_multiple_services', asset_ids=','.join(selected_asset_ids)))

    # GET request: Fetch data for the page
    product_type = request.args.get('product_type', '')
    location = request.args.get('location', '')  # New location filter
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))

    # Fetch assets using the helper function
    assets, total_pages = retrieve_asset_data(
        search_query=search_query,
        product_type=product_type,
        location=location,
        page=page
    )

    # Fetch unique product types for the filter dropdown
    cursor.execute("SELECT DISTINCT product_type FROM it_assets WHERE archieved = 'No'")
    product_types = [row['product_type'] for row in cursor.fetchall()]

    # Fetch unique locations for the filter dropdown
    cursor.execute("SELECT DISTINCT location FROM it_assets WHERE archieved = 'No'")
    locations = [row['location'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return render_template(
        'all_assets.html',
        assets=assets,
        product_types=product_types,
        locations=locations,  # Pass locations to template
        selected_product_type=product_type,
        selected_location=location,  # Pass selected location
        search_query=search_query,
        page=page,
        total_pages=total_pages,
         permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
    )


@app.route('/create_multiple_services', methods=['GET', 'POST'])
@login_required
def create_multiple_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    # Get the selected asset_ids from the query parameter
    asset_ids = request.args.get('asset_ids', '')
    if not asset_ids:
        flash('No assets selected.', 'create_multiple_services')
        cursor.close()
        conn.close()
        return redirect(url_for('all_assets'))

    selected_asset_ids = asset_ids.split(',')

    if request.method == 'POST':
        # Generate a common ticket_id starting with 'S'
        cursor.execute("SELECT ticket_id FROM service_details WHERE ticket_id LIKE 'S%' ORDER BY ticket_id DESC LIMIT 1")
        last_ticket = cursor.fetchone()
        if last_ticket:
            last_number = int(last_ticket['ticket_id'][1:]) if last_ticket['ticket_id'][1:].isdigit() else 0
            ticket_id = f"S{last_number + 1:04d}"
        else:
            ticket_id = 'S0001'


        technician_source = request.form['technician_source']
        
        # Set technician_name and technician_id based on technician_source
        if technician_source == 'inhouse':
            technician_name = session['username']
            technician_id = session['emp_id']
        else:  # outhouse
            technician_name = request.form['technician_name']
            technician_id = request.form['technician_id']



        # technician_name = request.form['technician_name']
        # technician_id = request.form['technician_id']
        reference_name = request.form['reference_name']
        work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)

        # Handle multiple file uploads
        service_bill_paths = []
        if 'service_bill' in request.files:
            files = request.files.getlist('service_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    ticket_folder = os.path.join(app.config['UPLOAD_FOLDER'], ticket_id)
                    service_bills_folder = os.path.join(ticket_folder, 'service_bills')
                    os.makedirs(service_bills_folder, exist_ok=True)
                    filename = f"{ticket_id}_{file.filename}"
                    file_path = os.path.join(service_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(ticket_id, 'service_bills', filename)
                    service_bill_paths.append(relative_path)
            service_bill_path = ','.join(service_bill_paths) if service_bill_paths else None
        else:
            service_bill_path = None

        # Generate unique service_ids for all selected assets
        service_ids = generate_unique_id('SI', count=len(selected_asset_ids))

        # Create a service for each selected asset
        created_service_ids = []
        try:
            for asset_id, service_id in zip(selected_asset_ids, service_ids):
                created_by = session['username']
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                warranty_type = in_warranty_out_warranty(asset_id)

                cursor.execute("""
                    INSERT INTO service_details (service_id, ticket_id, asset_id, service_case_id, technician_source, technician_name, technician_id, 
                                         work_done, next_service_date, service_charge, remarks, service_bill_path, 
                                         created_by, created_at, warranty_type, reference_name,archieved, overall_archieved, multiple_service_bill_path )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (service_id, ticket_id, asset_id, service_case_id,technician_source, technician_name, technician_id, work_done, 
                      next_service_date, service_charge, remarks, service_bill_path, created_by, created_at, warranty_type,
                        reference_name, 'No', 'No',service_bill_path ))
                created_service_ids.append(service_id)
            conn.commit()

            # Send email confirmation
            details = {
                'ticket_id': ticket_id,
                'service_ids': ', '.join(created_service_ids),
                'asset_ids': ', '.join(selected_asset_ids),
                'technician_source': technician_source,
                'technician_name': technician_name,
                'work_done': work_done,
                'next_service_date': next_service_date if next_service_date else 'Not Set',
                'service_charge': service_charge if service_charge else 'Not Set',
                'created_at': created_at,
                'remarks': remarks if remarks else 'None'
            }
            send_confirmation_email('create', 'multiple_services', ticket_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

            flash(f"Multiple services created successfully with ticket ID {ticket_id}!", "create_multiple_services")
            cursor.close()
            conn.close()
            return redirect(url_for('create_multiple_services', ticket_id=ticket_id, service_ids=','.join(created_service_ids)))

        except mysql.connector.errors.IntegrityError as e:
            conn.rollback()  # Roll back the transaction on error
            if "Duplicate entry" in str(e):
                flash(f"Error: The reference name '{reference_name}' is already in use. Please use a unique reference name.", "create_multiple_services")
            else:
                flash(f"Database error: {str(e)}", "create_multiple_services")
            # Stay on the page by falling through to the GET handling

    # GET request: Fetch technicians for dropdown
    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('create_multiple_services.html', asset_ids=selected_asset_ids, technicians=technicians,
                            permissions=page_perms['permissions'],
                        role=page_perms['role'],
                        header_permissions=header_perms['permissions']
                           )

@app.route('/edit_related_multiple_services', methods=['GET', 'POST'])
@login_required
def edit_related_multiple_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    # Get ticket IDs and reference names starting with 'S' for dropdown
    cursor.execute("""
        SELECT DISTINCT ticket_id, reference_name 
        FROM service_details 
        WHERE ticket_id LIKE 'S%' 
        ORDER BY ticket_id
    """)
    ticket_ids = cursor.fetchall()

    if request.method == 'POST' and 'ticket_id' in request.form:
        ticket_id = request.form['ticket_id']
        if not ticket_id:
            flash('Please provide a Ticket ID.', 'danger')
            cursor.close()
            conn.close()
            return render_template('enter_ticket_id.html', ticket_ids=ticket_ids)

        cursor.execute("""
            SELECT service_id, asset_id, technician_name, work_done, reference_name
            FROM service_details
            WHERE ticket_id = %s
        """, (ticket_id,))
        services = cursor.fetchall()

        if not services:
            flash(f"No services found for Ticket ID {ticket_id}.", 'edit_related_multiple_services')
            cursor.close()
            conn.close()
            return redirect(url_for('all_assets'))

        page = int(request.args.get('page', 1))
        per_page = 10
        total_services = len(services)
        total_pages = (total_services + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_services = services[start:end]

        cursor.close()
        conn.close()
        return render_template(
            'list_related_services.html',
            services=paginated_services,
            ticket_id=ticket_id,
            page=page,
            total_pages=total_pages,
             permissions=page_perms['permissions'],
            role=page_perms['role'],
            header_permissions=header_perms['permissions']
        )

    cursor.close()
    conn.close()
    return render_template('enter_ticket_id.html', ticket_ids=ticket_ids,
                            permissions=page_perms['permissions'],
            role=page_perms['role'],
            header_permissions=header_perms['permissions']
                           )


@app.route('/edit_related_multiple_services_form/<ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_related_multiple_services_form(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')

    if request.method == 'POST':
        selected_services = request.form.get('selected_services', '').split(',')
        if not selected_services or selected_services == ['']:
            flash('No services selected for editing.', 'edit_related_multiple_services')
            cursor.close()
            conn.close()
            return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))

        # Fetch current service details
        in_placeholders = ','.join(['%s'] * len(selected_services))
        query = """
            SELECT service_id, asset_id, work_done, technician_name, technician_id, next_service_date,
                   service_charge, remarks, service_case_id, service_bill_path, multiple_service_bill_path
            FROM service_details
            WHERE ticket_id = %s AND service_id IN ({})
        """.format(in_placeholders)
        params = (ticket_id,) + tuple(selected_services)
        cursor.execute(query, params)
        services = cursor.fetchall()

        if not services:
            flash(f"No services found for Ticket ID {ticket_id} with selected IDs.", 'edit_related_multiple_services')
            cursor.close()
            conn.close()
            return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))


        technician_source = request.form['technician_source']
        
        # Set technician_name and technician_id based on technician_source
        if technician_source == 'inhouse':
            technician_name = session['username']
            technician_id = session['emp_id']
        else:  # outhouse
            technician_name = request.form['technician_name']
            technician_id = request.form['technician_id']

        # technician_name = request.form['technician_name']
        # technician_id = request.form['technician_id']
        new_work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)

        # Handle file uploads
        service_bill_paths = []
        if 'service_bill' in request.files:
            files = request.files.getlist('service_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    ticket_folder = os.path.join(app.config['UPLOAD_FOLDER'], ticket_id)
                    service_bills_folder = os.path.join(ticket_folder, 'service_bills')
                    os.makedirs(service_bills_folder, exist_ok=True)
                    filename = f"{ticket_id}_{file.filename}"
                    file_path = os.path.join(service_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(ticket_id, 'service_bills', filename)
                    service_bill_paths.append(relative_path)

        # Handle removed files
        removed_bills = request.form.get('removed_bills', '').split(',')
        if removed_bills == ['']:
            removed_bills = []

        # Update selected services
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        modified_by = session['username']
        for service in services:
            existing_work_done = service['work_done'] or ''
            updated_work_done = (
                f"{existing_work_done}, [{current_timestamp}] {new_work_done}" if new_work_done and existing_work_done
                else f"[{current_timestamp}] {new_work_done}" if new_work_done
                else existing_work_done
            )

            # Handle multiple_service_bill_path and service_bill_path
            existing_multiple_bill_paths = service['multiple_service_bill_path'].split(',') if service['multiple_service_bill_path'] else []
            existing_service_bill_paths = service['service_bill_path'].split(',') if service['service_bill_path'] else []

            # Remove files from both paths if in removed_bills
            updated_multiple_bill_paths = [path for path in existing_multiple_bill_paths if path not in removed_bills]
            updated_service_bill_paths = [path for path in existing_service_bill_paths if path not in removed_bills]

            # Add new uploads to both multiple_service_bill_path and service_bill_path
            if service_bill_paths:
                updated_multiple_bill_paths.extend(service_bill_paths)
                updated_service_bill_paths.extend(service_bill_paths)

            # Ensure uniqueness and join back to strings
            updated_multiple_bill_paths = list(dict.fromkeys(updated_multiple_bill_paths))  # Remove duplicates
            updated_service_bill_paths = list(dict.fromkeys(updated_service_bill_paths))    # Remove duplicates
            multiple_service_bill_path = ','.join(updated_multiple_bill_paths) if updated_multiple_bill_paths else None
            service_bill_path = ','.join(updated_service_bill_paths) if updated_service_bill_paths else None

            # Update the database
            cursor.execute("""
                UPDATE service_details
                SET technician_source = %s, technician_name = %s, technician_id = %s, work_done = %s, next_service_date = %s,
                    service_charge = %s, remarks = %s, service_case_id = %s, service_bill_path = %s,
                    multiple_service_bill_path = %s, modified_by = %s, modified_at = NOW()
                WHERE service_id = %s
            """, (technician_source, technician_name, technician_id, updated_work_done, next_service_date, service_charge, remarks,
                  service_case_id, service_bill_path, multiple_service_bill_path, modified_by, service['service_id']))

        conn.commit()

        # Send email confirmation
        details = {
            'ticket_id': ticket_id,
            'service_ids': ', '.join(selected_services),
            'asset_ids': ', '.join([service['asset_id'] for service in services]),
            'technician_source':technician_source,
            'technician_name': technician_name,
            'work_done': new_work_done if new_work_done else 'No new work done added',
            'next_service_date': next_service_date if next_service_date else 'Not Set',
            'service_charge': service_charge if service_charge else 'Not Set',
            'modified_at': current_timestamp,
            'remarks': remarks if remarks else 'None'
        }
        send_confirmation_email('edit', 'multiple_services', ticket_id, details, to_email='nivetha@tapmobi.in', cc_email=None)

        cursor.close()
        conn.close()
        flash(f"Selected services for Ticket ID {ticket_id} updated successfully!", "edit_related_multiple_services")
        return redirect(url_for('all_assets'))

    # GET request: Fetch selected services for display
    selected_services = request.args.get('selected_services', '').split(',')
    if not selected_services or selected_services == ['']:
        flash('Please select services to edit.', 'edit_related_multiple_services')
        cursor.close()
        conn.close()
        return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))

    in_placeholders = ','.join(['%s'] * len(selected_services))
    query = """
        SELECT service_id, asset_id, technician_name, technician_id, work_done, next_service_date,
               service_charge, remarks, service_case_id, service_bill_path, multiple_service_bill_path
        FROM service_details
        WHERE ticket_id = %s AND service_id IN ({})
    """.format(in_placeholders)
    params = (ticket_id,) + tuple(selected_services)
    cursor.execute(query, params)
    services = cursor.fetchall()

    if not services:
        flash(f"No services found for Ticket ID {ticket_id} with selected IDs.", 'edit_related_multiple_services')
        cursor.close()
        conn.close()
        return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))

    # Group work_done entries for display
    work_done_groups = {}
    for service in services:
        work_done = service['work_done'] or 'No work done recorded yet'
        if work_done not in work_done_groups:
            work_done_groups[work_done] = []
        work_done_groups[work_done].append(service['asset_id'])

    work_done_display = []
    for work_done, asset_ids in work_done_groups.items():
        if len(asset_ids) == len(services):
            work_done_display.append({'label': 'For all selected assets', 'work_done': work_done})
        else:
            work_done_display.append({'label': f"Asset IDs: {', '.join(map(str, asset_ids))}", 'work_done': work_done})

    asset_ids = [service['asset_id'] for service in services]
    service = services[0]  # Use first service for pre-filling shared fields

    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template(
        'edit_related_multiple_services_form.html',
        ticket_id=ticket_id,
        asset_ids=asset_ids,
        technicians=technicians,
        service=service,
        selected_services=','.join(selected_services),
        work_done_display=work_done_display,
        permissions=page_perms['permissions'],
        role=page_perms['role'],
        header_permissions=header_perms['permissions']
    )


def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = 'nivetha@tapmobi.in'

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def check_and_send_alerts(get_db_connection):  # Pass db connection function as parameter

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = datetime.now().date()
    
    # 1. Warranty Alerts (1 month before)
    warranty_threshold = today + timedelta(days=30)
    cursor.execute("""
        SELECT asset_id, product_name, warranty_end 
        FROM it_assets 
        WHERE warranty_end IS NOT NULL 
        AND warranty_end <= %s 
        AND warranty_end >= %s
    """, (warranty_threshold, today))
    warranty_alerts = cursor.fetchall()


    for alert in warranty_alerts:
        subject = f"Warranty Alert: {alert['product_name']}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; color: #191970; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f0f0f0; color: #191970; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Warranty Alert</h2>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    <p>Your asset warranty is nearing its end:</p>
                    <table>
                        <tr><th>Field</th><th>Value</th></tr>
                        <tr><td>Asset ID</td><td>{alert['asset_id']}</td></tr>
                        <tr><td>Product</td><td>{alert['product_name']}</td></tr>
                        <tr><td>Warranty End Date</td><td>{alert['warranty_end']}</td></tr>
                        <tr><td>Days Remaining</td><td>{(alert['warranty_end'] - today).days}</td></tr>
                    </table>
                </div>
                <div class="footer">
                    Regards,<br>Asset Management Team
                </div>
            </div>
        </body>
        </html>
        """
        send_email_with_cc('nivetha@tapmobi.in', subject, html_body, cc_email=None)

    # 2. Extended Warranty Alerts (1 month before)
    cursor.execute("""
        SELECT asset_id, product_name, extended_warranty_end 
        FROM it_assets 
        WHERE extended_warranty_end IS NOT NULL 
        AND extended_warranty_end <= %s 
        AND extended_warranty_end >= %s
    """, (warranty_threshold, today))
    ext_warranty_alerts = cursor.fetchall()

    for alert in ext_warranty_alerts:
        subject = f"Extended Warranty Alert: {alert['product_name']}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; color: #191970; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f0f0f0; color: #191970; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Extended Warranty Alert</h2>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    <p>Your asset extended warranty is nearing its end:</p>
                    <table>
                        <tr><th>Field</th><th>Value</th></tr>
                        <tr><td>Asset ID</td><td>{alert['asset_id']}</td></tr>
                        <tr><td>Product</td><td>{alert['product_name']}</td></tr>
                        <tr><td>Extended Warranty End Date</td><td>{alert['extended_warranty_end']}</td></tr>
                        <tr><td>Days Remaining</td><td>{(alert['extended_warranty_end'] - today).days}</td></tr>
                    </table>
                </div>
                <div class="footer">
                    Regards,<br>Asset Management Team
                </div>
            </div>
        </body>
        </html>
        """
        send_email_with_cc('nivetha@tapmobi.in', subject, html_body, cc_email=None)

    # 3. Insurance Alerts (1 year before)
    insurance_threshold = today + timedelta(days=365)
    cursor.execute("""
        SELECT id.asset_id, id.insurance_end, vayu_asset_management.product_name
        FROM insurance_details id
        JOIN it_assets it ON id.asset_id = vayu_asset_management.asset_id
        WHERE id.insurance_end IS NOT NULL 
        AND id.insurance_end <= %s 
        AND id.insurance_end >= %s
    """, (insurance_threshold, today))
    insurance_alerts = cursor.fetchall()

    for alert in insurance_alerts:
        subject = f"Insurance Alert for Asset {alert['asset_id']}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; color: #191970; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f0f0f0; color: #191970; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Insurance Alert</h2>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    <p>Your asset insurance is nearing its renewal date:</p>
                    <table>
                        <tr><th>Field</th><th>Value</th></tr>
                        <tr><td>Asset ID</td><td>{alert['asset_id']}</td></tr>
                        <tr><td>Product</td><td>{alert['product_name']}</td></tr>
                        <tr><td>Insurance End Date</td><td>{alert['insurance_end']}</td></tr>
                        <tr><td>Days Remaining</td><td>{(alert['insurance_end'] - today).days}</td></tr>
                    </table>
                </div>
                <div class="footer">
                    Regards,<br>Asset Management Team
                </div>
            </div>
        </body>
        </html>
        """
        send_email_with_cc('nivetha@tapmobi.in', subject, html_body, cc_email=None)

    # 4. Service Alerts (15 days before)
    service_threshold = today + timedelta(days=15)
    cursor.execute("""
        SELECT sd.asset_id, sd.next_service_date, vayu_asset_management.product_name
        FROM service_details sd
        JOIN it_assets it ON sd.asset_id = vayu_asset_management.asset_id
        WHERE sd.next_service_date IS NOT NULL 
        AND sd.next_service_date <= %s 
        AND sd.next_service_date >= %s
    """, (service_threshold, today))
    service_alerts = cursor.fetchall()

    for alert in service_alerts:
        subject = f"Service Alert for Asset {alert['asset_id']}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; color: #191970; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f0f0f0; color: #191970; }}
                .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Service Alert</h2>
                </div>
                <div class="content">
                    <p>Dear User,</p>
                    <p>Your asset is due for service:</p>
                    <table>
                        <tr><th>Field</th><th>Value</th></tr>
                        <tr><td>Asset ID</td><td>{alert['asset_id']}</td></tr>
                        <tr><td>Product</td><td>{alert['product_name']}</td></tr>
                        <tr><td>Next Service Date</td><td>{alert['next_service_date']}</td></tr>
                        <tr><td>Days Remaining</td><td>{(alert['next_service_date'] - today).days}</td></tr>
                    </table>
                </div>
                <div class="footer">
                    Regards,<br>Asset Management Team
                </div>
            </div>
        </body>
        </html>
        """
        send_email_with_cc('nivetha@tapmobi.in', subject, html_body, cc_email=None)

    # 5. AMC Recurring Alerts
    cursor.execute("""
        SELECT asset_id, purchase_date, recurring_alert_for_amc, product_name 
        FROM it_assets 
        WHERE recurring_alert_for_amc IS NOT NULL
    """)
    amc_assets = cursor.fetchall()

    for asset in amc_assets:
        alerts = eval(asset['recurring_alert_for_amc'])  # Convert string to list
        if isinstance(asset['purchase_date'], str):
            purchase_date = datetime.strptime(asset['purchase_date'], '%Y-%m-%d').date()
        else:
            purchase_date = asset['purchase_date']
        
        for event_name, value, unit in alerts:
            value = int(value)
            if unit.lower() == 'days':
                interval = timedelta(days=value)
            elif unit.lower() == 'months':
                interval = timedelta(days=value * 30)  # Approximate conversion
            elif unit.lower() == 'years':
                interval = timedelta(days=value * 365)

            days_since_purchase = (today - purchase_date).days
            if days_since_purchase % interval.days == 0 and days_since_purchase > 0:
                subject = f"AMC Alert: {event_name} for {asset['asset_id']}"
                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                        .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
                        .content {{ padding: 20px; color: #191970; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                        th {{ background-color: #f0f0f0; color: #191970; }}
                        .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>AMC Alert</h2>
                        </div>
                        <div class="content">
                            <p>Dear User,</p>
                            <p>Recurring AMC alert:</p>
                            <table>
                                <tr><th>Field</th><th>Value</th></tr>
                                <tr><td>Asset ID</td><td>{asset['asset_id']}</td></tr>
                                <tr><td>Product</td><td>{asset['product_name']}</td></tr>
                                <tr><td>Event</td><td>{event_name}</td></tr>
                                <tr><td>Recurrence</td><td>Every {value} {unit}</td></tr>
                                <tr><td>Purchase Date</td><td>{purchase_date}</td></tr>
                            </table>
                        </div>
                        <div class="footer">
                            Regards,<br>Asset Management Team
                        </div>
                    </div>
                </body>
                </html>
                """
                send_email_with_cc('nivetha@tapmobi.in', subject, html_body, cc_email=None)

    cursor.close()
    conn.close()

scheduler = BackgroundScheduler()
start_now = datetime.now()
print("start_now =", start_now)
scheduler.add_job(lambda: check_and_send_alerts(get_db_connection), 'interval', days=1)
# scheduler.add_job(lambda: check_and_send_alerts(get_db_connection), 'interval', minutes=1)
scheduler.start()


# @app.route('/upcoming_alerts', methods=['GET', 'POST'])
# def upcoming_alerts():
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     page_perms = get_permissions(session, 'view_service')
#     header_perms = get_permissions(session, 'header')
    
#     alert_type = request.args.get('alert_type', 'all')
#     date_range = request.args.get('date_range', 30, type=int)
    
#     # today = datetime.now().date()
#     today = date.today()  
#     end_date = today + timedelta(days=date_range)
    
#     alerts = []
    
#     if alert_type in ['all', 'warranty_end']:
#         cursor.execute("""
#             SELECT asset_id, product_name, warranty_end as alert_date, 'Warranty End' as alert_type
#             FROM it_assets 
#             WHERE warranty_end IS NOT NULL 
#             AND warranty_end BETWEEN %s AND %s
#         """, (today, end_date))
#         alerts.extend(cursor.fetchall())
    
#     if alert_type in ['all', 'extended_warranty_end']:
#         cursor.execute("""
#             SELECT asset_id, product_name, extended_warranty_end as alert_date, 'Extended Warranty End' as alert_type
#             FROM it_assets 
#             WHERE extended_warranty_end IS NOT NULL 
#             AND extended_warranty_end BETWEEN %s AND %s
#         """, (today, end_date))
#         alerts.extend(cursor.fetchall())

#     if alert_type in ['all', 'extended_warranty_end_extended_warranty_info']:
#         cursor.execute("""
#             SELECT ewi.asset_id, ewi.extended_warranty_end_date as alert_date, 'Extended Warranty End (Seperate)' as alert_type, 
#                    ia.product_name
#             FROM extended_warranty_info ewi
#             JOIN vayu_asset_management.it_assets ia ON ewi.asset_id = ia.asset_id
#             WHERE ewi.extended_warranty_end_date IS NOT NULL 
#             AND ewi.extended_warranty_end_date BETWEEN %s AND %s
#         """, (today, end_date))
#         alerts.extend(cursor.fetchall())
    
#     if alert_type in ['all', 'insurance_end']:
#         cursor.execute("""
#             SELECT asset_id, insurance_end as alert_date, 'Insurance End' as alert_type
#             FROM insurance_details 
#             WHERE insurance_end IS NOT NULL 
#             AND insurance_end BETWEEN %s AND %s
#         """, (today, end_date))
#         alerts.extend(cursor.fetchall())
    
#     if alert_type in ['all', 'next_service_date']:
#         cursor.execute("""
#             SELECT asset_id, next_service_date as alert_date, 'Next Service' as alert_type
#             FROM service_details 
#             WHERE next_service_date IS NOT NULL 
#             AND next_service_date BETWEEN %s AND %s
#         """, (today, end_date))
#         alerts.extend(cursor.fetchall())
    
#     cursor.close()
#     conn.close()
    
#     alerts.sort(key=lambda x: x['alert_date'])
    
#     return render_template('upcoming_alerts.html', 
#                          alerts=alerts,
#                          alert_type=alert_type,
#                          date_range=date_range,
#                          today=today,
#                         permissions=page_perms['permissions'],
#                         role=page_perms['role'],
#                         header_permissions=header_perms['permissions']
#                          )

@app.route('/upcoming_alerts', methods=['GET', 'POST'])
@login_required
def upcoming_alerts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    page_perms = get_permissions(session, 'view_service')
    header_perms = get_permissions(session, 'header')
    
    alert_type = request.args.get('alert_type', 'all')
    date_range = request.args.get('date_range', 30, type=int)
    
    today = date.today()
    end_date = today + timedelta(days=date_range)

    # Gather all warranty-related alerts regardless of alert_type
    warranty_alerts = []

    # Warranty End
    cursor.execute("""
        SELECT asset_id, product_name, warranty_end as alert_date, 'Warranty End' as alert_type
        FROM it_assets 
        WHERE warranty_end IS NOT NULL 
        AND warranty_end BETWEEN %s AND %s
    """, (today, end_date))
    warranty_alerts.extend(cursor.fetchall())

    # Extended Warranty End from it_assets
    cursor.execute("""
        SELECT asset_id, product_name, extended_warranty_end as alert_date, 'Extended Warranty End' as alert_type
        FROM it_assets 
        WHERE extended_warranty_end IS NOT NULL 
        AND extended_warranty_end BETWEEN %s AND %s
    """, (today, end_date))
    warranty_alerts.extend(cursor.fetchall())

    # Extended Warranty End from extended_warranty_info
    cursor.execute("""
        SELECT ewi.asset_id, ia.product_name, ewi.extended_warranty_end_date as alert_date, 'Extended Warranty End (Seperate)' as alert_type
        FROM extended_warranty_info ewi
        JOIN vayu_asset_management.it_assets ia ON ewi.asset_id = ia.asset_id
        WHERE ewi.extended_warranty_end_date IS NOT NULL 
        AND ewi.extended_warranty_end_date BETWEEN %s AND %s
    """, (today, end_date))
    warranty_alerts.extend(cursor.fetchall())

    # Deduplicate to get only the latest warranty-related date per asset
    latest_warranty_alerts = {}
    for alert in warranty_alerts:
        asset_id = alert['asset_id']
        if asset_id not in latest_warranty_alerts or alert['alert_date'] > latest_warranty_alerts[asset_id]['alert_date']:
            latest_warranty_alerts[asset_id] = alert

    # Final list of alerts
    filtered_alerts = []

# Now apply filter based on selected alert_type
    for alert in latest_warranty_alerts.values():
        normalized_alert_type = alert['alert_type'].replace(' ', '_').lower()
        if alert_type == 'all' or normalized_alert_type == alert_type:
            filtered_alerts.append(alert)

    # Add insurance alerts (unfiltered by deduplication)
    if alert_type in ['all', 'insurance_end']:
        cursor.execute("""
            SELECT id.asset_id, ia.product_name, id.insurance_end as alert_date, 'Insurance End' as alert_type
            FROM insurance_details id
            JOIN vayu_asset_management.it_assets ia ON id.asset_id = ia.asset_id
            WHERE id.insurance_end IS NOT NULL 
            AND id.insurance_end BETWEEN %s AND %s
        """, (today, end_date))
        filtered_alerts.extend(cursor.fetchall())

    # Add next service alerts
    if alert_type in ['all', 'next_service_date']:
        cursor.execute("""
            SELECT sd.asset_id, ia.product_name, sd.next_service_date as alert_date, 'Next Service' as alert_type
            FROM service_details sd
            JOIN vayu_asset_management.it_assets ia ON sd.asset_id = ia.asset_id
            WHERE sd.next_service_date IS NOT NULL 
            AND sd.next_service_date BETWEEN %s AND %s
        """, (today, end_date))
        filtered_alerts.extend(cursor.fetchall())

    cursor.close()
    conn.close()

    # Sort by alert date
    filtered_alerts.sort(key=lambda x: x['alert_date'])

    return render_template('upcoming_alerts.html',
                           alerts=filtered_alerts,
                           alert_type=alert_type,
                           date_range=date_range,
                           today=today,
                           permissions=page_perms['permissions'],
                           role=page_perms['role'],
                           header_permissions=header_perms['permissions']
                           )





@app.route('/it_dashboard', methods=['POST', 'GET'])
@login_required
def it_dashboard():

    
    conn = get_db_connection()
    cursor = conn.cursor()


    # Main query for assets
    query = """
        WITH latest_assignments AS (
            SELECT asset_id, 
                effective_date, 
                end_date AS latest_end_date, 
                confirmation_status,
                ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY created_at DESC) AS rn
            FROM vayu_asset_management.assets_users
            WHERE archieved = 'No'
        )
        SELECT ia.asset_id, 
            ia.product_type, 
            au.effective_date, 
            au.latest_end_date, 
            au.confirmation_status
        FROM vayu_asset_management.it_assets ia
        LEFT JOIN latest_assignments au ON ia.asset_id = au.asset_id AND au.rn = 1
        WHERE ia.archieved = 'No';

    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # Initialize Counters
    total_assets = 0
    assigned_assets = 0
    un_assigned_assets = 0
    unauthorized_assets = 0

    # Process Rows
    for row in rows:
        total_assets += 1
        effective_date = row[2]  # effective_date
        end_date = row[3]       # end_date
        confirmation_status = int(row[4]) if row[4] is not None else None

        if effective_date is None and end_date is None:
            un_assigned_assets += 1
        elif effective_date and end_date is None and confirmation_status == 1:
            assigned_assets += 1
        elif effective_date and end_date is None and confirmation_status is None:
            unauthorized_assets += 1
        else:
            un_assigned_assets += 1



    # Fetch raised tickets
    cursor.execute("""
        SELECT rt.asset_id, rt.ticket_status, ia.asset_id
        FROM vayu_asset_management.raised_tickets rt
        JOIN vayu_asset_management.it_assets ia ON ia.asset_id = rt.asset_id;
    """)
    tickets_rows = cursor.fetchall()

    total_raised_tickets = 0
    completed_tickets = 0
    uncompleted_tickets = 0
    completed_assigned = 0
    completed_unassigned = 0
    completed_unauthorized = 0

    for row in tickets_rows:
        total_raised_tickets += 1
        if row[1] == "completed":
            completed_tickets += 1
            # Determine asset status for completed tickets
            asset_id = row[0]
            cursor.execute("""
                SELECT au.effective_date, au.end_date, au.confirmation_status
                FROM vayu_asset_management.assets_users au
                WHERE au.asset_id = %s
                AND au.effective_date = (
                    SELECT MAX(effective_date)
                    FROM vayu_asset_management.assets_users
                    WHERE asset_id = %s
                );
            """, (asset_id, asset_id))
            asset_row = cursor.fetchone()
            if asset_row:
                effective_date = asset_row[0]
                end_date = asset_row[1]
                confirmation_status = int(asset_row[2]) if asset_row[2] is not None else None

                if effective_date and end_date is None and confirmation_status == 1:
                    completed_assigned += 1
                elif effective_date and end_date is None and confirmation_status is None:
                    completed_unauthorized += 1
                else:
                    completed_unassigned += 1

    uncompleted_tickets = total_raised_tickets - completed_tickets

    # Dashboard Data
    dashboard_data = {
        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "unassigned_assets": un_assigned_assets,
        "unauthorized_assets": unauthorized_assets,
        "total_raised_tickets": total_raised_tickets,
        "completed_tickets": completed_tickets,
        "uncompleted_tickets": uncompleted_tickets,
        "completed_assigned": completed_assigned,
        "completed_unassigned": completed_unassigned,
        "completed_unauthorized": completed_unauthorized
    }

    # Chart Data Query
    cursor.execute("""
        WITH latest_assets AS (
            SELECT 
                ia.asset_id,
                ia.product_type,
                au.effective_date,
                au.end_date,
                au.confirmation_status,
                ROW_NUMBER() OVER (PARTITION BY ia.asset_id ORDER BY au.effective_date DESC) AS row_num
            FROM vayu_asset_management.it_assets ia
            LEFT JOIN vayu_asset_management.assets_users au 
            ON ia.asset_id = au.asset_id
        )
        SELECT 
            la.product_type,
            COUNT(*) AS total_product_type,
            SUM(CASE 
                WHEN la.effective_date IS NULL AND la.end_date IS NULL AND la.confirmation_status = 0 THEN 1
                WHEN la.effective_date IS NULL AND la.end_date IS NULL AND la.confirmation_status = 1 THEN 1
                WHEN la.effective_date IS NOT NULL AND la.end_date IS NOT NULL AND la.confirmation_status = 1 THEN 1
                WHEN la.effective_date IS NOT NULL AND la.end_date IS NULL AND la.confirmation_status = 0 THEN 1
                WHEN la.effective_date IS NULL AND la.end_date IS NULL AND la.confirmation_status IS NULL THEN 1
                ELSE 0
            END) AS unassigned,
                   
            SUM(CASE 
                WHEN la.effective_date IS NOT NULL AND la.end_date IS NULL AND la.confirmation_status = 1 THEN 1
                ELSE 0
            END) AS assigned,
                   
            SUM(CASE 
                WHEN la.effective_date IS NOT NULL AND la.end_date IS NULL AND la.confirmation_status IS NULL THEN 1
                ELSE 0
            END) AS unauthorized
                   
        FROM latest_assets la
        WHERE la.row_num = 1
        GROUP BY la.product_type;
    """)
    chart_data = cursor.fetchall()

    chart_data_dict = [
        {"product_type": row[0], "total_product_type": row[1], "unassigned": row[2], "assigned": row[3], "unauthorized": row[4]}
        for row in chart_data
    ]

    cursor.close()
    conn.close()

    page_perms = get_permissions(session, 'it_dashboard')
    header_perms = get_permissions(session, 'header')


    return render_template('dashboard.html', 
                            dashboard_data=dashboard_data, 
                            chart_data=chart_data_dict,
        permissions=page_perms['permissions'],
        role=page_perms['role'],
        header_permissions=header_perms['permissions']
                            )


@app.route('/get_unassigned_products')
@login_required
def get_unassigned_products():
    product_type = request.args.get('product_type', 'All')
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT ia.asset_id, ia.product_type, ia.product_name, ia.serial_no, ia.make, ia.model, ia.remarks
            FROM vayu_asset_management.it_assets ia
            LEFT JOIN vayu_asset_management.assets_users au 
            ON ia.asset_id = au.asset_id
            AND au.effective_date = (
                SELECT MAX(effective_date)
                FROM vayu_asset_management.assets_users
                WHERE asset_id = ia.asset_id
            )
            WHERE (au.effective_date IS NULL AND au.end_date IS NULL AND (au.confirmation_status = 0 OR au.confirmation_status = 1 OR au.confirmation_status IS NULL))
               OR (au.effective_date IS NOT NULL AND au.end_date IS NOT NULL AND au.confirmation_status = 1)
               OR (au.effective_date IS NOT NULL AND au.end_date IS NULL AND au.confirmation_status = 0)
        """
        if product_type != 'All':
            query += " AND ia.product_type = %s"
            cursor.execute(query, (product_type,))
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        unassigned_products = [
            {
                "asset_id": row[0],
                "product_type": row[1],
                "product_name": row[2],
                "serial_no": row[3],
                "make": row[4],
                "model": row[5],
                "remarks": row[6]
            } for row in rows
        ]
        return jsonify(unassigned_products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# New send_request_verification_email function
def send_request_verification_email(request_id, request_type, details, to_email='nivetha@tapmobi.in', user_email=None):
    token = str(uuid.uuid4())
    expiration_time = datetime.utcnow() + timedelta(days=2)

    # Save token and expiration to the appropriate table
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        table_name = 'product_requests' if request_type == 'product' else 'wfh_asset_requests'
        query = f"""
            UPDATE {table_name}
            SET token = %s, token_expiration = %s
            WHERE request_id = %s
        """
        cursor.execute(query, (token, expiration_time, request_id))
        conn.commit()
        cursor.close()
        conn.close()

    # Generate verification URLs
    accept_url = url_for('confirm_request', request_id=request_id, token=token, action='accept', request_type=request_type, _external=True)
    reject_url = url_for('confirm_request', request_id=request_id, token=token, action='reject', request_type=request_type, _external=True)

    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .header {{ background-color: #191970; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 20px; color: #191970; }}
            .button {{ padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 5px; }}
            .accept {{ background-color: #28a745; color: #ffffff; }}
            .reject {{ background-color: #dc3545; color: #ffffff; }}
            .footer {{ text-align: center; font-size: 12px; color: #666; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f0f0f0; color: #191970; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{'Product Request' if request_type == 'product' else 'WFH Asset Request'} Verification</h2>
            </div>
            <div class="content">
                <p>Dear Admin,</p>
                <p>A new {'product request' if request_type == 'product' else 'WFH asset request'} has been submitted. Please review and confirm:</p>
                <table>
                    <tr><th>Field</th><th>Value</th></tr>
                    <tr><td>Request ID</td><td>{request_id}</td></tr>
                    <tr><td>Username</td><td>{details['username']}</td></tr>
    """
    if request_type == 'product':
        html_body += f"""
                    <tr><td>Product Needed</td><td>{details['product_needed']}</td></tr>
                    <tr><td>Reason</td><td>{details['reason']}</td></tr>
        """
    else:
        html_body += f"""
                    <tr><td>Asset ID</td><td>{details['asset_id']}</td></tr>
                    <tr><td>Duration (Days)</td><td>{details['duration_days']}</td></tr>
                    <tr><td>Start Date</td><td>{details['start_date']}</td></tr>
                    <tr><td>End Date</td><td>{details['end_date']}</td></tr>
                    <tr><td>Reason</td><td>{details['reason']}</td></tr>
        """
    html_body += f"""
                </table>
                <p>
                    <a href="{accept_url}" class="button accept">Accept Request</a>
                    <a href="{reject_url}" class="button reject">Reject Request</a>
                </p>
                <p>This link will expire in 2 days.</p>
            </div>
            <div class="footer">
                Regards,<br>Asset Management Team
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"{'Product Request' if request_type == 'product' else 'WFH Asset Request'} Verification"
    send_email_with_cc(to_email, subject, html_body, cc_email='nivetha@tapmobi.in')

@app.route('/create_product_request', methods=['GET', 'POST'])
@login_required
def create_product_request():
    if 'IOMS_emp_id' not in session:
        print("DEBUG: User not logged in.")
        flash("Please log in to submit a product request.", "danger")
        return redirect(url_for('login'))

    user_id = session['IOMS_emp_id']
    username = session['username']
    user_email = session.get('email', 'nivetha@tapmobi.in')

    header_perms = get_permissions(session, 'header')

    if request.method == 'POST':
        product_needed = request.form.get('product_needed', '').strip()
        reason = request.form.get('reason', '').strip()
    

        if not product_needed or not reason:

            flash("All fields are required.", "create_product_request")
            return render_template('create_product_request.html')

        request_id = generate_unique_id('PR')
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    INSERT INTO product_requests (request_id, user_id, username, product_needed, reason)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (request_id, user_id, username, product_needed, reason))
                conn.commit()
                cursor.close()
                conn.close()

                # Send verification email
                details = {
                    'username': username,
                    'product_needed': product_needed,
                    'reason': reason
                }
                try:
                    send_request_verification_email(request_id, 'product', details, to_email='nivetha@tapmobi.in', user_email=user_email)
                    
                except Exception as e:
                    
                    flash("Request submitted, but failed to send verification email.", "create_product_request")
                    return redirect(url_for('create_product_request'))

                flash("Product request submitted successfully. Awaiting admin approval.", "create_product_request")
                return redirect(url_for('view_product_requests'))
            except Exception as e:
                
                flash(f"Failed to submit request due to a database error: {e}", "create_product_request")
                cursor.close()
                conn.close()
                return render_template('create_product_request.html',header_permissions=header_perms['permissions'])
        else:
            
            flash("Database connection failed while submitting request.", "create_product_request")
            return render_template('create_product_request.html',header_permissions=header_perms['permissions'])

    return render_template('create_product_request.html', header_permissions=header_perms['permissions'])

@app.route('/view_product_requests', methods=['GET'])
@login_required
def view_product_requests():
    if 'IOMS_emp_id' not in session:
        flash("Please log in to view product requests.", "view_product_requests")
        return redirect(url_for('login'))

    user_id = session['IOMS_emp_id']
    conn = get_db_connection()
    requests = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM product_requests
            WHERE user_id = %s
            and overall_archieved = 'No'
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id,))
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
       
    else:
        
        flash("Database connection failed while fetching requests.", "view_product_requests")

    header_perms = get_permissions(session, 'header')
    return render_template('view_product_requests.html', requests=requests, header_permissions=header_perms['permissions'])

@app.route('/create_wfh_request', methods=['GET', 'POST'])
@login_required
def create_wfh_request():
    if 'IOMS_emp_id' not in session:
        flash("Please log in to submit a WFH asset request.", "danger")
        return redirect(url_for('login'))

    user_id = session['IOMS_emp_id']
    username = session['username']
    user_email = session.get('email', 'nivetha@tapmobi.in')
    
    header_perms = get_permissions(session, 'header')

    # Fetch user-assigned assets
    conn = get_db_connection()
    assets = []
    if conn:
        cursor = conn.cursor()
        query = """
            SELECT ia.asset_id, ia.product_name, ia.product_type
            FROM vayu_asset_management.it_assets ia
            LEFT JOIN vayu_asset_management.assets_users au 
            ON ia.asset_id = au.asset_id
            AND au.effective_date = (
                SELECT MAX(effective_date)
                FROM vayu_asset_management.assets_users
                WHERE asset_id = ia.asset_id
            
            AND archieved = 'No'
            AND overall_archieved = 'No')
            WHERE (ia.archieved != 'yes' OR ia.archieved IS NULL)
            AND au.employee_code = %s
            AND au.confirmation_status = 1
            AND (au.end_date IS NULL OR au.end_date > CURRENT_DATE)
        """
        cursor.execute(query, (user_id,))
        assets = [{'asset_id': asset[0], 'product_name': asset[1], 'product_type': asset[2]} for asset in cursor.fetchall()]
        cursor.close()
        conn.close()
    else:
        
        flash("Database connection failed while fetching assets.", "create_wfh_request")

    if request.method == 'POST':
        
        asset_id = request.form.get('asset_id', '').strip()
        duration_days = request.form.get('duration_days', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        reason = request.form.get('reason', '').strip()
       

        if not all([asset_id, duration_days, start_date, end_date, reason]):
            
            flash("All fields are required.", "create_wfh_request")
            return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])

        try:
            duration_days = int(duration_days)
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            # Calculate the inclusive duration (including both start and end dates)
            calculated_duration = (end_date - start_date).days + 1
           
            if duration_days <= 0:
                
                flash("Duration must be greater than 0.", "create_wfh_request")
                return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])
            if start_date > end_date:
                flash("Start date cannot be after end date.", "create_wfh_request")
                return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])
            if calculated_duration != duration_days:
               
                flash("The duration does not match the date range. Ensure the end date aligns with the duration.", "create_wfh_request")
                return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])
        except ValueError as e:
            
            flash("Invalid date or duration format. Please ensure all dates and duration are valid.", "create_wfh_request")
            return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])

        if not any(asset['asset_id'] == asset_id for asset in assets):
           
            flash("Selected asset is not assigned to you.", "create_wfh_request")
            return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])

        request_id = generate_unique_id('WFH')
        
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    INSERT INTO wfh_asset_requests (request_id, user_id, username, asset_id, duration_days, start_date, end_date, reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (request_id, user_id, username, asset_id, duration_days, start_date, end_date, reason))
                conn.commit()
                cursor.close()
                conn.close()

                # Send verification email
                details = {
                    'username': username,
                    'asset_id': asset_id,
                    'duration_days': duration_days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'reason': reason
                }
                try:
                    send_request_verification_email(request_id, 'wfh_asset', details, to_email='nivetha@tapmobi.in', user_email=user_email)
                   
                except Exception as e:
                    
                    flash("Request submitted, but failed to send verification email.", "create_wfh_request")
                    return redirect(url_for('create_wfh_request'))

                flash("WFH asset request submitted successfully. Awaiting admin approval.", "create_wfh_request")
                return redirect(url_for('view_wfh_requests'))
            except Exception as e:
                
                flash(f"Failed to submit request due to a database error: {e}", "create_wfh_request")
                cursor.close()
                conn.close()
                return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])
        else:
            
            flash("Database connection failed while submitting request.", "create_wfh_request")
            return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])

    return render_template('create_wfh_request.html', assets=assets, header_permissions=header_perms['permissions'])

@app.route('/view_wfh_requests', methods=['GET'])
@login_required
def view_wfh_requests():
    if 'IOMS_emp_id' not in session:
       
        flash("Please log in to view WFH requests.", "danger")
        return redirect(url_for('login'))

    user_id = session['IOMS_emp_id']
    conn = get_db_connection()
    requests = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM wfh_asset_requests
            WHERE user_id = %s
            and overall_archieved = 'No'
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id,))
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
       
    else:
        
        flash("Database connection failed while fetching requests.", "view_wfh_requests")

    header_perms = get_permissions(session, 'header')
    return render_template('view_wfh_requests.html', requests=requests, header_permissions=header_perms['permissions'])


# Route for Confirming Requests
@app.route('/confirm_request/<request_id>/<token>/<action>/<request_type>', methods=['GET', 'POST'])
def confirm_request(request_id, token, action, request_type):
    table_name = 'product_requests' if request_type == 'product' else 'wfh_asset_requests'
    conn = get_db_connection()
    if not conn:
        return render_template('response_message.html', message="Database connection failed.")

    cursor = conn.cursor(dictionary=True)
    query = f"""
        SELECT token, token_expiration, status, u.username, u.employee_id, u.email
        FROM {table_name}
        JOIN Big_App_Login_Users.User u ON u.employee_id = {table_name}.user_id
        WHERE {table_name}.request_id = %s
    """
    cursor.execute(query, (request_id,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="Invalid request ID.")

    stored_token = result['token']
    token_expiration = result['token_expiration']
    status = result['status']
    username = result['username']
    user_id = result['employee_id']
    to_email = result['email'] if result['email'] else 'nivetha@tapmobi.in'

    if stored_token != token:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="Invalid or incorrect token.")

    current_time = datetime.utcnow()
    if current_time > token_expiration:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="This verification link has expired. Please contact IT support.")

    if status != 'pending':
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="This request has already been responded to.")

    if action == 'reject' and request.method == 'GET':
        cursor.close()
        conn.close()
        return render_template('reject_request.html', request_id=request_id, token=token, request_type=request_type)

    if request.method == 'POST' and action == 'reject':
        rejection_reason = request.form.get('rejection_reason', '')
        if not rejection_reason:
            return render_template('reject_request.html', request_id=request_id, token=token, request_type=request_type, error="Rejection reason is required.")
        status = 'rejected'
        query = f"""
            UPDATE {table_name}
            SET status = %s, rejection_reason = %s, modified_at = %s, token = NULL, token_expiration = NULL
            WHERE request_id = %s
        """
        cursor.execute(query, (status, rejection_reason, datetime.utcnow(), request_id))
        conn.commit()
    elif action == 'accept':
        status = 'accepted'
        query = f"""
            UPDATE {table_name}
            SET status = %s, modified_at = %s, token = NULL, token_expiration = NULL
            WHERE request_id = %s
        """
        cursor.execute(query, (status, datetime.utcnow(), request_id))
        conn.commit()
    else:
        cursor.close()
        conn.close()
        return render_template('response_message.html', message="Invalid action.")

    # Fetch request details for confirmation email
    query = f"""
        SELECT * FROM {table_name} WHERE request_id = %s
    """
    cursor.execute(query, (request_id,))
    request_details = cursor.fetchone()
    details = {
        'username': request_details['username'],
        'status': status,
        'rejection_reason': request_details['rejection_reason'] if status == 'rejected' else 'N/A'
    }
    if request_type == 'product':
        details.update({
            'product_needed': request_details['product_needed'],
            'reason': request_details['reason']
        })
    else:
        details.update({
            'asset_id': request_details['asset_id'],
            'duration_days': request_details['duration_days'],
            'start_date': request_details['start_date'],
            'end_date': request_details['end_date'],
            'reason': request_details['reason']
        })

    cursor.close()
    conn.close()

    # Send confirmation email
    send_confirmation_email(
        action='update',
        entity_type=f"{'product_request' if request_type == 'product' else 'wfh_asset_request'}",
        entity_id=request_id,
        details=details,
        to_email=to_email,
        cc_email=['nivetha@tapmobi.in']
    )

    return render_template('response_message.html', message=f"Thank you for your response. The {'product request' if request_type == 'product' else 'WFH asset request'} has been {status}.")

if __name__ == '__main__':
    try:
        create_database()
        create_tables()
        # app.run(debug=True, use_reloader=False, port=8005)
        app.run(host='192.168.2.48', port=8022, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Error: {e}")
