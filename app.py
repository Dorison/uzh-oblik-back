from flask import Flask, request, abort
from http import HTTPStatus
from user import user_manager, authenticate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return user_manager.get(user_id)

app = Flask(__name__)
# TODO implement more secure way.
app.secret_key = "009e5686fbe6267253fa2c0acfae50f6c4b1e0ae3e12184b101d461f32e49b7e"
login_manager.init_app(app)

@login_manager.unauthorized_handler
def unauthorized():
    abort(HTTPStatus.UNAUTHORIZED)

@app.route('/users', methods = ['POST'])
def authenticate():
    username = request.json.get('username')
    password = request.json.get('password')
    user = user_manager.users_by_id(username)
    if authenticate(user, password):
        abort(HTTPStatus.UNAUTHORIZED)
    else:
        login_user(user, remember=True)
        return {'username': username, 'password': password}, HTTPStatus.FOUND

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
    app.run(host='0.0.0.0')

