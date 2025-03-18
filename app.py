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



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Set session timeout


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
                    amc VARCHAR(255),
                    archieved VARCHAR(255)
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
    return redirect(url_for('create_asset')) 

@app.route('/create_asset', methods=['GET', 'POST'])
def create_asset():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch dropdown data
    cursor.execute("""
        SELECT DISTINCT product_type, company_name, asset_category, asset_type FROM drop_down_attributes
    """)

    product_types, companies, asset_categories, asset_types = set(), set(), set(), set()

    dropdown =  cursor.fetchall()


    for row in dropdown:
        if row['product_type']:
            product_types.add(row['product_type'])
        if row['company_name']:
            companies.add(row['company_name'])
        if row['asset_category']:
            asset_categories.add(row['asset_category'])
        if row['asset_type']:
            asset_types.add(row['asset_type'])

    cursor.close()
    conn.close()

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            if conn is None:
                flash("Database connection failed!", "danger")
                return redirect(url_for('create_asset'))
                
            cursor = conn.cursor()

            asset_id = generate_unique_id('IT')
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
            warranty_checked = request.form.get('warranty_checked', 'No')
            warranty_exists = request.form.get('warranty_exists', 'No')
            warranty_start = request.form['warranty_start']
            warranty_period = request.form['warranty_period']
            warranty_end = request.form['warranty_end']
            extended_warranty_exists = request.form.get('extended_warranty_exists', 'No')
            extended_warranty_period = request.form['extended_warranty_period']
            extended_warranty_end = request.form['extended_warranty_end']
            adp_production = request.form['adp_production']
            insurance = request.form['insurance']
            description = request.form['description']
            remarks = request.form['remarks']
            product_age = request.form['product_age']
            product_condition = request.form['product_condition']
            asset_category = request.form['asset_category']
            amc = request.form['amc']
            archieved = request.form.get('archieved', 'No')
            has_user_details = request.form.get('has_user_details', False)

            created_by = 't1'

            query = """
                INSERT INTO it_assets (
                    created_by, asset_id, product_type, product_name, serial_no, make, model, part_no, 
                    purchase_date, vendor_name, vendor_id, company_name, asset_type, purchase_value, 
                    warranty_checked, warranty_exists, warranty_start, warranty_period, warranty_end,
                    extended_warranty_exists, extended_warranty_period, extended_warranty_end,
                    adp_production, insurance, description, remarks, product_age, product_condition,
                    asset_category, amc, archieved, has_user_details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
               created_by , asset_id, product_type, product_name, serial_no, make, model, part_no, 
                purchase_date, vendor_name, vendor_id, company_name, asset_type, purchase_value, 
                warranty_checked, warranty_exists, warranty_start, warranty_period, warranty_end,
                extended_warranty_exists, extended_warranty_period, extended_warranty_end,
                adp_production, insurance, description, remarks, product_age, product_condition,
                asset_category, amc, archieved, has_user_details
            )

            cursor.execute(query, values)

            conn.commit()
            cursor.close()
            conn.close()

            flash("Asset successfully created!", "success")

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

        return redirect(url_for('create_asset'))
    


    return render_template('create_asset.html', 
                           product_types=list(product_types), 
                           companies=list(companies),
                           asset_categories=list(asset_categories),
                           asset_types=list(asset_types))

if __name__ == '__main__':
    
    create_database()
    create_tables()
    app.run(debug=True, use_reloader=False, port=5000)
