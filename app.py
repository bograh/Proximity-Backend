from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import db, User, Friendship, Location

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///proximityapp.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.gmnturgnmsnxhabevrsh:uypKRVt7qAuGeiHv@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['JWT_SECRET_KEY'] = '9LlvwBNxtLW92rGonSRNcn+SCKlkpxnu0Og+IEkCm6o/mGAEr83h5t+BTi9VABtN6PSIpVQhBhhl62X5tM7+8A=='  # Change this to a secure secret key
jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/hello', methods=['GET'])
def hello():
  return "Hello World!!"

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({"error": "Missing fields"}), 400
        
        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    user_id = data['user_id']
    latitude = data['latitude']
    longitude = data['longitude']
    
    location = Location(user_id=user_id, latitude=latitude, longitude=longitude, timestamp=datetime.datetime.utcnow())
    db.session.add(location)
    db.session.commit()
    
    return jsonify({'message': 'Location updated successfully'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user_id': user.id
        }), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/home', methods=['GET'])
@jwt_required()
def home():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Get user's current location
    current_location = Location.query.filter_by(user_id=current_user_id).order_by(Location.timestamp.desc()).first()

    # Get nearby friends (within 1km and active in the last hour)
    nearby_friends = []
    if current_location:
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        nearby_friends = db.session.query(User, Location).join(Friendship, Friendship.friend_id == User.id)\
            .join(Location, Location.user_id == User.id)\
            .filter(Friendship.user_id == current_user_id)\
            .filter(Location.timestamp > one_hour_ago)\
            .filter(func.st_distance_sphere(
                func.point(Location.longitude, Location.latitude),
                func.point(current_location.longitude, current_location.latitude)
            ) < 1000).all()  # 1000 meters = 1km

    # Format nearby friends data
    friends_data = [{
        'id': friend.User.id,
        'username': friend.User.username,
        'latitude': friend.Location.latitude,
        'longitude': friend.Location.longitude,
        'last_seen': friend.Location.timestamp.isoformat()
    } for friend in nearby_friends]

    # Get notifications (this is a placeholder - implement based on your notification system)
    notifications = []  # You would populate this based on your notification logic

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'current_location': {
                'latitude': current_location.latitude if current_location else None,
                'longitude': current_location.longitude if current_location else None,
                'timestamp': current_location.timestamp.isoformat() if current_location else None
            }
        },
        'nearby_friends': friends_data,
        'notifications': notifications
    }), 200



if __name__ == '__main__':
    app.run(debug=True)
