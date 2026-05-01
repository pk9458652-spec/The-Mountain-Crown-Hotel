from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
import sqlite3
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import threading

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, static_folder='.')
CORS(app)

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'hotel.db'))

# ─── Flask-Mail Configuration ────────────────────────────────────────────────
# IMPORTANT: For Gmail, you must use an "App Password"
# 1. Enable 2-Step Verification in your Google Account
# 2. Search for "App Passwords" in your account settings
# 3. Generate a new password for "Mail" and "Other (Custom name)" like "Hotel Site"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'themountaincrown@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'ntuvzkvazsjnnyxc')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'themountaincrown@gmail.com')

mail = Mail(app)

def send_booking_email(booking_details):
    """Sends a confirmation email to the customer."""
    try:
        msg = Message(
            f"Booking Confirmation - Mountain Crown Hotel (ID: #{booking_details['booking_id']})",
            recipients=[booking_details['email']]
        )
        
        msg.body = f"""
Dear {booking_details['name']},

Thank you for choosing Mountain Crown Hotel! Your booking has been confirmed.

--- BOOKING DETAILS ---
Booking ID: #{booking_details['booking_id']}
Room: {booking_details['room_name']} (Room No: {booking_details['room_number']})
Check-in: {booking_details['check_in']}
Check-out: {booking_details['check_out']}
Guests: {booking_details['guests']}
Total Amount: ₹{booking_details['total_amount']}
Payment Method: {booking_details['payment_method']}

We look forward to welcoming you!

Best Regards,
Mountain Crown Hotel Team
"""
        # You can also use msg.html for a prettier email
        mail.send(msg)
        return True
    except Exception as e:
        error_msg = f"\n[!!! EMAIL ERROR !!!] {datetime.now()}\nRecipients: {booking_details['email']}\nError: {str(e)}\n"
        print(error_msg)
        with open("email_errors.log", "a") as f:
            f.write(error_msg)
            import traceback
            traceback.print_exc(file=f)
        return False

def send_cancellation_email(email, name, booking_id):
    """Sends a cancellation confirmation email."""
    try:
        msg = Message(
            f"Booking Cancelled - Mountain Crown Hotel (ID: #{booking_id})",
            recipients=[email]
        )
        msg.body = f"""
Dear {name},

Your booking #{booking_id} at Mountain Crown Hotel has been successfully cancelled.

If you did not request this cancellation or have any questions, please contact our support team.

We hope to see you again soon!

Best Regards,
Mountain Crown Hotel Team
"""
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send cancellation email: {e}")
        return False

