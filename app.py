from flask import Flask, request

from user import user_manager, authenticate

from flask_login import LoginManager
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return user_manager.get(user_id)

app = Flask(__name__)
app.secret_key = '009e5686fbe6267253fa2c0acfae50f6c4b1e0ae3e12184b101d461f32e49b7e'
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

        return {'username': username, 'password': password}, 401
    else:
        return {'username': username, 'password': password}, 200



@app.route("/hello")
def hello():
    return "hello World"

if __name__ == '__main__':
    app.run(host='0.0.0.0')

