from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://username:password@your_server/database_name?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20))  # 'admin' or 'user'

class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(255))

# AuthController
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    new_user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password=data['password'],
        role='user'  # Default role for new users
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Email already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if user and user.is_active:
        access_token = create_access_token(identity={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_active': user.is_active,
            'role': user.role
        })
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# TodoController
@app.route('/get/<int:id>', methods=['GET'])
@jwt_required()
def get_todo(id):
    todo = TodoItem.query.get(id)
    if todo:
        return jsonify({'id': todo.id, 'title': todo.title, 'description': todo.description}), 200
    else:
        return jsonify({'message': 'Todo item not found'}), 404

@app.route('/todo/getall')
def get_all_todos():
    todos = Todo.query.all()
    todo_list = [{'id':todo.id, 'title':todo.title, 'description':todo.description} for todo in todos]
    return jsonify(todo_list)

@app.route('/todo/put/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = Todo.query.get_or_404(id)
    data = request.get_json()
    todo.title = data['title']
    todo.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Todo item updated successfully'})

@app.route('/todo/create', methods=['POST'])
def create_todo():
    data = request.get_json()
    new_todo = Todo(title=data['title'], description=data['description'])
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'message': 'Todo item created successfully', 'id': new_todo.id})


@app.route('/todo/delete/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo item deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)