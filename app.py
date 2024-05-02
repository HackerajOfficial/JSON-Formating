from flask import Flask, render_template, request, redirect, jsonify, url_for
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from datetime import datetime
import cx_Oracle


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///json.db"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Specify the upload folder
# db = SQLAlchemy(app)
# migrate = Migrate(app,db)

# Database configuration
DB_USER = 'test1'
DB_PASSWORD = 'aa'
DB_DSN = 'RAAZ'  # This is the Oracle Database Service Name or DS

# Database connection
def get_db_connection():
    try:
        connection = cx_Oracle.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN
        )
        return connection
    except cx_Oracle.DatabaseError as e:
        print("Database connection error:", e)
        return None

# Route to test database connection
@app.route('/dmc')
def test_db_connection():
    connection = get_db_connection()
    if connection:
        return 'Database connection successful!'
    else:
        return 'Failed to connect to the database.'


current_date_YYMMDD = datetime.now().strftime('%Y-%m-%d')


@app.route('/')
def hello():
    return render_template('index.html') 

# @app.route('/form-submit', methods=['post'])
# def simpleformsubmition():
#     name = request.form['name']
#     print(name)
#     # Return a response
#     return jsonify({'message': 'Form data received successfully'})

# @app.route('/formSubmit', methods=['post'])
@app.route('/form-submit', methods=['post'])
def formsubmitionusingjavascript():
    data = request.json
    print(data)
    print(data)
    return jsonify({'data': data})

@app.route('/lid/create', methods=['get','post'])
def formsubmitionusingjavascriptforlid():
    if request.method == 'GET':
        return render_template('lidinmultipleproduct.html')
        
    elif request.method == 'POST':
        db = get_db_connection()
        data = request.json
        print(data)
        print("=================================================")

        # Fetch username
        username = data['username']
        print("Username:", username)

        user_id = 1

        # Fetch max_lid_id
        query_max_lid_id = """
            SELECT COALESCE(MAX(lid_id+1), 1) AS max_lid_id FROM LID
        """
        cursor = db.cursor()
        try:
            cursor.execute(query_max_lid_id)
            max_lid_id = cursor.fetchone()[0]
        finally:
            cursor.close()

        # Insert LID record
        lid_status = "True"
        lid_name = data['lid_name']
        print(f"===================={lid_name}====================")
        
        query_insert_lid = """
            INSERT INTO LID (lid_id, lid_name, lid_date, lid_status, user_id) 
            VALUES (:max_lid_id, :lid_name, TO_DATE(:current_date_YYMMDD, 'YYYY-MM-DD'), :lid_status, :user_id)
        """
        cursor = db.cursor()
        try:
            cursor.execute(query_insert_lid, max_lid_id=max_lid_id, lid_name=lid_name, current_date_YYMMDD=current_date_YYMMDD, lid_status=lid_status, user_id=user_id)
            db.commit()
        finally:
            cursor.close()
        
        # # Fetch data list
        data_list = data['data']
        print("Data:")
        cursor = db.cursor()
        try:
            query_insert_product = """
            INSERT INTO Product (product_id, product_name, product_price) 
            VALUES (:product_id, :product_name, :product_price)
            """
            query_insert_lid_product = """
                INSERT INTO LID_PRODUCT(LID_ID, PRODUCT_ID)
                VALUES (:LID_ID, :PRODUCT_ID)
            """
            for item in data_list:
                query_max_product_id = """
                SELECT COALESCE(MAX(product_id+1), 1) AS max_product_id FROM product
                 """
                cursor.execute(query_max_product_id)
                max_product_id = cursor.fetchone()[0]

                cursor.execute(query_insert_product, product_id=max_product_id, product_name=item['name'], product_price=item['price'])
                cursor.execute(query_insert_lid_product, LID_ID=max_lid_id, PRODUCT_ID=max_product_id)
                
                db.commit()

            
        finally:
            cursor.close()
        
        # return jsonify({'data': data})
        return redirect(url_for('liddetails'))

        
@app.route('/lid/')
def liddetails():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT lid_id, lid_name, lid_date FROM LID ORDER BY LID_ID DESC")
    lid_records = cursor.fetchall()
    print(lid_records)
    cursor.close()
    return render_template('lidlist.html', lid_records=lid_records)

@app.route('/lid/cart')
def lid_product():
    db = get_db_connection()
    # Get the product ID from the request parameters
    lid_id = request.args.get('lid_id')
    # Fetch cart details associated with the product ID
    query_for_lid_respect_products="""
        SELECT p.product_id, p.product_name, p.product_price
        FROM Product p
        JOIN lid_product lp ON p.product_id = lp.product_id
        WHERE lp.lid_id = :lid_id
    """
    # Execute the query and fetch the results
    cursor = db.cursor()
    try:
        cursor.execute(query_for_lid_respect_products, lid_id=lid_id)
        lid_products = cursor.fetchall()
    finally:
        cursor.close()
    print(lid_products)
    # Convert the results to JSON and return them
    return jsonify({'lid_products': lid_products})

if __name__ == "__main__":
    app.run(debug=True, port=7229)