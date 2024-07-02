from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import sqlite3
import secrets
import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Allow CORS for the specified domain
CORS(app, supports_credentials=True, origins=["https://serverboi.org", "http://localhost:3000"])

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

DATABASE = 'pixels.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pixels (
                id INTEGER PRIMARY KEY,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                color TEXT NOT NULL,
                user_id INTEGER,
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

init_db()

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            return User(id=user[0], username=user[1], password=user[2])
    return None

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Pixel Map Backend is working. Use the provided endpoints to interact with the application.",
        "endpoints": {
            "register": "/register (POST)",
            "login": "/login (POST)",
            "logout": "/logout (POST)",
            "update_pixels": "/api/update_pixels (POST)",
            "get_map": "/api/get_map (GET)",
            "user_stats": "/api/user_stats (GET)",
            "next_allowed_time": "/api/next_allowed_time (GET)"
        }
    }), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Invalid data'}), 400

    username = data['username']
    password = data['password']

    if len(username) < 3 or len(password) < 6:
        return jsonify({'message': 'Username must be at least 3 characters and password must be at least 6 characters'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            user_id = cursor.lastrowid
            user = User(id=user_id, username=username, password=hashed_password)
            login_user(user)
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Username already exists'}), 400
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Invalid data'}), 400

    username = data['username']
    password = data['password']

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user[2], password):
            user_obj = User(id=user[0], username=user[1], password=user[2])
            login_user(user_obj)
            return jsonify({'message': 'Login successful'}), 200
        return jsonify({'message': 'Invalid credentials'}), 400

@app.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/update_pixels', methods=['POST'])
@login_required
def update_pixels():
    user_id = current_user.id
    data = request.json
    pixels = data['pixels']
    now = datetime.datetime.now(datetime.timezone.utc)  # Use UTC to avoid timezone issues
    print(f"Current time: {now}")

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(placed_at) FROM pixels WHERE user_id = ?', (user_id,))
        last_placed = cursor.fetchone()[0]

        if last_placed:
            last_placed_time = datetime.datetime.fromisoformat(last_placed).replace(tzinfo=datetime.timezone.utc)
            print(f"Last placed time: {last_placed_time}")
            time_since_last_placement = now - last_placed_time
            print(f"Time since last placement: {time_since_last_placement}")
            if time_since_last_placement < datetime.timedelta(minutes=10):
                next_allowed_time = last_placed_time + datetime.timedelta(minutes=10)
                print(f"Next allowed time: {next_allowed_time}")
                return jsonify({
                    'message': 'You need to wait before placing another pixel',
                    'next_allowed_time': next_allowed_time.isoformat()
                }), 403

        for pixel in pixels:
            lat = pixel['lat']
            lng = pixel['lng']
            color = pixel['color']
            cursor.execute('INSERT INTO pixels (lat, lng, color, user_id, placed_at) VALUES (?, ?, ?, ?, ?)', (lat, lng, color, user_id, now))
        conn.commit()

    next_allowed_time = now + datetime.timedelta(minutes=10)
    print(f"Next allowed time after placement: {next_allowed_time}")
    return jsonify({"status": "success", "user_id": user_id, "next_allowed_time": next_allowed_time.isoformat()})

@app.route('/api/get_map', methods=['GET'])
def get_map():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pixels.lat, pixels.lng, pixels.color, pixels.user_id, pixels.placed_at, users.username
            FROM pixels
            JOIN users ON pixels.user_id = users.id
        ''')
        pixels = cursor.fetchall()
    
    return jsonify({"pixels": [
        {
            "lat": row[0], 
            "lng": row[1], 
            "color": row[2], 
            "user_id": row[3], 
            "placed_at": row[4], 
            "username": row[5]
        } for row in pixels
    ]})

@app.route('/api/user_stats', methods=['GET'])
@login_required
def user_stats():
    user_id = current_user.id
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # User-specific stats
        cursor.execute('SELECT COUNT(*) FROM pixels WHERE user_id = ?', (user_id,))
        total_pixels_placed = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT color) FROM pixels WHERE user_id = ?', (user_id,))
        total_unique_colors = cursor.fetchone()[0]

        cursor.execute('SELECT lat, lng, color FROM pixels WHERE user_id = ?', (user_id,))
        placed_pixels = cursor.fetchall()

        # World stats
        cursor.execute('SELECT COUNT(*) FROM pixels')
        total_world_pixels_placed = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM pixels')
        total_users_with_pixels = cursor.fetchone()[0]

        # Earth surface area calculation
        def calculate_percentage_pixels_placed(total_world_pixels_placed):
            total_grid_cells = 459216307166210800  # Total grid cells on the Earth's surface
            percentage_pixels_placed = (total_world_pixels_placed / total_grid_cells) * 100
            return percentage_pixels_placed

        # Format large numbers
        def humanize_large_number(number):
            if number < 1000:
                return str(number)
            for unit in ['K', 'M', 'B', 'T', 'P', 'E']:
                number /= 1000.0
                if number < 1000:
                    return f"{number:.2f}{unit}"
            return f"{number:.2f}Z"

        # Calculate the percentage of pixels placed
        percentage_pixels_placed = calculate_percentage_pixels_placed(total_world_pixels_placed)

        # Prepare the response
        user_stats = {
            'totalPixelsPlaced': humanize_large_number(total_pixels_placed),
            'totalUniqueColors': total_unique_colors,
            'placedPixels': [{'lat': lat, 'lng': lng, 'color': color} for lat, lng, color in placed_pixels],
            'totalWorldPixelsPlaced': humanize_large_number(total_world_pixels_placed),
            'totalUsersWithPixels': humanize_large_number(total_users_with_pixels),
            'percentagePixelsPlaced': round(percentage_pixels_placed, 20)  # Increased precision for small percentages
        }

    return jsonify(user_stats)

@app.route('/api/next_allowed_time', methods=['GET'])
@login_required
def next_allowed_time():
    user_id = current_user.id
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(placed_at) FROM pixels WHERE user_id = ?', (user_id,))
        last_placed = cursor.fetchone()[0]
        if last_placed:
            last_placed_time = datetime.datetime.fromisoformat(last_placed).replace(tzinfo=datetime.timezone.utc)
            next_allowed_time = last_placed_time + datetime.timedelta(minutes=10)
            return jsonify({"next_allowed_time": next_allowed_time.isoformat()})
        else:
            return jsonify({"next_allowed_time": datetime.datetime.now(datetime.timezone.utc).isoformat()})

if __name__ == '__main__':
    app.run(debug=True)