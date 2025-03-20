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

db_config = {
    'user': 'nivetha',
    'password': 'Nivetha@07',
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'asset_management'
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


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(100),
                    created_at DATETIME,
                    assignment_code VARCHAR(255) UNIQUE NOT NULL,
                    asset_id VARCHAR(255) NOT NULL,
                    product_id VARCHAR(255) NOT NULL,
                    assigned_user VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    effective_date DATE,
			        end_date DATE,
                    modified_by VARCHAR(100),
                    modified_at DATETIME,
                    remarks TEXT,
                    confirmation_status VARCHAR(255),
                    token VARCHAR(255),
                    token_expiration DATETIME,
                    asset_category VARCHAR(255) NOT NULL ,
                    archieved VARCHAR(255) 
                )
            """)


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


            cursor.execute("""
               CREATE TABLE IF NOT EXISTS service_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                service_id VARCHAR(255) UNIQUE NOT NULL,
                service_type VARCHAR(255) NOT NULL,                  
                ticket_id VARCHAR(255) NOT NULL,
                asset_id VARCHAR(255) NOT NULL,
                product_name VARCHAR(255),
                serial_number VARCHAR(255),
                service_case_id VARCHAR(255) UNIQUE NOT NULL,       
                warranty_type VARCHAR(255) NOT NULL,
                technician_name VARCHAR(255) NOT NULL,
                technician_id VARCHAR(255) NOT NULL,
                work_done TEXT,
                next_service_date DATE,
                service_charge DECIMAL(10, 2),
                modified_by VARCHAR(100),
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                remarks TEXT,
                asset_category VARCHAR(255) NOT NULL,
                archieved VARCHAR(255)    
            )

            """)


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS technician_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    technician_type VARCHAR(255) NOT NULL,
                    technician_id VARCHAR(255) UNIQUE NOT NULL,
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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raised_tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_by VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ticket_id VARCHAR(255) UNIQUE NOT NULL,
                    asset_id VARCHAR(255) NOT NULL,     
                    serial_number VARCHAR(255) NOT NULL,     
                    product_name VARCHAR(255) NOT NULL,
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
                    asset_category VARCHAR(255) NOT NULL,
                    remarks TEXT,
                    archieved VARCHAR(255)
                )
            """)


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
                cursor.execute(f"INSERT INTO drop_down_attributes ({column_name}) VALUES (%s)", (new_option,))
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
            FROM drop_down_attributes
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

@app.route('/save_form_state', methods=['POST'])
def save_form_state():
    form_data = request.form.to_dict(flat=False)
    print('\n\n Form Data:', form_data)
    session['form_state'] = form_data
    
    # Store the referrer to determine return destination
    referrer = request.referrer
    if referrer:
        if 'edit_asset' in referrer:
            session['return_to'] = 'edit_asset'
            session['asset_id'] = referrer.split('/')[-1]  # Extract asset_id from URL
        elif 'create_asset' in referrer:
            session['return_to'] = 'create_asset'
    print('\n\n Session after setting:', session)
    return redirect(url_for('create_vendor'))


if __name__ == '__main__':
    
    create_database()
    create_tables()
    app.run(debug=True, use_reloader=False, port=5000)
