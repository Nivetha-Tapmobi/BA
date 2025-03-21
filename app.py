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
import ast
from jinja2 import Environment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SESSION_TYPE'] = 'filesystem'  # Optional: Use filesystem for session storage
app.config['SESSION_PERMANENT'] = False  # Session lasts only for the browser session
app.config['SESSION_USE_SIGNER'] = True  # Sign session cookies for security

# Optional: If using filesystem session storage
from flask_session import Session
Session(app)

# Customize Jinja2 environment to include zip
def jinja2_zip(*args):
    return zip(*args)

app.jinja_env.globals['zip'] = jinja2_zip


# db_config = {
#     'host': 'localhost',
#     'user': 'yt',
#     'password': 'yt',
#     'database': 'asset_management',
#      'port': 3306  # Added port explicitly
# }

# db_config = {
#     'user': 'nivetha',
#     'password': 'Nivetha@07',
#     'host': '127.0.0.1',
#     'port': 3306,
#     'database': 'asset_management'
# }

db_config = {
    'user': 'nivetha',
    'password': 'Nivetha@07',
    'host': '127.0.0.1',
    'port': 3306,
    'database': 't1'
}


UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}

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
                    recurring_alert_for_amc VARCHAR(255)
                    
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
                    token VARCHAR(255),
                    token_expiration DATETIME,
                    archieved VARCHAR(255) 
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
                warranty_type VARCHAR(255) NOT NULL,
                service_case_id VARCHAR(255) UNIQUE,       
                technician_name VARCHAR(255) NOT NULL,
                technician_id VARCHAR(255) NOT NULL,
                work_done TEXT,
                next_service_date DATE,
                service_charge DECIMAL(10, 2),
                modified_by VARCHAR(100),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                remarks TEXT,
                archieved VARCHAR(255),
                service_bill_path VARCHAR(255)
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
                    serial_number VARCHAR(255) NOT NULL,     
                    product_name VARCHAR(255) NOT NULL,
                    purchase_date DATE,  
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
                    asset_category VARCHAR(255) NOT NULL,
                    archieved VARCHAR(255)
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
                    archieved VARCHAR(255)
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
                    serial_number VARCHAR(255) NOT NULL,     
                    product_name VARCHAR(255) NOT NULL,
                    policy_number VARCHAR(255) UNIQUE NOT NULL,
                    insurance_value DECIMAL(10, 2),
                    insurance_start DATE,
                    insurance_period VARCHAR(255),
                    insurance_end DATE,
                    modified_by VARCHAR(255), 
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    remarks TEXT,
                    asset_category VARCHAR(255) NOT NULL,
                    archieved VARCHAR(255)
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

def generate_unique_id( prefix):
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
        
    order_column = 'created_at'

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name} ORDER BY {order_column} DESC LIMIT 1")
    last_record = cursor.fetchone()
    
    current_date = datetime.now().strftime("%Y%m%d")

    if last_record is None:
        new_id = f"{prefix}{current_date}-01"  # Start from 01 if no records exist
    else:
        last_unique_key = last_record[3]  # Assuming unique key is at index 3
        last_number = int(last_unique_key[-2:])  # Extract last 2 digits
        new_id = f"{prefix}{current_date}-{last_number + 1:02d}"  # Increment and format

    cursor.close()
    conn.close()
    
    return new_id

# Email configuration (adjust as per your SMTP settings)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""

