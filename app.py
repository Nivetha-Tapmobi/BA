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
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


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
                    under_audit VARCHAR(10) DEFAULT 'No'
                    
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
                reference_name VARCHAR(500) UNIQUE,
                warranty_type VARCHAR(255) NOT NULL,
                service_case_id VARCHAR(255),       
                technician_name VARCHAR(255) NOT NULL,
                technician_id VARCHAR(255) NOT NULL,
                work_done TEXT,
                next_service_date DATE,
                service_charge DECIMAL(10, 2),
                modified_by VARCHAR(100),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                remarks TEXT,
                archieved VARCHAR(255),
                service_bill_path VARCHAR(255),
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

                elif option_type == 'location':
                    column_name = 'location'

                elif option_type == 'product_condition':
                    column_name = 'product_condition'

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
def create_asset():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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

    print('\n\n Form State in create_asset:', form_state)  # Debug output

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection failed!", "danger")
                return redirect(url_for('create_asset'))
            
            cursor = conn.cursor()

            print(request.form)
            
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
            location = request.form['location']
            under_audit = request.form['under_audit']

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
                           product_conditions = product_conditions,
                           locations = locations,
                           vendors=vendors,
                           form_state=form_state)

@app.route('/edit_asset/<asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch dropdown options (similar to create_asset)
    # product_types, companies, asset_categories, asset_types = display_drop_down('Create_Asset').values()
    product_types, companies, asset_categories, asset_types, locations, product_conditions  = display_drop_down('Create_Asset').values()
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
            location = request.form['location']

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

            under_audit = request.form['under_audit']
            location = request.form['location']

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
                    recurring_alert_for_amc=%s, image_path=%s, purchase_bill_path=%s, under_audit = %s,location = %s,
                    modified_by=%s, modified_at=NOW()
                WHERE asset_id=%s
            """
            values = (
                product_type, product_name, serial_no, make, model, part_no, purchase_date, 
                vendor_name, vendor_id, company_name, asset_type, purchase_value, warranty_checked, 
                warranty_exists, warranty_start, warranty_period, warranty_end, extended_warranty_exists, 
                extended_warranty_period, extended_warranty_end, adp_production, insurance, 
                description, remarks, product_age, product_condition, asset_category, archieved, 
                has_user_details, has_amc, recurring_alert_for_amc, asset_images_str, purchase_bills_str,under_audit, location,
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
                           product_conditions = product_conditions,
                           locations = locations,
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
                'extended_warranty_info'
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


@app.route('/get_asset_details/<asset_id>', methods=['GET'])
def get_asset_details(asset_id):
    print('get')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch asset details
        cursor.execute("""
            SELECT asset_id, product_type, product_name, serial_no, make, model, part_no, 
                   description, purchase_date, vendor_name, vendor_id, company_name, 
                   asset_type, purchase_value, product_condition, adp_production, insurance, 
                   warranty_exists, warranty_start, warranty_period, warranty_end, 
                   extended_warranty_exists, extended_warranty_period, extended_warranty_end, 
                   has_amc, image_path, purchase_bill_path, created_by, created_at, 
                   modified_by, modified_at, remarks, product_age, asset_category, 
                   recurring_alert_for_amc, has_user_details, archieved
            FROM it_assets WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
        asset = cursor.fetchone()

        # Fetch asset users
        cursor.execute("""
            SELECT assignment_code, assigned_user, employee_code, effective_date, end_date 
            FROM assets_users WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
        asset_users = cursor.fetchall()

        # Fetch service details
        cursor.execute("""
            SELECT service_id, warranty_type, ticket_id, work_done, next_service_date, service_charge 
            FROM service_details WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
        service_details = cursor.fetchall()

        # Fetch raised tickets
        cursor.execute("""
            SELECT ticket_id, problem_description, ticket_status 
            FROM raised_tickets WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
        raised_tickets = cursor.fetchall()

        # Fetch extended warranty info
        cursor.execute("""
            SELECT warranty_asset_id, extended_warranty_start, extended_warranty_period, warranty_value 
            FROM extended_warranty_info WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
        extended_warranty = cursor.fetchall()

        # Fetch insurance details
        cursor.execute("""
            SELECT policy_number, insurance_value, insurance_start, insurance_period, insurance_end 
            FROM insurance_details WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
        insurance_details = cursor.fetchall()

        if not asset:
            return jsonify({'error': 'Asset not found'}), 404

        return jsonify({
            'asset': asset,
            'asset_users': asset_users,
            'service_details': service_details,
            'raised_tickets': raised_tickets,
            'extended_warranty': extended_warranty,
            'insurance_details': insurance_details
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
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
            INSERT INTO assets_users (created_by, created_at, assignment_code, asset_id, assigned_user, 
                       effective_date, remarks, email, archieved, employee_code, overall_archieved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (created_by, created_at, assignment_code, asset_id, assigned_user, effective_date, remarks, 
              email, archieved, employee_code, 'No'))
        

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


# Route to view raised tickets
@app.route('/view_raised_tickets', methods=['GET'])
@app.route('/view_raised_tickets/<asset_id>', methods=['GET'])
def view_raised_tickets(asset_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if asset_id:
        # Fetch tickets for the specific asset, excluding archived
        cursor.execute("""
            SELECT created_by, ticket_id, raised_by, problem_description, 
                   ticket_status, ignore_reason, asset_id
            FROM raised_tickets 
            WHERE asset_id = %s AND archieved = 'No'
        """, (asset_id,))
    else:
        # Fetch all tickets when no asset_id is provided, excluding archived
        cursor.execute("""
            SELECT created_by, ticket_id, raised_by, problem_description, 
                   ticket_status, ignore_reason, asset_id
            FROM raised_tickets
            WHERE archieved = 'No'
        """)

    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_raised_tickets.html', 
                         tickets=tickets, 
                         asset_id=asset_id,
                         ticket_is_processed=ticket_is_processed)

# @app.route('/view_raised_tickets', methods=['GET'])
# @app.route('/view_raised_tickets/<asset_id>', methods=['GET'])
# def view_raised_tickets(asset_id=None):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     if asset_id:
#         # Fetch tickets for the specific asset
#         cursor.execute("""
#             SELECT created_by, ticket_id, raised_by, problem_description, 
#                    ticket_status, ignore_reason
#             FROM raised_tickets 
#             WHERE asset_id = %s
#         """, (asset_id,))
#     else:
#         # Fetch all tickets when no asset_id is provided
#         cursor.execute("""
#             SELECT created_by, ticket_id, raised_by, problem_description, 
#                    ticket_status, ignore_reason, asset_id
#             FROM raised_tickets
#         """)

#     tickets = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     return render_template('view_raised_tickets.html', tickets=tickets, asset_id=asset_id)

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


# Function to check if ticket is processed (ignored or in service)
def ticket_is_processed(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if ticket has an ignore_reason in raised_tickets
    cursor.execute("""
        SELECT ignore_reason 
        FROM raised_tickets 
        WHERE ticket_id = %s
    """, (ticket_id,))
    ticket = cursor.fetchone()
    
    has_ignore_reason = ticket and ticket['ignore_reason'] is not None
    
    # Check if ticket exists in service_details
    cursor.execute("""
        SELECT ticket_id 
        FROM service_details 
        WHERE ticket_id = %s
    """, (ticket_id,))
    service = cursor.fetchone()
    
    has_service = service is not None
    
    cursor.close()
    conn.close()
    
    # Return True if either condition is met
    return has_ignore_reason or has_service

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

    # Fetch distinct product types for the filter
    cursor.execute("""
        SELECT DISTINCT product_type 
        FROM it_assets 
        WHERE has_user_details = 0
    """)
    product_types = [row['product_type'] for row in cursor.fetchall()]

    print('product_types', product_types)

    cursor.close()
    conn.close()

    return render_template('create_replacement.html', assets=unassigned_assets, product_types=product_types)


@app.route('/create_service/<ticket_id>/<asset_id>', methods=['GET', 'POST'])
@app.route('/create_service/<ticket_id>/', methods=['GET', 'POST'])
def create_service(ticket_id, asset_id=None):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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

        # Insert into service_details table with warranty_type
        cursor.execute("""
            INSERT INTO service_details (service_id, ticket_id, asset_id, service_case_id, technician_name, technician_id, 
                                 work_done, next_service_date, service_charge, remarks, service_bill_path, 
                                 created_by, created_at, warranty_type, archieved, overall_archieved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (service_id, ticket_id, asset_id, service_case_id, technician_name, technician_id, work_done, 
              next_service_date, service_charge, remarks, service_bill_path, created_by, created_at, warranty_type, 'No', 'No'))
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
        # warranty_type = request.form['warranty_type']  # New field
        warranty_type = in_warranty_out_warranty(asset_id)
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
        cursor.execute("SELECT * FROM service_details WHERE service_id = %s AND archieved = 'No'", (service_id,))
        service = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM service_details WHERE archieved = 'No' and overall_archieved = 'No' ")
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
        SET archieved = 'Yes' 
        WHERE service_id = %s
    """, (service_id,))
    
    conn.commit()
    cursor.close()
    conn.close()

    flash("Service Deleted successfully!", "success")
    return redirect(url_for('view_service'))  # Replace with your desired redirect route

# Function to get purchase date of an asset
def get_purchase_date(asset_id):
    asset = fetch_it_assets_info(asset_id)
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
def create_insurance(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
        created_by = 'nive'
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

        cursor.close()
        conn.close()
        flash("Insurance created successfully!", "success")
        return redirect(url_for('view_insurance', insurance_id=insurance_id))

    # GET request: Fetch asset info, purchase date, and latest insurance end date
    asset = fetch_it_assets_info(asset_id)
    if not asset:
        flash("Asset not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('some_default_route'))  # Replace with your default route

    purchase_date = asset['purchase_date']
    latest_insurance_end = get_latest_insurance_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('create_insurance.html', asset_id=asset_id, product_name=asset['product_name'],
                          purchase_date=purchase_date, latest_insurance_end=latest_insurance_end)

# Route to edit an existing insurance record
@app.route('/edit_insurance/<insurance_id>', methods=['GET', 'POST'])
def edit_insurance(insurance_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
        modified_by = 'nive'
        modified_at = datetime.now()

        # Calculate insurance_end date
        insurance_start_date = datetime.strptime(insurance_start, '%Y-%m-%d').date()
        total_days = (insurance_period_years * 365) + (insurance_period_months * 30) + insurance_period_days
        insurance_end = insurance_start_date + timedelta(days=total_days)

        # Handle multiple file uploads (append to existing files)
        insurance_bill_paths = insurance['insurance_bill_path'].split(',') if insurance['insurance_bill_path'] else []
        if 'insurance_bill' in request.files:
            files = request.files.getlist('insurance_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
                    insurance_bills_folder = os.path.join(asset_folder, 'insurance_bills')
                    os.makedirs(insurance_bills_folder, exist_ok=True)
                    filename = f"{insurance_id}_{file.filename}"
                    file_path = os.path.join(insurance_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'insurance_bills', filename)
                    insurance_bill_paths.append(relative_path)
            insurance_bill_path = ','.join(insurance_bill_paths) if insurance_bill_paths else None
        else:
            insurance_bill_path = insurance['insurance_bill_path']

        # Update the insurance record
        cursor.execute("""
            UPDATE insurance_details 
            SET  policy_number = %s, insurance_value = %s, insurance_start = %s, 
                insurance_period = %s, insurance_end = %s, insurance_bill_path = %s, remarks = %s, 
                modified_by = %s, modified_at = %s
            WHERE insurance_id = %s
        """, ( policy_number, insurance_value, insurance_start,
              f"{insurance_period_years} years, {insurance_period_months} months, {insurance_period_days} days",
              insurance_end, insurance_bill_path, remarks, modified_by, modified_at, insurance_id))
        conn.commit()

        cursor.close()
        conn.close()
        flash("Insurance updated successfully!", "success")
        return redirect(url_for('view_insurance', insurance_id=insurance_id))

    # GET request: Fetch asset info, purchase date, and latest insurance end date
    asset = fetch_it_assets_info(asset_id)
    purchase_date = asset['purchase_date'] if asset else None
    latest_insurance_end = get_latest_insurance_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('edit_insurance.html', insurance=insurance, asset_id=asset_id,
                          product_name=asset['product_name'] if asset else '',
                          purchase_date=purchase_date, latest_insurance_end=latest_insurance_end)


@app.route('/view_insurance', methods=['GET'])
@app.route('/view_insurance/<id>', methods=['GET'])
def view_insurance(id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if id and id.startswith('INS'):
        # Path 3: Treat id as insurance_id
        cursor.execute("SELECT * FROM insurance_details WHERE insurance_id = %s AND archieved = 'No'", (id,))
        insurance = cursor.fetchone()
        if insurance:
            # Fetch product_name from it_assets using asset_id
            asset = fetch_it_assets_info(insurance['asset_id'])
            insurance['product_name'] = asset['product_name'] if asset else 'N/A'
        else:
            insurance = {}  # If no record is found, set to an empty dict
    elif id and id.startswith('IT'):
        # Path 2: Treat id as asset_id
        cursor.execute("SELECT * FROM insurance_details WHERE asset_id = %s AND archieved = 'No'", (id,))
        insurance = cursor.fetchall()
        # If no records are found, set insurance to an empty list
        if insurance is None:
            insurance = []
        else:
            # Fetch product_name for each insurance record
            for ins in insurance:
                asset = fetch_it_assets_info(ins['asset_id'])
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
                asset = fetch_it_assets_info(ins['asset_id'])
                ins['product_name'] = asset['product_name'] if asset else 'N/A'

    cursor.close()
    conn.close()
    return render_template('view_insurance.html', insurance=insurance)


# @app.route('/view_insurance', methods=['GET'])
# @app.route('/view_insurance/<insurance_id>', methods=['GET'])
# def view_insurance(insurance_id=None):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     if insurance_id:
#         cursor.execute("SELECT * FROM insurance_details WHERE insurance_id = %s AND archieved = 'No'", (insurance_id,))
#         insurance = cursor.fetchone()
#         if insurance:
#             # Fetch product_name from it_assets using asset_id
#             asset = fetch_it_assets_info(insurance['asset_id'])
#             insurance['product_name'] = asset['product_name'] if asset else 'N/A'
#     else:
#         cursor.execute("SELECT * FROM insurance_details WHERE archieved = 'No'")
#         insurance = cursor.fetchall()
#         # Fetch product_name for each insurance record
#         for ins in insurance:
#             asset = fetch_it_assets_info(ins['asset_id'])
#             ins['product_name'] = asset['product_name'] if asset else 'N/A'

#     cursor.close()
#     conn.close()
#     return render_template('view_insurance.html', insurance=insurance)

# Route to delete (archive) an insurance record
@app.route('/delete_insurance/<insurance_id>', methods=['POST'])
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
    flash("Insurance record archived successfully!", "success")
    return redirect(url_for('view_insurance'))

# Function to get the latest extended warranty end date for an asset
def get_latest_extended_warranty_end_date(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check the count of extended warranty records for the asset_id
    cursor.execute("""
        SELECT COUNT(*)
        FROM extended_warranty_info
        WHERE asset_id = %s AND archieved = 'No'
    """, (asset_id,))
    count = cursor.fetchone()['COUNT(*)']

    # Only fetch the latest end date if there is more than one record
    if count > 1:
        cursor.execute("""
            SELECT extended_warranty_end_date 
            FROM extended_warranty_info 
            WHERE asset_id = %s AND archieved = 'No'
            ORDER BY extended_warranty_end_date DESC
            LIMIT 1
        """, (asset_id,))
        warranty = cursor.fetchone()
        latest_end_date = warranty['extended_warranty_end_date'] if warranty else None
    else:
        latest_end_date = None

    cursor.close()
    conn.close()
    return latest_end_date


# Route to create a new extended warranty record
@app.route('/create_extended_warranty/<asset_id>', methods=['GET', 'POST'])
def create_extended_warranty(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


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
        created_by = 'nivi'
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
        conn.commit()

        cursor.close()
        conn.close()
        flash("Extended warranty created successfully!", "success")
        return redirect(url_for('view_extended_warranty', warranty_asset_id=warranty_asset_id))

    # GET request: Fetch asset info and latest extended warranty end date
    asset = fetch_it_assets_info(asset_id)


    purchase_date = asset['purchase_date']
    warranty_end = asset.get('warranty_end', None)  # Assuming warranty_end is a field in it_assets
    latest_extended_warranty_end = get_latest_extended_warranty_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('create_extended_warranty.html', asset_id=asset_id,
                          purchase_date=purchase_date, warranty_end=warranty_end,
                          latest_extended_warranty_end=latest_extended_warranty_end,
                          product_conditions=product_conditions)

# Route to edit an existing extended warranty record
@app.route('/edit_extended_warranty/<warranty_asset_id>', methods=['GET', 'POST'])
def edit_extended_warranty(warranty_asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the existing warranty record
    cursor.execute("SELECT * FROM extended_warranty_info WHERE warranty_asset_id = %s", (warranty_asset_id,))
    warranty = cursor.fetchone()

    if not warranty:
        flash("Extended warranty record not found.", "danger")
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
        modified_by = 'nivi'
        modified_at = datetime.now()

        # Calculate extended_warranty_end_date
        extended_warranty_start_date = datetime.strptime(extended_warranty_start, '%Y-%m-%d').date()
        total_days = (extended_warranty_period_years * 365) + (extended_warranty_period_months * 30) + extended_warranty_period_days
        extended_warranty_end_date = extended_warranty_start_date + timedelta(days=total_days)

        # Handle multiple file uploads (append to existing files)
        extended_warranty_bill_paths = warranty['extended_warranty_bill_path'].split(',') if warranty['extended_warranty_bill_path'] else []
        if 'extended_warranty_bill' in request.files:
            files = request.files.getlist('extended_warranty_bill')
            for file in files:
                if file and allowed_file(file.filename):
                    asset_folder = os.path.join(app.config['UPLOAD_FOLDER'], asset_id)
                    warranty_bills_folder = os.path.join(asset_folder, 'extended_warranty_bills')
                    os.makedirs(warranty_bills_folder, exist_ok=True)
                    filename = f"{warranty_asset_id}_{file.filename}"
                    file_path = os.path.join(warranty_bills_folder, filename)
                    file.save(file_path)
                    relative_path = os.path.join(asset_id, 'extended_warranty_bills', filename)
                    extended_warranty_bill_paths.append(relative_path)
            extended_warranty_bill_path = ','.join(extended_warranty_bill_paths) if extended_warranty_bill_paths else None
        else:
            extended_warranty_bill_path = warranty['extended_warranty_bill_path']

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
        conn.commit()

        cursor.close()
        conn.close()
        flash("Extended warranty updated successfully!", "success")
        return redirect(url_for('view_extended_warranty', warranty_asset_id=warranty_asset_id))

    # GET request: Fetch asset info and latest extended warranty end date
    asset = fetch_it_assets_info(asset_id)
    purchase_date = asset['purchase_date'] if asset else None
    warranty_end = asset.get('warranty_end', None) if asset else None
    latest_extended_warranty_end = get_latest_extended_warranty_end_date(asset_id)

    cursor.close()
    conn.close()
    return render_template('edit_extended_warranty.html', warranty=warranty, asset_id=asset_id,
                          purchase_date=purchase_date, warranty_end=warranty_end,
                          latest_extended_warranty_end=latest_extended_warranty_end)


@app.route('/view_extended_warranty', methods=['GET'])
@app.route('/view_extended_warranty/<asset_id>', methods=['GET'])  # Updated path for asset_id
@app.route('/view_extended_warranty/warranty/<warranty_asset_id>', methods=['GET'])
def view_extended_warranty(asset_id=None, warranty_asset_id=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if warranty_asset_id:
        # Path 3: Fetch a single record by warranty_asset_id
        cursor.execute("SELECT * FROM extended_warranty_info WHERE warranty_asset_id = %s AND archieved = 'No'", (warranty_asset_id,))
        warranty = cursor.fetchone()
        if warranty:
            # Fetch product_name from it_assets using asset_id
            asset = fetch_it_assets_info(warranty['asset_id'])
            warranty['product_name'] = asset['product_name'] if asset else 'N/A'
        else:
            warranty = {}  # If no record is found, set to an empty dict
    elif asset_id:
        # Path 2: Fetch all records for the given asset_id
        cursor.execute("SELECT * FROM extended_warranty_info WHERE asset_id = %s AND archieved = 'No'", (asset_id,))
        warranty = cursor.fetchall()
        # If no records are found, set warranty to an empty list
        if warranty is None:
            warranty = []
        else:
            # Fetch product_name for each warranty record
            for w in warranty:
                asset = fetch_it_assets_info(w['asset_id'])
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
                asset = fetch_it_assets_info(w['asset_id'])
                w['product_name'] = asset['product_name'] if asset else 'N/A'

    cursor.close()
    conn.close()
    return render_template('view_extended_warranty.html', warranty=warranty)



# Route to delete (archive) an extended warranty record
@app.route('/delete_extended_warranty/<warranty_asset_id>', methods=['POST'])
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
    flash("Extended warranty record archived successfully!", "success")
    return redirect(url_for('view_extended_warranty'))


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


@app.route('/check_asset_status', methods=['GET', 'POST'])
def check_asset_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
        """, (new_condition, last_status_check, next_status_check, frequency, audit_remarks, 'admin', asset_id))
        conn.commit()
        flash('Asset status updated successfully!', 'success')

    # Get filter parameters
    selected_employee = request.args.get('employee', '')
    search_query = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of assets per page

    # Build the query for counting total assets (for pagination)
    count_query = """
        SELECT COUNT(*) as total
        FROM it_assets ia
        LEFT JOIN assets_users au ON ia.asset_id = au.asset_id AND au.archieved = 'No'
        WHERE ia.archieved = 'No' AND ia.under_audit = 'Yes'
    """
    count_params = []

    # Build the main query
    query = """
        SELECT ia.*, au.assigned_user, au.employee_code, au.effective_date
        FROM it_assets ia
        LEFT JOIN assets_users au ON ia.asset_id = au.asset_id AND au.archieved = 'No'
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
        search_query=search_query
    )


def retrieve_asset_data(search_query='', product_type='', location='', page=1, per_page=10):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Build the query for counting total assets (for pagination)
    count_query = """
        SELECT COUNT(*) as total
        FROM it_assets
        WHERE archieved = 'No' and overall_archieved = 'No'
    """
    count_params = []

    # Build the main query
    query = """
        SELECT *
        FROM it_assets
        WHERE archieved = 'No' and overall_archieved = 'No'
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

def in_warranty_out_warranty(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    current_date = datetime.now().date()

    # Fetch warranty details from it_assets
    cursor.execute("""
        SELECT warranty_end, extended_warranty_end
        FROM it_assets
        WHERE asset_id = %s
    """, (asset_id,))
    asset = cursor.fetchone()

    in_warranty = False
    if asset:
        # Check warranty_end
        if asset['warranty_end'] and asset['warranty_end'] >= current_date:
            in_warranty = True
        # Check extended_warranty_end in it_assets
        if asset['extended_warranty_end'] and asset['extended_warranty_end'] >= current_date:
            in_warranty = True

    # Check extended_warranty_info table
    cursor.execute("""
        SELECT extended_warranty_end_date
        FROM extended_warranty_info
        WHERE asset_id = %s
    """, (asset_id,))
    ext_warranty = cursor.fetchone()

    if ext_warranty and ext_warranty['extended_warranty_end_date'] and ext_warranty['extended_warranty_end_date'] >= current_date:
        in_warranty = True

    cursor.close()
    conn.close()
    return 'in_warranty' if in_warranty else 'out_warranty'

@app.route('/all_assets', methods=['GET', 'POST'])
def all_assets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
    cursor.execute("SELECT DISTINCT product_type FROM it_assets WHERE archieved = 'No'and overall_archieved = 'No'")
    product_types = [row['product_type'] for row in cursor.fetchall()]

    # Fetch unique locations for the filter dropdown
    cursor.execute("SELECT DISTINCT location FROM it_assets WHERE archieved = 'No'and overall_archieved = 'No'")
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
        total_pages=total_pages
    )


@app.route('/create_multiple_services', methods=['GET', 'POST'])
def create_multiple_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the selected asset_ids from the query parameter
    asset_ids = request.args.get('asset_ids', '')
    if not asset_ids:
        flash('No assets selected.', 'danger')
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

        technician_name = request.form['technician_name']
        technician_id = request.form['technician_id']
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
        for asset_id, service_id in zip(selected_asset_ids, service_ids):
            created_by = 'service'
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            warranty_type = in_warranty_out_warranty(asset_id)  # Dynamically determine warranty status

            cursor.execute("""
                INSERT INTO service_details (service_id, ticket_id, asset_id, service_case_id, technician_name, technician_id, 
                                     work_done, next_service_date, service_charge, remarks, service_bill_path, 
                                     created_by, created_at, warranty_type, reference_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (service_id, ticket_id, asset_id, service_case_id, technician_name, technician_id, work_done, 
                  next_service_date, service_charge, remarks, service_bill_path, created_by, created_at, warranty_type, reference_name))
            created_service_ids.append(service_id)
        conn.commit()

        cursor.close()
        conn.close()
        flash(f"Multiple services created successfully with ticket ID {ticket_id}!", "success")
        return redirect(url_for('create_multiple_services', ticket_id=ticket_id, service_ids=','.join(created_service_ids)))

    # GET request: Fetch technicians for dropdown
    technicians_data = display_drop_down('Create_Technician')
    technicians = technicians_data['technicians']

    cursor.close()
    conn.close()
    return render_template('create_multiple_services.html', asset_ids=selected_asset_ids, technicians=technicians)

@app.route('/edit_related_multiple_services', methods=['GET', 'POST'])
def edit_related_multiple_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
            flash(f"No services found for Ticket ID {ticket_id}.", 'danger')
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
            total_pages=total_pages
        )

    cursor.close()
    conn.close()
    return render_template('enter_ticket_id.html', ticket_ids=ticket_ids)

@app.route('/edit_related_multiple_services_form/<ticket_id>', methods=['GET', 'POST'])
def edit_related_multiple_services_form(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        selected_services = request.form.get('selected_services', '').split(',')
        if not selected_services or selected_services == ['']:
            flash('No services selected for editing.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))

        # Construct the query with dynamic IN clause
        in_placeholders = ','.join(['%s'] * len(selected_services))
        query = """
            SELECT service_id, asset_id, work_done, technician_name, technician_id, next_service_date,
                   service_charge, remarks, service_case_id, service_bill_path
            FROM service_details
            WHERE ticket_id = %s AND service_id IN ({})
        """.format(in_placeholders)
        
        # Combine ticket_id with selected_services for parameters
        params = (ticket_id,) + tuple(selected_services)
        cursor.execute(query, params)
        services = cursor.fetchall()

        if not services:
            flash(f"No services found for Ticket ID {ticket_id} with selected IDs.", 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))

        technician_name = request.form['technician_name']
        technician_id = request.form['technician_id']
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
            service_bill_path = ','.join(service_bill_paths) if service_bill_paths else None
        else:
            cursor.execute("SELECT service_bill_path FROM service_details WHERE ticket_id = %s LIMIT 1", (ticket_id,))
            existing = cursor.fetchone()
            service_bill_path = existing['service_bill_path'] if existing else None

        # Update selected services
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for service in services:
            existing_work_done = service['work_done'] or ''
            if new_work_done:
                updated_work_done = f"{existing_work_done}, [{current_timestamp}] {new_work_done}" if existing_work_done else f"[{current_timestamp}] {new_work_done}"
            else:
                updated_work_done = existing_work_done

            cursor.execute("""
                UPDATE service_details
                SET technician_name = %s, technician_id = %s, work_done = %s, next_service_date = %s,
                    service_charge = %s, remarks = %s, service_case_id = %s, service_bill_path = %s,
                    modified_at = NOW()
                WHERE service_id = %s
            """, (technician_name, technician_id, updated_work_done, next_service_date, service_charge, remarks,
                  service_case_id, service_bill_path, service['service_id']))

        conn.commit()
        cursor.close()
        conn.close()
        flash(f"Selected services for Ticket ID {ticket_id} updated successfully!", "success")
        return redirect(url_for('all_assets'))

    # GET request: Fetch selected services for display
    selected_services = request.args.get('selected_services', '').split(',')
    if not selected_services or selected_services == ['']:
        flash('Please select services to edit.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('edit_related_multiple_services', ticket_id=ticket_id))

    # Construct the query with dynamic IN clause
    in_placeholders = ','.join(['%s'] * len(selected_services))
    query = """
        SELECT service_id, asset_id, technician_name, technician_id, work_done, next_service_date,
               service_charge, remarks, service_case_id, service_bill_path
        FROM service_details
        WHERE ticket_id = %s AND service_id IN ({})
    """.format(in_placeholders)
    
    # Combine ticket_id with selected_services for parameters
    params = (ticket_id,) + tuple(selected_services)
    cursor.execute(query, params)
    services = cursor.fetchall()

    if not services:
        flash(f"No services found for Ticket ID {ticket_id} with selected IDs.", 'danger')
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

    # Prepare work_done_display
    work_done_display = []
    for work_done, asset_ids in work_done_groups.items():
        if len(asset_ids) == len(services):  # All selected assets have the same work_done
            work_done_display.append({'label': 'For all selected assets', 'work_done': work_done})
        else:
            work_done_display.append({'label': f"Asset IDs: {', '.join(map(str, asset_ids))}", 'work_done': work_done})

    # Prepare data for template
    asset_ids = [service['asset_id'] for service in services]
    service = services[0]  # Use first service for pre-filling shared fields

    technicians_data = display_drop_down('Create_Technician')  # Assuming this function exists
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
        work_done_display=work_done_display  # Pass the grouped work_done history
    )



# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = 'nivetha@tapmobi.in'  # Update this
SMTP_PASSWORD = "Tapmobi@07"  # Update this
to_mail ='nivetha@tapmobi.in'

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
    print('entering function')
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
    print('warranty_alerts',warranty_alerts)

    for alert in warranty_alerts:
        subject = f"Warranty Alert: {alert['product_name']}"
        body = f"""
        Dear User,

        Your asset warranty is nearing its end:
        Asset ID: {alert['asset_id']}
        Product: {alert['product_name']}
        Warranty End Date: {alert['warranty_end']}
        Days Remaining: {(alert['warranty_end'] - today).days}

        Regards,
        Asset Management Team
        """
        send_email(to_mail, subject, body)  # Update recipient email

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
        body = f"""
        Dear User,

        Your asset extended warranty is nearing its end:
        Asset ID: {alert['asset_id']}
        Product: {alert['product_name']}
        Extended Warranty End Date: {alert['extended_warranty_end']}
        Days Remaining: {(alert['extended_warranty_end'] - today).days}

        Regards,
        Asset Management Team
        """
        send_email(to_mail, subject, body)

    # 3. Insurance Alerts (1 year before)
    insurance_threshold = today + timedelta(days=365)
    cursor.execute("""
        SELECT asset_id, insurance_end 
        FROM insurance_details 
        WHERE insurance_end IS NOT NULL 
        AND insurance_end <= %s 
        AND insurance_end >= %s
    """, (insurance_threshold, today))
    insurance_alerts = cursor.fetchall()

    for alert in insurance_alerts:
        subject = f"Insurance Alert for Asset {alert['asset_id']}"
        body = f"""
        Dear User,

        Your asset insurance is nearing its renewal date:
        Asset ID: {alert['asset_id']}
        Insurance End Date: {alert['insurance_end']}
        Days Remaining: {(alert['insurance_end'] - today).days}

        Regards,
        Asset Management Team
        """
        send_email(to_mail, subject, body)

    # 4. Service Alerts (15 days before)
    service_threshold = today + timedelta(days=15)
    cursor.execute("""
        SELECT asset_id, next_service_date 
        FROM service_details 
        WHERE next_service_date IS NOT NULL 
        AND next_service_date <= %s 
        AND next_service_date >= %s
    """, (service_threshold, today))
    service_alerts = cursor.fetchall()

    for alert in service_alerts:
        subject = f"Service Alert for Asset {alert['asset_id']}"
        body = f"""
        Dear User,

        Your asset is due for service:
        Asset ID: {alert['asset_id']}
        Next Service Date: {alert['next_service_date']}
        Days Remaining: {(alert['next_service_date'] - today).days}

        Regards,
        Asset Management Team
        """
        send_email(to_mail, subject, body)

    # 5. AMC Recurring Alerts
    cursor.execute("""
        SELECT asset_id, purchase_date, recurring_alert_for_amc 
        FROM it_assets 
        WHERE recurring_alert_for_amc IS NOT NULL
    """)
    amc_assets = cursor.fetchall()

    for asset in amc_assets:
        alerts = eval(asset['recurring_alert_for_amc'])  # Convert string to list
        # purchase_date = datetime.strptime(asset['purchase_date'], '%Y-%m-%d').date()
        if isinstance(asset['purchase_date'], str):
            purchase_date = datetime.strptime(asset['purchase_date'], '%Y-%m-%d').date()
        else:
            purchase_date = asset['purchase_date']
        
        for event_name, value, unit in alerts:
            value = int(value)
            if unit.lower() == 'days':
                interval = timedelta(days=value)
            elif unit.lower() == 'months':
                interval = timedelta(days=value * 30)  # Approximation
            elif unit.lower() == 'years':
                interval = timedelta(days=value * 365)

            days_since_purchase = (today - purchase_date).days
            if days_since_purchase % interval.days == 0 and days_since_purchase > 0:
                subject = f"AMC Alert: {event_name} for {asset['asset_id']}"
                body = f"""
                Dear User,

                Recurring AMC alert:
                Asset ID: {asset['asset_id']}
                Event: {event_name}
                Recurrence: Every {value} {unit}
                Purchase Date: {purchase_date}

                Regards,
                Asset Management Team
                """
                send_email(to_mail, subject, body)

    cursor.close()
    conn.close()



scheduler = BackgroundScheduler()
start_now = datetime.now()
print("start_now =", start_now)
scheduler.add_job(lambda: check_and_send_alerts(get_db_connection), 'interval', days=1)
# scheduler.add_job(lambda: check_and_send_alerts(get_db_connection), 'interval', minutes=1)
scheduler.start()


@app.route('/upcoming_alerts', methods=['GET', 'POST'])
def upcoming_alerts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    alert_type = request.args.get('alert_type', 'all')
    date_range = request.args.get('date_range', 30, type=int)
    
    # today = datetime.now().date()
    today = date.today()  
    end_date = today + timedelta(days=date_range)
    
    alerts = []
    
    if alert_type in ['all', 'warranty_end']:
        cursor.execute("""
            SELECT asset_id, product_name, warranty_end as alert_date, 'Warranty End' as alert_type
            FROM it_assets 
            WHERE warranty_end IS NOT NULL 
            AND warranty_end BETWEEN %s AND %s
        """, (today, end_date))
        alerts.extend(cursor.fetchall())
    
    if alert_type in ['all', 'extended_warranty_end']:
        cursor.execute("""
            SELECT asset_id, product_name, extended_warranty_end as alert_date, 'Extended Warranty End' as alert_type
            FROM it_assets 
            WHERE extended_warranty_end IS NOT NULL 
            AND extended_warranty_end BETWEEN %s AND %s
        """, (today, end_date))
        alerts.extend(cursor.fetchall())
    
    if alert_type in ['all', 'insurance_end']:
        cursor.execute("""
            SELECT asset_id, insurance_end as alert_date, 'Insurance End' as alert_type
            FROM insurance_details 
            WHERE insurance_end IS NOT NULL 
            AND insurance_end BETWEEN %s AND %s
        """, (today, end_date))
        alerts.extend(cursor.fetchall())
    
    if alert_type in ['all', 'next_service_date']:
        cursor.execute("""
            SELECT asset_id, next_service_date as alert_date, 'Next Service' as alert_type
            FROM service_details 
            WHERE next_service_date IS NOT NULL 
            AND next_service_date BETWEEN %s AND %s
        """, (today, end_date))
        alerts.extend(cursor.fetchall())
    
    cursor.close()
    conn.close()
    
    alerts.sort(key=lambda x: x['alert_date'])
    
    return render_template('upcoming_alerts.html', 
                         alerts=alerts,
                         alert_type=alert_type,
                         date_range=date_range,
                         today=today)


if __name__ == '__main__':
    
    create_database()
    create_tables()
    app.run(debug=True, use_reloader=False, port=5000)
