from flask import Flask, request, abort
from http import HTTPStatus
from user import user_manager, authenticate_user
from item import item_manager
from serviceman import serviceman_manager
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from decouple import config
from db import db
from flask_cors import CORS
from datetime import timedelta, datetime


login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return user_manager.get_by_id(user_id)

app = Flask(__name__)
app.secret_key = config("secret_key", "009e5686fbe6267253fa2c0acfae50f6c4b1e0ae3e12184b101d461f32e49b7e")
login_manager.init_app(app)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://postgres:{config('db_password')}@{config('db_host', '3.71.13.232')}:{config('db_port', '5432')}/uzh"
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
db.init_app(app)
#TODO fix security issue
CORS(app)

with app.app_context():
    db.create_all()

@login_manager.unauthorized_handler
def unauthorized():
    abort(HTTPStatus.UNAUTHORIZED)

@app.route('/users', methods = ['POST'])
def authenticate():
    username = request.json.get('username')
    password = request.json.get('password')
    user = user_manager.get_by_id(username)
    if authenticate_user(user, password):
        login_user(user, remember=True)
        return {'username': username, 'password': password}, HTTPStatus.FOUND
    else:
        abort(HTTPStatus.UNAUTHORIZED)

@app.route("/users", methods=['PUT'])
@login_required
def create_user():
    if not current_user.is_admin:
        abort(HTTPStatus.UNAUTHORIZED)
    username = request.json.get('username')
    password = request.json.get('password')
    is_admin = request.json.get('is_admin')
    if username == current_user.get_id():
        abort(HTTPStatus.UNAUTHORIZED)
    user_manager.create_user(username, password, is_admin)
    return {'username': username, 'password': password, "is_admin": is_admin}, HTTPStatus.CREATED


@app.route("/serviceman", methods=['PUT'])
#@login_required
def create_serviceman():
    name = request.json.get('name')
    surname = request.json.get('surname')
    patronymic = request.json.get("patronymic")
    id = serviceman_manager.create_service_man(name, surname, patronymic)
    return {'id': id}, HTTPStatus.CREATED


@app.route("/serviceman/<id>", methods=['get'])
def get_serviceman(id):
    serviceman = serviceman_manager.get_by_id(id)
    return serviceman.to_dict()


@app.route("/serviceman", methods=['get'])
def get_servicemen():
    return [serviceman.to_dict() for serviceman in serviceman_manager.get_all()]



@app.route("/item", methods=['PUT'])
def create_item():
    name = request.json.get('name')
    returnable = bool(request.json.get('returnable'))
    term = int(request.json.get('term')) # days
    id = item_manager.create_item(name, returnable, term)
    return {"id": id}, HTTPStatus.CREATED

@app.route("/item/<id>", methods=['get'])
def get_item(id):
    item = item_manager.get_by_id(id)
    return item.to_dict()

@app.route("/item", methods=['get'])
def get_items():
    return [item.to_dict() for item in item_manager.get_all()]


@app.route("/serviceman/<serviceman_id>/item/<item_id>", methods=['PUT'])
def issue_item(serviceman_id, item_id):
    date = datetime.strptime(request.json.get('date'), "%Y-%m-%d")
    size = request.json.get("size")
    serviceman = serviceman_manager.get_by_id(serviceman_id)
    item = item_manager.get_by_id(item_id)
    id = serviceman_manager.issue_item(serviceman, item, size, date)
    return {"id": id}, HTTPStatus.CREATED

@app.route("/expires", methods=['GET'])
def expires():
    from_date = datetime.strptime(request.args.get("from"), "%Y-%m-%d")
    term = int(request.args.get("term"))
    return [issue.to_dict() for issue in item_manager.get_expires(from_date, term)]


@app.route("/norm", methods=['PUT'])
def create_norm():
    sexes = request.json.get("sexes")
    print("sexes: ", sexes)
    ranks = request.json.get("ranks")
    print("ranks: ", ranks)




@app.route("/logout")
@login_required
def logout():
    logout_user()


@app.route("/authorised")
@login_required
def hello_authorised():
    return f"hello {current_user.get_id}"


@app.route("/hello")
def hello():
    return "hello CI/CD!"


if __name__ == '__main__':
    """
    with app.app_context():        
        user_manager.create_user("test", "test", True)
    """
    app.run(host='0.0.0.0')