def send_email(to_email, username, asset_id, table_name, action):
    # Determine the subject and body content based on table_name
    if 'add_user' in table_name.lower():
        subject = f"New Asset Assignment Notification - {action}"
        body_content = f"Your asset has been assigned to you"

    elif 'edit_user' in table_name.lower():
        subject = f"Asset Assignment Update Notification - {action}"
        body_content = f"Your asset assignment has been updated"

    elif 'raise_ticket' in table_name.lower():
        subject = f"New Ticket Raised "

    body = f"""
    Dear {username},

    {body_content}:
    Asset ID: {asset_id}
    Date: {request.form['effective_date']}

    Remarks: {request.form.get('remarks', 'None')}

    Regards,
    Asset Management Team
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

def raise_ticket_send_email(to_email, raised_by, asset_id, ticket_id, problem_description):
    subject = f"New Ticket Raised - {ticket_id}"
    body = f"""
    Dear Admin,

    A new ticket has been raised:

    Ticket ID: {ticket_id}
    Asset ID: {asset_id}
    Raised By: {raised_by}
    Problem Description: {problem_description}
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    Please take appropriate action.

    Regards,
    Asset Management Team
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

@app.route('/')
def home():
    return redirect(url_for('view_assets')) 

@app.route('/add_new_option', methods=['POST'])
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

                else:
                    return jsonify({'error': 'Invalid option type'}), 400
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(f"INSERT INTO dropdown_attributes ({column_name}) VALUES (%s)", (new_option,))
                conn.commit()
                cursor.close()
                return jsonify({'message': f'New {option_type} added successfully'}), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Invalid request'}), 400

