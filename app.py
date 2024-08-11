from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token
import datetime
from models import db, User, Friendship, Location

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///proximityapp.db'
app.config['JWT_SECRET_KEY'] = 'mysuperawesomesecretkey'  # Change this to a secure secret key
jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/hello', methods=['GET'])
def hello():
  return "Hello World!!"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = data['password']
    
    user = User(username=username, email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

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

if __name__ == '__main__':
    app.run(debug=True)
