from flask_migrate import Migrate
from flask import request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_login import LoginManager, UserMixin, login_required, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
db = SQLAlchemy(app)
api = Api(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)



class User(UserMixin, db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), default='ROLE_ADMIN')
    company_id = db.Column(db.Integer, db.ForeignKey('Company.id', name='fk_user_company'))
    def __repr__(self):
        return f"<User {self.username}>"

class Company(db.Model):
    __tablename__ = "Company"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    employees = db.Column(db.Integer, nullable=False)
    users = db.relationship('User', backref='Company', lazy=True)
    def __repr__(self):
        return f"<Company {self.name}>"

class Client(db.Model):
    __tablename__ = "Client"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id', name='fk_client_client'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('Company.id', name='fk_client_company'), nullable=False)
    def __repr__(self):
        return f"<Client {self.name}>"


class ClientUser(db.Model):
    __tablename__ = "ClientUser"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    deleted_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    def __repr__(self):
        return f"<Client {self.client_id}>"
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define custom decorator for role-based access control
def admin_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        # Assume you have a user object with 'role' attribute
        if current_user.role != 'ROLE_ADMIN':
            return {'message': 'Access forbidden'}, 403
        return fn(*args, **kwargs)
    return wrapper

# Define RESTful resources
class UserListResource(Resource):
    def get(self):
        username_filter = request.args.get('username', None)
        if username_filter:
            users = User.query.filter_by(username=username_filter).all()
        else:
            users = User.query.all()
        return {'users': [{'id': user.id, 'username': user.username} for user in users]}

class UserReplaceResource(Resource):
    def put(self, user_id):
        user = User.query.get(user_id)
        if user:
            data = request.get_json()
            user.username = data.get('username', user.username)
            db.session.commit()
            return {'message': 'User updated successfully'}
        return {'message': 'User not found'}, 404

class ClientListResource(Resource):
    @admin_required
    def post(self):
        data = request.get_json()
        if not all(field in data for field in ['name', 'email', 'phone', 'user_id', 'company_id']):
            return {'message': 'Missing required fields'}, 400

        # Add validation for unique company
        if Client.query.filter_by(company_id=data['company_id']).first():
            return {'message': 'Company already taken by another client'}, 400

        client = Client(**data)
        db.session.add(client)
        db.session.commit()
        return {'message': 'Client created successfully'}, 201

class ClientFieldResource(Resource):
    def patch(self, client_id):
        client = Client.query.get(client_id)
        if client:
            data = request.get_json()
            for key, value in data.items():
                setattr(client, key, value)
            db.session.commit()
            return {'message': 'Client field(s) updated successfully'}
        return {'message': 'Client not found'}, 404

# Add resources to the API
api.add_resource(UserListResource, '/users')
api.add_resource(UserReplaceResource, '/users/<int:user_id>')
api.add_resource(ClientListResource, '/clients')
api.add_resource(ClientFieldResource, '/clients/<int:client_id>')