def display_drop_down(page):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if page == 'Create_Asset':
        cursor.execute("""
            SELECT DISTINCT product_type, company_name, asset_category, asset_type 
            FROM dropdown_attributes
        """)

        product_types, companies, asset_categories, asset_types = set(), set(), set(), set()
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

        result = {
            "product_types": list(product_types),
            "companies": list(companies),
            "asset_categories": list(asset_categories),
            "asset_types": list(asset_types)
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

    # Close the cursor & connection AFTER fetching the data
    cursor.close()
    conn.close()

    return result

@app.route('/create_asset', methods=['GET', 'POST'])
def create_asset():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    dropdown_data = display_drop_down('Create_Asset')
    product_types, companies, asset_categories, asset_types = dropdown_data.values()
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

    print('\n\n Form State in create_asset:', form_state)  # Debug output

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection failed!", "danger")
                return redirect(url_for('create_asset'))
            
            cursor = conn.cursor()
            
            created_by = 't1'
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

            # Validate vendor_id
            if not vendor_id:
                flash("Vendor ID is required!", "danger")
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
                    asset_category, archieved, has_user_details, has_amc, recurring_alert_for_amc, image_path, purchase_bill_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                created_by, created_at, asset_id, product_type, product_name, serial_no, make, model, part_no, 
                purchase_date, vendor_name, vendor_id, company_name, asset_type, purchase_value, 
                warranty_checked, warranty_exists, warranty_start, warranty_period, warranty_end,
                extended_warranty_exists, extended_warranty_period, extended_warranty_end,
                adp_production, insurance, description, remarks, product_age, product_condition,
                asset_category, archieved, has_user_details, has_amc, recurring_alert_for_amc,
                asset_images_str, purchase_bills_str
            )

            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()

            if 'form_state' in session:
                session.pop('form_state')

            flash("Asset successfully created!", "success")
            return redirect(url_for('create_asset'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('create_asset'))

    return render_template('create_asset.html', 
                           product_types=product_types, 
                           companies=companies,
                           asset_categories=asset_categories,
                           asset_types=asset_types,
                           vendors=vendors,
                           form_state=form_state)

@app.route('/edit_asset/<asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch dropdown options (similar to create_asset)
    product_types, companies, asset_categories, asset_types = display_drop_down('Create_Asset').values()
    vendors_data = display_drop_down('Create_Vendor')
    vendors = vendors_data['vendors']  # Flat list of vendors
    if request.method == 'POST':
        try:
            # Update asset details based on form submission
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

            asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
            asset_images_folder = os.path.join(asset_folder, 'Asset_Images')
            purchase_bills_folder = os.path.join(asset_folder, 'Purchase_Bills')

            os.makedirs(asset_images_folder, exist_ok=True)
            os.makedirs(purchase_bills_folder, exist_ok=True)

            # Fetch existing file paths
            cursor.execute("SELECT image_path, purchase_bill_path FROM it_assets WHERE asset_id = %s", (asset_id,))
            existing_data = cursor.fetchone()
            existing_images = existing_data['image_path'].split(',') if existing_data['image_path'] else []
            existing_bills = existing_data['purchase_bill_path'].split(',') if existing_data['purchase_bill_path'] else []

            # Handle Asset Image Uploads
            asset_images = existing_images
            if 'asset_image[]' in request.files:
                files = request.files.getlist('asset_image[]')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(asset_images_folder, filename)
                        file.save(filepath)
                        if filename not in asset_images:
                            asset_images.append(filename)

            # Handle Purchase Bill Uploads
            purchase_bills = existing_bills
            if 'purchase_bill[]' in request.files:
                files = request.files.getlist('purchase_bill[]')
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(purchase_bills_folder, filename)
                        file.save(filepath)
                        if filename not in purchase_bills:
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

            # Handling recurring alert
            recurring_alert_keys = request.form.getlist('recurring_alert_key[]')
            recurring_alert_values = request.form.getlist('recurring_alert_value[]')
            recurring_alert_units = request.form.getlist('recurring_alert_unit[]')
            recurring_alert_for_amc = str(list(zip(recurring_alert_keys, recurring_alert_values, recurring_alert_units)))

            update_query = """
                UPDATE it_assets SET 
                    product_type=%s, product_name=%s, serial_no=%s, make=%s, model=%s, part_no=%s, 
                    purchase_date=%s, vendor_name=%s, vendor_id=%s, company_name=%s, asset_type=%s, 
                    purchase_value=%s, warranty_checked=%s, warranty_exists=%s, warranty_start=%s, 
                    warranty_period=%s, warranty_end=%s, extended_warranty_exists=%s, 
                    extended_warranty_period=%s, extended_warranty_end=%s, adp_production=%s, 
                    insurance=%s, description=%s, remarks=%s, product_age=%s, product_condition=%s, 
                    asset_category=%s, archieved=%s, has_user_details=%s, has_amc=%s, 
                    recurring_alert_for_amc=%s, image_path=%s, purchase_bill_path=%s, 
                    modified_by=%s, modified_at=NOW()
                WHERE asset_id=%s
            """
            values = (
                product_type, product_name, serial_no, make, model, part_no, purchase_date, 
                vendor_name, vendor_id, company_name, asset_type, purchase_value, warranty_checked, 
                warranty_exists, warranty_start, warranty_period, warranty_end, extended_warranty_exists, 
                extended_warranty_period, extended_warranty_end, adp_production, insurance, 
                description, remarks, product_age, product_condition, asset_category, archieved, 
                has_user_details, has_amc, recurring_alert_for_amc, asset_images_str, purchase_bills_str,
                "current_user", asset_id  # Replace "current_user" with actual user tracking logic
            )

            cursor.execute(update_query, values)
            conn.commit()
            flash("Asset successfully updated!", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('view_assets'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            cursor.close()
            conn.close()

    # GET request: Fetch asset details
    cursor.execute("SELECT * FROM it_assets WHERE asset_id = %s", (asset_id,))
    asset = cursor.fetchone()

    print('actual amc', asset['has_amc'])
    # asset['has_amc'] = 'Yes' if asset['has_amc'] in (1, True) else 'No'
    asset['has_amc'] = 'Yes' if str(asset['has_amc']) in ('1', 'True', 1, True) else 'No'

    print('Asset has_amc normalized:', asset['has_amc'])  # Debug

    # Check if coming from create_vendor to clear vendor selection
    from_create_vendor = request.referrer and 'create_vendor' in request.referrer
    if from_create_vendor:
        asset['vendor_name'] = None
        asset['vendor_id'] = None
        print('Returning from create_vendor, cleared vendor_name and vendor_id')

    # If form_state exists, ensure it doesn’t override cleared values
    form_state = session.get('form_state', {}) if request.referrer and 'create_vendor' in request.referrer else {}
    if from_create_vendor and 'form_state' in session:
        form_state['vendor_name'] = ['']
        form_state['vendor_id'] = ['']
        session['form_state'] = form_state

    if not asset:
        flash('Asset not found!', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('view_assets'))

    cursor.close()
    conn.close()

    # Parse warranty_period and extended_warranty_period if they exist
    warranty_period_dict = json.loads(asset['warranty_period']) if asset['warranty_period'] else {"years": 0, "months": 0, "days": 0}
    extended_warranty_period_dict = json.loads(asset['extended_warranty_period']) if asset['extended_warranty_period'] else {"years": 0, "months": 0, "days": 0}
    recurring_alert_list = ast.literal_eval(asset['recurring_alert_for_amc']) if asset['recurring_alert_for_amc'] else []
    return render_template('edit_asset.html', 
                           asset=asset, 
                           product_types=product_types, 
                           companies=companies,
                           asset_categories=asset_categories,
                           asset_types=asset_types,
                           vendors=vendors,
                           warranty_period_dict=warranty_period_dict,
                           extended_warranty_period_dict=extended_warranty_period_dict,
                           recurring_alert_list=recurring_alert_list,
                           form_state=form_state)

@app.route('/view_assets', methods=['GET'])
def view_assets():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Select all columns instead of just a few
    query = """
        SELECT id, created_by, created_at, asset_id, product_type, product_name, 
               serial_no, make, model, part_no, purchase_date, vendor_name, 
               vendor_id, company_name, asset_type, purchase_value, image_path,
               purchase_bill_path, warranty_checked, warranty_exists, 
               warranty_start, warranty_period, warranty_end, 
               extended_warranty_exists, extended_warranty_period, 
               extended_warranty_end, adp_production, insurance, description,
               remarks, product_age, product_condition, modified_by, 
               modified_at, has_user_details, asset_category, archieved,
               has_amc, recurring_alert_for_amc
        FROM it_assets 
        WHERE archieved != 'yes' OR archieved IS NULL
    """
    cursor.execute(query)
    all_assets = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convert the tuple results to a list of dictionaries for easier handling
    columns = [desc[0] for desc in cursor.description]
    assets_list = [dict(zip(columns, asset)) for asset in all_assets]

    today = date.today()

    return render_template('view_assets.html', all_assets=assets_list, today=today)

@app.route('/delete_asset/<string:id>', methods=['POST'])
def delete_asset(id):
    data = request.get_json()  # Get JSON data from the request body
    table_name = data.get('table')  # Extract table name from request body

    if table_name == 'it_assets':
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the `archived` column to 'yes' instead of deleting
        cursor.execute("UPDATE it_assets SET archieved = 'yes' WHERE asset_id = %s", (id,))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": "Asset Deleted successfully"}), 200
    else:
        return jsonify({"error": "Invalid table name"}), 400

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

# Route for creating a new user asset assignment
@app.route('/create_user_asset/<asset_id>', methods=['GET', 'POST'])
def create_user_asset(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch purchase_date and latest end_date for the asset
    purchase_date = get_purchase_date(asset_id)
    if not purchase_date:
        flash("Asset not found or purchase date not available.", "danger")
        return redirect(url_for('view_user_details', asset_id=asset_id))

    latest_end_date, is_disabled = get_latest_end_date(asset_id)

    if request.method == 'POST':
        assignment_code = generate_unique_id('AU')
        created_by = 't1'
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
            flash(f"Effective date cannot be earlier than the purchase date ({purchase_date}).", "danger")
            return redirect(url_for('create_user_asset', asset_id=asset_id))
        if latest_end_date and effective_date < latest_end_date:
            flash(f"Effective date cannot be earlier than the latest end date ({latest_end_date}).", "danger")
            return redirect(url_for('create_user_asset', asset_id=asset_id))

        cursor.execute("""
            SELECT email FROM big_app_login_users.users 
            WHERE employee_id = %s
        """, (employee_code,))
        user = cursor.fetchone()
        email = user['email']

        # Insert into assets_users table
        cursor.execute("""
            INSERT INTO assets_users (created_by, created_at, assignment_code, asset_id, assigned_user, effective_date, remarks, email, archieved, employee_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (created_by, created_at, assignment_code, asset_id, assigned_user, effective_date, remarks, email, archieved, employee_code))
        

        cursor.execute("""
            UPDATE it_assets 
            SET has_user_details = 1 
            WHERE asset_id = %s
        """, (asset_id,))

        conn.commit()

        # # Send email with table name 'add_user'
        # if user and email:
        #     send_email(email, assigned_user, asset_id, "add_user", "Created")

        cursor.close()
        conn.close()
        return redirect(url_for('view_user_details', asset_id=asset_id))

    # GET request: fetch employees
    cursor.execute("""
        SELECT id, username, employee_id, email, phone, designation 
        FROM big_app_login_users.users
    """)
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('create_user_asset.html', 
                           employees=employees, 
                           asset_id=asset_id, 
                           purchase_date=purchase_date, 
                           latest_end_date=latest_end_date,
                        #    row_count=row_count,
                           is_disabled=is_disabled)

# Route for editing an existing user asset assignment
@app.route('/edit_user_asset/<assignment_code>', methods=['GET', 'POST'])
def edit_user_asset(assignment_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch asset_id and purchase_date
    cursor.execute("""
        SELECT asset_id, effective_date, end_date 
        FROM assets_users 
        WHERE assignment_code = %s
    """, (assignment_code,))
    assignment = cursor.fetchone()
    if not assignment:
        flash("Assignment not found.", "danger")
        return redirect(url_for('view_user_details', asset_id=asset_id))

    asset_id = assignment['asset_id']
    purchase_date = get_purchase_date(asset_id)
    if not purchase_date:
        flash("Asset not found or purchase date not available.", "danger")
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
            flash(f"Effective date cannot be earlier than the purchase date ({purchase_date}).", "danger")
            return redirect(url_for('edit_user_asset', assignment_code=assignment_code))
        if end_date and effective_date > end_date:
            flash("Effective date cannot be later than the end date.", "danger")
            return redirect(url_for('edit_user_asset', assignment_code=assignment_code))

        # Update assets_users table
        cursor.execute("""
            UPDATE assets_users 
            SET assigned_user = %s, effective_date = %s, end_date = %s, remarks = %s, employee_code=%s
            WHERE assignment_code = %s
        """, (assigned_user, effective_date, end_date, remarks, employee_code, assignment_code))

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


        conn.commit()

        # Fetch user's email
        cursor.execute("""
            SELECT email FROM big_app_login_users.users 
            WHERE employee_id = %s
        """, (employee_code,))
        user = cursor.fetchone()

        # # Send email with table name 'edit_user'
        # if user and user['email']:
        #     send_email(user['email'], assigned_user, assignment_code, "edit_user", "Updated")

        cursor.close()
        conn.close()
        return redirect(url_for('view_user_details', asset_id=asset_id))

    # GET request: fetch employees and last user data
    cursor.execute("""
        SELECT id, username, employee_id, email, phone, designation 
        FROM big_app_login_users.users
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
    return render_template('edit_user_asset.html', employees=employees, assignment_code=assignment_code, last_user=last_user, purchase_date=purchase_date)

# Route for viewing user details
@app.route('/view_user_details/<asset_id>', methods=['GET'])
def view_user_details(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch minimal data for the table
    cursor.execute("""
        SELECT assignment_code, assigned_user, email, effective_date, end_date, remarks
        FROM assets_users WHERE asset_id = %s
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
    return render_template('view_user_details.html', assignments=assignments, full_details=full_details, asset_id=asset_id, latest_assignment_code=latest_assignment_code, latest_end_date=latest_end_date)

@app.route('/delete_user_asset/<assignment_code>', methods=['POST'])
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
def create_vendor():
    print('Form State in create_vendor:', session.get('form_state', {}))
    if request.method == 'POST':
        vendor_id = generate_unique_id('VD')
        vendor_name = request.form.get('vendor_name')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        remarks = request.form.get('remarks')
        created_by = "admin"
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

    return render_template('create_vendor.html')

# @app.route('/save_form_state', methods=['POST'])
# def save_form_state():
#     form_data = request.form.to_dict(flat=False)
#     print('\n\n Form Data:', form_data)
#     session['form_state'] = form_data
    
#     # Store the referrer to determine return destination
#     referrer = request.referrer
#     if referrer:
#         if 'edit_asset' in referrer:
#             session['return_to'] = 'edit_asset'
#             session['asset_id'] = referrer.split('/')[-1]  # Extract asset_id from URL
#         elif 'create_asset' in referrer:
#             session['return_to'] = 'create_asset'
#     print('\n\n Session after setting:', session)
#     return redirect(url_for('create_vendor'))

# Function to fetch asset details from it_assets table
def fetch_it_assets_info(asset_id):
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

# Route to handle both rendering the form and ticket creation
@app.route('/create_raise_ticket/<asset_id>', methods=['GET', 'POST'])
def create_raise_ticket(asset_id):
    # Fetch asset details
    asset = fetch_it_assets_info(asset_id)

    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for('view_assets'))  # Redirect to view_assets if asset not found

    # Assuming user_name is fetched from session or similar mechanism
    user_name = None  # Replace with actual user session data if available

    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()

        created_by = 't1'
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ticket_id = generate_unique_id('RT')
        raised_by = request.form['raised_by']
        problem_description = request.form['problem_description']
        remarks = request.form.get('remarks', '')
        ticket_status = 'Open'  # Default status
        archieved = 'No'  # Default value
        

        cursor.execute("""
            INSERT INTO raised_tickets (
                created_by, created_at, ticket_id, asset_id, raised_by, 
                problem_description, ticket_status, remarks, archieved
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (created_by, created_at, ticket_id, asset_id, raised_by, 
              problem_description, ticket_status, remarks, archieved))
        conn.commit()

        # Fetch admin email for notification
        # admin_email = "nivetha@tapmobi.in"

        # Send email notification to admin
        # raise_ticket_send_email(admin_email, raised_by, asset_id, ticket_id, problem_description)

        flash("Ticket raised successfully!", "success")
        cursor.close()
        conn.close()
        return redirect(url_for('view_assets'))

    # GET request: render the form
    return render_template('create_raise_ticket.html', 
                           asset_id=asset['asset_id'], 
                           product_name=asset['product_name'], 
                           serial_no=asset['serial_no'], 
                           user_name=user_name)

@app.route('/view_raised_tickets', methods=['GET'])
@app.route('/view_raised_tickets/<asset_id>', methods=['GET'])
def view_raised_tickets(asset_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if asset_id:
        # Fetch tickets for the specific asset
        cursor.execute("""
            SELECT created_by, ticket_id, raised_by, problem_description, 
                   ticket_status, ignore_reason
            FROM raised_tickets 
            WHERE asset_id = %s
        """, (asset_id,))
    else:
        # Fetch all tickets when no asset_id is provided
        cursor.execute("""
            SELECT created_by, ticket_id, raised_by, problem_description, 
                   ticket_status, ignore_reason, asset_id
            FROM raised_tickets
        """)

    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_raised_tickets.html', tickets=tickets, asset_id=asset_id)

# Route to fetch ticket details for the view popup
@app.route('/ticket_details/<ticket_id>', methods=['GET'])
def ticket_details(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, created_by, created_at, ticket_id, asset_id, raised_by, 
               problem_description, modified_by, modified_at, ticket_status, 
               ignore_reason, progress_notes, replacement_issued, 
               replacement_asset_id, replacement_reason, remarks, archieved
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

# Route to handle ignoring a ticket
@app.route('/ignore_ticket/<ticket_id>', methods=['POST'])
def ignore_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    ignore_reason = request.form['ignore_reason']
    modified_by = 't1'  # Replace with actual user if available
    modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        UPDATE raised_tickets 
        SET ignore_reason = %s, ticket_status = 'Closed', 
            modified_by = %s, modified_at = %s
        WHERE ticket_id = %s
    """, (ignore_reason, modified_by, modified_at, ticket_id))
    conn.commit()

    # Fetch asset_id for redirect
    cursor.execute("SELECT asset_id FROM raised_tickets WHERE ticket_id = %s", (ticket_id,))
    result = cursor.fetchone()
    if result:
        asset_id = result[0]  # If result is a tuple, use index 0
    else:
        asset_id = None

    cursor.close()
    conn.close()

    # Get referrer and prevent infinite redirect loop
    referrer = request.referrer
    if referrer and "ignore_ticket" not in referrer and "delete_ticket" not in referrer:
        return redirect(referrer)  # Redirect to the same page only if it’s not looping

    flash("Ticket ignored successfully!", "success")
    return redirect(url_for('view_raised_tickets', asset_id=asset_id))

@app.route('/delete_ticket/<ticket_id>', methods=['POST'])
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
def fetch_unassigned_assets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch unassigned assets where has_user_details = 0
    cursor.execute("""
        SELECT * 
        FROM it_assets 
        WHERE has_user_details = 0
    """)
    unassigned_assets = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('create_replacement.html', assets=unassigned_assets)


@app.route('/create_service/<ticket_id>/<asset_id>', methods=['GET', 'POST'])
@app.route('/create_service/<ticket_id>/', methods=['GET', 'POST'])
def create_service(ticket_id, asset_id=None):

    print(f"Request path: {request.path}")
    print(f"Entered create_service route with ticket_id={ticket_id}, asset_id={asset_id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    print(f"Entered create_service route with ticket_id={ticket_id}, asset_id={asset_id}")

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

    print(f"Final asset_id: {asset_id}")

    if request.method == 'POST':
        service_id = generate_unique_id('SI')
        created_by = 'service'
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        technician_name = request.form['technician_name']
        technician_id = request.form['technician_id']
        work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)
        warranty_type = request.form['warranty_type']  # New field

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

        # Insert into service_details table with warranty_type
        cursor.execute("""
            INSERT INTO service_details (service_id, ticket_id, asset_id, service_case_id, technician_name, technician_id, 
                                 work_done, next_service_date, service_charge, remarks, service_bill_path, 
                                 created_by, created_at, warranty_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (service_id, ticket_id, asset_id, service_case_id, technician_name, technician_id, work_done, 
              next_service_date, service_charge, remarks, service_bill_path, created_by, created_at, warranty_type))
        conn.commit()

        cursor.close()
        conn.close()
        flash("Service created successfully!", "success")
        return redirect(url_for('view_service', service_id=service_id))

    # GET request: Fetch technicians for dropdown
    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('create_service.html', ticket_id=ticket_id, asset_id=asset_id, technicians=technicians)

@app.route('/edit_service/<service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


        # Fetch asset_id and purchase_date
    cursor.execute("""
        SELECT asset_id from service_details
        WHERE service_id = %s
    """, (service_id,))
    services = cursor.fetchone()

    asset_id = services['asset_id']

    if request.method == 'POST':
        technician_name = request.form['technician_name']
        technician_id = request.form['technician_id']
        work_done = request.form['work_done']
        next_service_date = request.form['next_service_date'] or None
        service_charge = request.form['service_charge'] or None
        remarks = request.form.get('remarks', '')
        service_case_id = request.form.get('service_case_id', None)
        warranty_type = request.form['warranty_type']  # New field
        modified_by = 'service'
        modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Handle multiple file uploads
        cursor.execute("SELECT service_bill_path FROM service_details WHERE service_id = %s", (service_id,))
        existing_service = cursor.fetchone()
        existing_paths = existing_service['service_bill_path'].split(',') if existing_service['service_bill_path'] else []

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
                    existing_paths.append(relative_path)
        service_bill_path = ','.join(existing_paths) if existing_paths else None

        # Update services table with warranty_type
        cursor.execute("""
            UPDATE service_details 
            SET technician_name = %s, technician_id = %s, work_done = %s, next_service_date = %s, 
                service_charge = %s, remarks = %s, service_case_id = %s, service_bill_path = %s,
                modified_by = %s, modified_at = %s, warranty_type = %s
            WHERE service_id = %s
        """, (technician_name, technician_id, work_done, next_service_date, service_charge, remarks, 
              service_case_id, service_bill_path, modified_by, modified_at, warranty_type, service_id))
        conn.commit()

        cursor.close()
        conn.close()
        flash("Service updated successfully!", "success")
        return redirect(url_for('view_service', service_id=service_id))

    # GET request: Fetch service details and technicians
    cursor.execute("SELECT * FROM service_details WHERE service_id = %s", (service_id,))
    service = cursor.fetchone()

    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('edit_service.html', service=service, technicians=technicians)


@app.route('/view_service', methods=['GET'])
@app.route('/view_service/<service_id>', methods=['GET'])
def view_service(service_id=None):  # Added default value for clarity
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if service_id:
        cursor.execute("SELECT * FROM service_details WHERE service_id = %s", (service_id,))
        service = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM service_details")
        service = cursor.fetchall()
        

    cursor.close()
    conn.close()
    return render_template('view_service.html', service=service)


# Route to delete a service
@app.route('/delete_service/<service_id>', methods=['POST'])
def delete_service(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the 'archieved' column instead of deleting
    cursor.execute("""
        UPDATE service_details 
        SET archieved = 'yes' 
        WHERE service_id = %s
    """, (service_id,))
    
    conn.commit()
    cursor.close()
    conn.close()

    flash("Service Deleted successfully!", "success")
    return redirect(url_for('view_service'))  # Replace with your desired redirect route



@app.route('/create_technician', methods=['GET', 'POST'])
def create_technician():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        technician_name = request.form['technician_name']
        technician_type = request.form['technician_type']
        phone_number = request.form['phone_number']
        email_address = request.form['email']
        remarks = request.form['remarks']
        address = request.form['address']
        
        created_by = 'tech1'
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        modified_by = 'tech2'
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
                flash('Technician with the same name, phone number, or email already exists.', 'danger')
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
            flash('Technician added successfully!', 'success')

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

            # Fallback redirect
            cursor.close()
            conn.close()
            return redirect(url_for('create_service', ticket_id='default', asset_id='default'))

        except Exception as e:
            conn.rollback()
            flash(f'Error adding technician: {str(e)}', 'danger')
            print(f"Exception: {str(e)}")  # Debug print
            cursor.close()
            conn.close()
            return render_template('create_technician.html')

    cursor.close()
    conn.close()
    return render_template('create_technician.html')

# # Modified save_form_state to handle create_technician
@app.route('/save_form_state', methods=['POST'])
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
def save_form_state_technician():
    try:
        print("Received request to /save_form_state_technician")
        form_data = request.form.to_dict(flat=False)
        print("Form data:", form_data)
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
            else:
                session['return_to'] = 'create_service'  # Default fallback
        else:
            session['return_to'] = 'create_service'  # Default if no referrer

        print("Session after update:", session)
        return redirect(url_for('create_technician'))
    except Exception as e:
        print(f"Error in save_form_state_technician: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    
    create_database()
    create_tables()
    app.run(debug=True, use_reloader=False, port=5000)