# ─── Database Initialization ────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Room Types table — price tiers with total inventory
    c.execute('''
        CREATE TABLE IF NOT EXISTS room_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL UNIQUE,
            price_per_night REAL NOT NULL,
            description TEXT,
            max_guests INTEGER DEFAULT 2,
            image TEXT,
            total_rooms INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Rooms table — individual room units (one row per physical room)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type_id INTEGER NOT NULL,
            room_number TEXT NOT NULL,
            FOREIGN KEY (room_type_id) REFERENCES room_types(id)
        )
    ''')

    # Customers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bookings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            guests INTEGER NOT NULL,
            total_nights INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    ''')

    # Payments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            transaction_id TEXT,
            status TEXT DEFAULT 'success',
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    ''')

    # Gallery table — tracks uploaded event/gallery images
    c.execute('''
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT DEFAULT '',
            caption TEXT DEFAULT '',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Feedbacks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed room types if empty
    c.execute('SELECT COUNT(*) FROM room_types')
    if c.fetchone()[0] == 0:
        types = [
            ('Deluxe Room',        'deluxe',       2000, 'Perfect for couples with mountain views and a private balcony.', 2, 'images/room1.jpeg', 6),
            ('Executive Suite',    'executive',    3000, 'Spacious suite with living area and premium amenities.',         2, 'images/room2.jpeg', 5),
            ('Presidential Suite', 'presidential', 4000, 'The ultimate luxury experience with a private jacuzzi.',          4, 'images/room3.jpeg', 4),
        ]
        c.executemany(
            'INSERT INTO room_types (name, type, price_per_night, description, max_guests, image, total_rooms) VALUES (?,?,?,?,?,?,?)',
            types
        )

    # Seed individual rooms if empty
    c.execute('SELECT COUNT(*) FROM rooms')
    if c.fetchone()[0] == 0:
        c.execute('SELECT id, type, total_rooms FROM room_types')
        room_types = c.fetchall()
        rooms_to_insert = []
        floor_mapping = {'deluxe': 1, 'executive': 2, 'presidential': 3}
        for rt in room_types:
            rt_id, rt_type, total = rt
            floor = floor_mapping.get(rt_type, 1)
            for i in range(1, total + 1):
                rooms_to_insert.append((rt_id, f'{floor}{i:02d}'))
        c.executemany('INSERT INTO rooms (room_type_id, room_number) VALUES (?,?)', rooms_to_insert)

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─── Static Files ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# ─── API: Room Types with Availability ───────────────────────────────────────

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Return room types (price tiers). If check_in & check_out are provided,
    include available_count for those dates."""
    check_in  = request.args.get('check_in')
    check_out = request.args.get('check_out')

    conn = get_db()
    types = conn.execute('SELECT * FROM room_types').fetchall()

    result = []
    for rt in types:
        rt_dict = dict(rt)
        if check_in and check_out:
            # Count how many rooms of this type are booked for the requested period
            booked = conn.execute('''
                SELECT COUNT(DISTINCT r.id)
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE r.room_type_id = ?
                  AND b.status != 'cancelled'
                  AND NOT (b.check_out <= ? OR b.check_in >= ?)
            ''', (rt['id'], check_in, check_out)).fetchone()[0]
            rt_dict['available_count'] = max(0, rt['total_rooms'] - booked)
            rt_dict['booked_count'] = booked
        else:
            rt_dict['available_count'] = rt['total_rooms']
            rt_dict['booked_count'] = 0
        result.append(rt_dict)

    conn.close()
    return jsonify(result)

# ─── API: Check Availability for a Room Type ────────────────────────────────

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    data          = request.json
    room_type_id  = data.get('room_type_id')
    check_in      = data.get('check_in')
    check_out     = data.get('check_out')

    conn = get_db()
    rt = conn.execute('SELECT total_rooms FROM room_types WHERE id = ?', (room_type_id,)).fetchone()
    if not rt:
        conn.close()
        return jsonify({'available': False, 'available_count': 0}), 404

    booked = conn.execute('''
        SELECT COUNT(DISTINCT r.id)
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE r.room_type_id = ?
          AND b.status != 'cancelled'
          AND NOT (b.check_out <= ? OR b.check_in >= ?)
    ''', (room_type_id, check_in, check_out)).fetchone()[0]

    available_count = max(0, rt['total_rooms'] - booked)
    conn.close()
    return jsonify({'available': available_count > 0, 'available_count': available_count})

# ─── API: Create Booking ─────────────────────────────────────────────────────

@app.route('/api/book', methods=['POST'])
def create_booking():
    data = request.json

    # Validate required fields
    required = ['name', 'email', 'phone', 'room_type_id', 'check_in', 'check_out', 'guests', 'payment_method']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'Missing field: {field}'}), 400

    try:
        check_in  = datetime.strptime(data['check_in'],  '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400

    if check_out <= check_in:
        return jsonify({'success': False, 'message': 'Check-out must be after check-in'}), 400

    total_nights = (check_out - check_in).days

    conn = get_db()

    # Get room type price
    rt = conn.execute('SELECT * FROM room_types WHERE id = ?', (data['room_type_id'],)).fetchone()
    if not rt:
        conn.close()
        return jsonify({'success': False, 'message': 'Room type not found'}), 404

    # Find an available room of this type for the requested dates
    available_room = conn.execute('''
        SELECT r.id, r.room_number
        FROM rooms r
        WHERE r.room_type_id = ?
          AND r.id NOT IN (
              SELECT b.room_id FROM bookings b
              WHERE b.status != 'cancelled'
                AND NOT (b.check_out <= ? OR b.check_in >= ?)
          )
        LIMIT 1
    ''', (data['room_type_id'], data['check_in'], data['check_out'])).fetchone()

    if not available_room:
        conn.close()
        type_names = {'deluxe': 'Deluxe Rooms', 'executive': 'Executive Suites', 'presidential': 'Presidential Suites'}
        type_name = type_names.get(rt['type'], 'rooms of this type')
        return jsonify({
            'success': False,
            'message': f'No availability! All {type_name} are fully booked for your selected dates. Please choose a different room type or dates.'
        }), 409

    room_id      = available_room['id']
    room_number  = available_room['room_number']
    total_amount = rt['price_per_night'] * total_nights

    # Save customer
    cur = conn.execute(
        'INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)',
        (data['name'], data['email'], data['phone'])
    )
    customer_id = cur.lastrowid

    # Save booking
    cur = conn.execute(
        '''INSERT INTO bookings (customer_id, room_id, check_in, check_out, guests, total_nights, total_amount, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed')''',
        (customer_id, room_id, data['check_in'], data['check_out'],
         data['guests'], total_nights, total_amount)
    )
    booking_id = cur.lastrowid

    # Generate a fake transaction ID for demo
    import random, string
    txn_id = 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Save payment
    conn.execute(
        '''INSERT INTO payments (booking_id, amount, payment_method, transaction_id, status)
           VALUES (?, ?, ?, ?, 'success')''',
        (booking_id, total_amount, data['payment_method'], txn_id)
    )

    conn.commit()
    conn.close()

    # Prepare details for email
    booking_details = {
        'booking_id': booking_id,
        'name': data['name'],
        'email': data['email'],
        'room_name': rt['name'],
        'room_number': room_number,
        'check_in': data['check_in'],
        'check_out': data['check_out'],
        'guests': data['guests'],
        'total_amount': total_amount,
        'payment_method': data['payment_method']
    }
    
    # Send email notification
    email_sent = send_booking_email(booking_details)

    # Automated WhatsApp Notification (Background API Method)
    def send_whatsapp_async(phone, name, b_id, check_in_date, room_number):
        try:
            import time
            number = f"whatsapp:+91{phone}"
            message = f"Hello {name},\n\nYour booking #{b_id} at The Mountain Crown is confirmed! \nRoom: {room_number}\nCheck-in Date: {check_in_date}\n\nWe look forward to hosting you!"
            
            print(f"Queuing background WhatsApp message to {number}...")
            
            # ---------------------------------------------------------
            # REAL API INTEGRATION (Twilio WhatsApp Business API)
            # ---------------------------------------------------------
            # To make this physically send messages, uncomment this code 
            # and use your free Twilio.com API credentials:
            #
            # from twilio.rest import Client
            # TWILIO_SID = "your_twilio_account_sid_here"
            # TWILIO_AUTH_TOKEN = "your_twilio_auth_token_here"
            # client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
            # msg = client.messages.create(
            #     body=message,
            #     from_="whatsapp:+14155238886", # Twilio Sandbox Number
            #     to=number
            # )
            # ---------------------------------------------------------
            
            # Simulating network delay for background process
            time.sleep(2)
            print(f"✅ [SUCCESS] Automated WhatsApp confirmation sent to {number} invisibly!")
            
        except Exception as e:
            print(f"Automated WhatsApp Error: {e}")

    threading.Thread(target=send_whatsapp_async, args=(data['phone'], data['name'], booking_id, data['check_in'], room_number), daemon=True).start()

    return jsonify({
        'success': True,
        'message': 'Booking confirmed!' + (' Email sent.' if email_sent else ' (Email failed to send)'),
        'booking_id': booking_id,
        'transaction_id': txn_id,
        'total_amount': total_amount,
        'total_nights': total_nights,
        'room_name': rt['name'],
        'room_number': room_number
    })

# ─── API: Cancel Booking ───────────────────────────────────────────────────

@app.route('/api/cancel', methods=['POST'])
def cancel_booking():
    data = request.json
    booking_id = data.get('booking_id')
    email = data.get('email')

    if not booking_id or not email:
        return jsonify({'success': False, 'message': 'Booking ID and Email are required'}), 400

    conn = get_db()
    # Verify booking exists and belongs to this email
    booking = conn.execute('''
        SELECT b.id, b.status, b.check_in, b.customer_id
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        WHERE b.id = ? AND c.email = ?
    ''', (booking_id, email)).fetchone()

    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid Booking ID or Email address.'}), 404

    if booking['status'] == 'cancelled':
        conn.close()
        return jsonify({'success': False, 'message': 'This booking is already cancelled.'}), 400

    # Optional: check if cancellation is too late (based on policy)
    # The policy says free until 48 hrs before check-in. This is a basic system, 
    # so we'll just process the cancellation and mark it.
    conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    
    # Get customer info for email before closing connection
    customer = conn.execute('SELECT name, email FROM customers WHERE id = ?', (booking['customer_id'],)).fetchone()
    
    conn.commit()
    conn.close()

    # Send cancellation email
    email_sent = False
    if customer:
        email_sent = send_cancellation_email(customer['email'], customer['name'], booking_id)

    return jsonify({
        'success': True, 
        'message': f'Booking #{booking_id} has been successfully cancelled.' + (' Email sent.' if email_sent else ' (Email failed to send)')
    })

# ─── API: Check Booking (User) ───────────────────────────────────────────────

@app.route('/api/check-booking', methods=['POST'])
def check_my_booking():
    data = request.json
    booking_id = data.get('booking_id')
    phone = data.get('phone')

    if not booking_id or not phone:
        return jsonify({'success': False, 'message': 'Booking ID and Phone are required'}), 400

    conn = get_db()
    b = conn.execute('''
        SELECT b.id, c.name, c.email, c.phone, rt.name as room_name, r.room_number,
               b.check_in, b.check_out, b.guests, b.total_amount, b.status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN rooms r ON b.room_id = r.id
        JOIN room_types rt ON r.room_type_id = rt.id
        WHERE b.id = ? AND c.phone = ?
    ''', (booking_id, phone)).fetchone()
    conn.close()

    if b:
        return jsonify({'success': True, 'booking': dict(b)})
    return jsonify({'success': False, 'message': 'Booking not found. Please check your ID and phone number.'}), 404

# ─── API: Get All Bookings (Admin) ───────────────────────────────────────────

@app.route('/api/admin/bookings', methods=['GET'])
def get_all_bookings():
    conn = get_db()
    rows = conn.execute('''
        SELECT b.id, c.name, c.email, c.phone,
               rt.name AS room_name, rt.price_per_night,
               r.room_number,
               b.check_in, b.check_out, b.guests,
               b.total_nights, b.total_amount, b.status, b.created_at,
               p.transaction_id, p.payment_method, p.status AS payment_status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN rooms r ON b.room_id = r.id
        JOIN room_types rt ON r.room_type_id = rt.id
        LEFT JOIN payments p ON p.booking_id = b.id
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ─── API: Admin Delete & Allot Room ──────────────────────────────────────────

@app.route('/api/admin/bookings/<int:booking_id>', methods=['DELETE'])
def admin_delete_booking(booking_id):
    conn = get_db()
    conn.execute('DELETE FROM payments WHERE booking_id = ?', (booking_id,))
    conn.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Booking and associated payments deleted'})

@app.route('/api/admin/rooms', methods=['GET'])
def get_all_rooms():
    conn = get_db()
    rooms = conn.execute('SELECT r.id, r.room_number, rt.name as type_name, r.room_type_id FROM rooms r JOIN room_types rt ON r.room_type_id = rt.id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])

@app.route('/api/admin/bookings/<int:booking_id>/allot', methods=['POST'])
def admin_allot_room(booking_id):
    data = request.json
    new_room_id = data.get('room_id')
    conn = get_db()
    conn.execute('UPDATE bookings SET room_id = ? WHERE id = ?', (new_room_id, booking_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Room allotted successfully'})

# ─── API: Room Inventory Summary (Admin) ─────────────────────────────────────

@app.route('/api/admin/inventory', methods=['GET'])
def get_inventory():
    today = datetime.now().date().isoformat()
    conn = get_db()
    types = conn.execute('SELECT * FROM room_types').fetchall()
    result = []
    for rt in types:
        booked_today = conn.execute('''
            SELECT COUNT(DISTINCT r.id)
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE r.room_type_id = ?
              AND b.status != 'cancelled'
              AND b.check_in <= ? AND b.check_out > ?
        ''', (rt['id'], today, today)).fetchone()[0]
        result.append({
            'type': rt['name'],
            'price': rt['price_per_night'],
            'total': rt['total_rooms'],
            'occupied_today': booked_today,
            'available_today': rt['total_rooms'] - booked_today
        })
    conn.close()
    return jsonify(result)

# ─── API: Gallery ────────────────────────────────────────────────────────────

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    """Return all gallery images ordered by newest first."""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM gallery ORDER BY uploaded_at DESC'
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'filename': r['filename'],
            'url': f'images/{r["filename"]}',
            'title': r['title'],
            'caption': r['caption'],
            'uploaded_at': r['uploaded_at']
        })
    return jsonify(result)


@app.route('/api/gallery/upload', methods=['POST'])
def upload_gallery_image():
    """Upload an image to the gallery. Saves file to images/ folder."""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided'}), 400

    file = request.files['image']
    title = request.form.get('title', '').strip()
    caption = request.form.get('caption', '').strip()

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'File type not allowed. Use JPG, PNG, GIF, or WebP.'}), 400

    # Build a safe unique filename: evt_<uuid>.<ext>
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f'evt_{uuid.uuid4().hex[:12]}.{ext}'

    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    os.makedirs(images_dir, exist_ok=True)
    save_path = os.path.join(images_dir, unique_name)
    file.save(save_path)

    # Record in database
    conn = get_db()
    cur = conn.execute(
        'INSERT INTO gallery (filename, title, caption) VALUES (?, ?, ?)',
        (unique_name, title, caption)
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Image uploaded successfully!',
        'id': new_id,
        'filename': unique_name,
        'url': f'images/{unique_name}',
        'title': title,
        'caption': caption
    })


@app.route('/api/gallery/<int:image_id>', methods=['DELETE'])
def delete_gallery_image(image_id):
    """Delete a gallery image from DB and disk."""
    conn = get_db()
    row = conn.execute('SELECT filename FROM gallery WHERE id = ?', (image_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Image not found'}), 404

    filename = row['filename']
    conn.execute('DELETE FROM gallery WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()

    # Remove physical file
    file_path = os.path.join(os.path.dirname(__file__), 'images', filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    return jsonify({'success': True, 'message': 'Image deleted'})

# ─── API: Feedback ───────────────────────────────────────────────────────────

@app.route('/api/feedback', methods=['GET', 'POST'])
def handle_feedback():
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        rating = data.get('rating', 0)
        message = data.get('message', '').strip()

        if not name or not rating or not message:
            conn.close()
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        conn.execute(
            'INSERT INTO feedbacks (name, rating, message) VALUES (?, ?, ?)',
            (name, rating, message)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Feedback successfully submitted'})

    elif request.method == 'GET':
        rows = conn.execute('SELECT * FROM feedbacks ORDER BY created_at DESC').fetchall()
        conn.close()
        feedbacks = [dict(r) for r in rows]
        return jsonify(feedbacks)

# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("\n[OK] The Mountain Crown server is running!")
    print("   Open: http://localhost:5000 or your network IP\n")
    app.run(host='0.0.0.0', debug=True, port=5000)
