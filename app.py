from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
import qrcode

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

# @app.route('/approve/<int:request_id>')
# def approve(request_id):
#     request = Request.query.get(request_id)
#     request.approved = True
#     db.session.commit()
#     return redirect('/admin')




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

    # Compose email
    msg = EmailMessage()
    msg['Subject'] = 'Visitor Confirmation'
    msg['From'] = 'bbumbble94@gmail.com'  # Update with your email address
    msg['To'] = request.email

    # Email content
    msg.set_content('Thank you for your visit! Please show the attached qr code at the point of entry')

    # Attach QR code image
    with open(qr_code, 'rb') as file:
        qr_code_data = file.read()
    msg.add_attachment(qr_code_data, maintype='image', subtype='png')

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('bbumbble94@gmail.com', 'FindMeaMatch')  # Update with your email credentials
        smtp.send_message(msg)

def generate_qr_code(request):
    # Generate QR code data
    qr_code_data = f'Name: {request.name}\nAddress: {request.address}\nEmail: {request.email}\nPhone: {request.phone_number}\nPurpose: {request.purpose}\nVisitor ID: {request.id}'

    # Generate QR code image
    qr_code = f'qrcodes/qr_code_{request.id}.png'
    img = qrcode.make(qr_code_data)
    img.save(qr_code)

    return qr_code

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
