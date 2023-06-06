import requests
import os
import qrcode
from io import BytesIO
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///requests.db'
db = SQLAlchemy(app)

# Database model
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    approved = db.Column(db.Boolean, default=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Admin side - route to approve requests
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            requests = Request.query.all()
            return render_template('admin.html', requests=requests)
        else:
            return 'Invalid username or password'

    return render_template('admin_login.html')

@app.route('/approve/<int:request_id>')
def approve(request_id):
    request = Request.query.get(request_id)
    request.approved = True
    db.session.commit()

    # Send confirmation email with QR code
    send_confirmation_email(request)

    return redirect('/admin')

def send_confirmation_email(request):
    # Generate QR code
    qr_code = generate_qr_code(request)

    # Prepare the email data
    email_data = {
        "from": "Mailgun Sandbox <postmaster@sandbox1b0c786dabf84e19ba1f127ef582b3ce.mailgun.org>",
        "to": request.email,
        "subject": "Visitor Confirmation",
        "text": "Thank you for your visit! Please show the attached QR code at the point of entry",
    }

    # Attach the QR code image
    with open(qr_code, 'rb') as file:
        email_data["attachment"] = [
            ("qr_code.png", file.read())
        ]

    # Send the email using Mailgun API
    response = requests.post(
        "https://api.mailgun.net/v3/sandbox1b0c786dabf84e19ba1f127ef582b3ce.mailgun.org/messages",
        auth=("api", "bca908d844eca56eca5f837977370ca1-6d1c649a-d25e1c15"),
        files=email_data.get("attachment"),
        data=email_data
    )

    if response.status_code != 200:
        print("Failed to send email.")
    else:
        print("Email sent successfully.")

def generate_qr_code(request):
    # Generate QR code data
    qr_code_data = f'Name: {request.name}\nAddress: {request.address}\nEmail: {request.email}\nPhone: {request.phone_number}\nPurpose: {request.purpose}\nVisitor ID: {request.id}'

    # Generate QR code image
    qr_code_path = f'qrcodes/qr_code_{request.id}.png'
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill="black", back_color="white")
    qr_image.save(qr_code_path)

    return qr_code_path

# Client side - form submission
@app.route('/client', methods=['GET', 'POST'])
def client():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        email = request.form['email']
        phone_number = request.form['phone_number']
        purpose = request.form['purpose']

        new_request = Request(name=name, address=address, email=email, phone_number=phone_number, purpose=purpose)
        db.session.add(new_request)
        db.session.commit()
        return redirect('/')

    return render_template('client.html')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
