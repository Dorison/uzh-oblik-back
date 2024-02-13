from flask import Flask, request, abort
from http import HTTPStatus
from user import user_manager, authenticate_user
from item import item_manager
from norm import norm_manager, ObligationDto
from serviceman import serviceman_manager
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from decouple import config
from db import db, ranks, officer_ranks
from flask_cors import CORS
from datetime import timedelta, datetime
from logging import getLogger
import json
logger = getLogger(__name__)

datetime_format = "%d.%m.%Y %H:%M:%S"
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return user_manager.get_by_id(user_id)


app = Flask(__name__)
app.secret_key = config("secret_key", "009e5686fbe6267253fa2c0acfae50f6c4b1e0ae3e12184b101d461f32e49b7e")
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://postgres:{config('db_password')}@{config('db_host', '3.71.13.232')}:{config('db_port', '5432')}/uzh"
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config['JSON_AS_ASCII'] = False
app.config['REMEMBER_COOKIE_NAME'] = 'secret'
app.config['REMEMBER_COOKIE_HTTPONLY'] = False
login_manager.init_app(app)
login_manager.session_protection = None

db.init_app(app)
# TODO fix security issue
CORS(app)


def none_is_now(date_str, format="%Y-%m-%d"):
    return datetime.now() if date_str is None else datetime.strptime(date_str, format)


class NonASCIIJSONEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        kwargs['ensure_ascii'] = False
        super(NonASCIIJSONEncoder, self).__init__(**kwargs)


app.json_encoder = NonASCIIJSONEncoder

with app.app_context():
    db.create_all()


@login_manager.unauthorized_handler
def unauthorized():
    abort(HTTPStatus.UNAUTHORIZED)


@app.route('/users', methods=['POST'])
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


# @login_required
def _create_serviceman(request, date):
    name = request.json.get('name')
    surname = request.json.get('surname')
    patronymic = request.json.get("patronymic")
    sex = bool(request.json.get('sex'))
    rank = int(request.json.get('rank'))
    group = str(request.json.get('group'))
    id = serviceman_manager.create_service_man(name, surname, patronymic, sex, rank, group, date)
    return {'id': id}, HTTPStatus.CREATED


@app.route("/serviceman", methods=['PUT'])
def create_serviceaman():
    return _create_serviceman(request, datetime.now())


@app.route("/history/serviceman", methods=['PUT'])
def history_create_serviceman():
    return _create_serviceman(request, datetime.strptime(request.json.get('date'), "%Y-%m-%d"))


def _promote(id, request, date):
    rank = int(request.json.get('rank'))
    serviceman = serviceman_manager.get_by_id(id)
    serviceman_manager.promote(serviceman, rank, date)
    return {"id": id}


@app.route("/serviceman/<int:id>/rank", methods=['PUT'])
def promote(id):
    return _promote(id, request, datetime.now())


@app.route("/serviceman/<int:id>/paternity_leave", methods=['PUT'])
def paternity_leave(id):
    from_date = datetime.strptime(request.json.get('from_date'), "%Y-%m-%d")
    to_date_str = request.json.get('to_date')
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d") if to_date_str else None
    serviceman = serviceman_manager.get_by_id(id)
    leave_id = serviceman_manager.parental_leave(serviceman, from_date, to_date)
    return {id: leave_id}, HTTPStatus.CREATED


@app.route("/serviceman/<int:id>/paternity_leave/<int:leave_id>", methods=['PATCH'])
def paternity_leave_close(id, leave_id):
    to_date = datetime.strptime(request.json.get('to_date'), "%Y-%m-%d")
    serviceman = serviceman_manager.get_by_id(id)
    leave_id = serviceman_manager.parental_leave_close(serviceman, leave_id, to_date)
    return {id: leave_id}, HTTPStatus.CREATED


@app.route("/history/serviceman/<int:id>/rank", methods=['PUT'])
def history_promote(id):
    return _promote(id, request, datetime.strptime(request.json.get('date'), "%Y-%m-%d"))


@app.route("/serviceman/<int:id>/terminate", methods=['PUT'])
def terminate(id):
    date = datetime.strptime(request.json.get('from_date'), "%Y-%m-%d")
    serviceman = serviceman_manager.get_by_id(id)
    serviceman_manager.terminate(serviceman, date)
    return {"id": id}


@app.route("/serviceman/<int:id>", methods=['get'])
# @login_required
def get_serviceman(id):
    serviceman = serviceman_manager.get_by_id(id)
    return serviceman.to_dict()


# отримати норми службовця
@app.route("/serviceman/<int:id>/norm")
def get_serviceman_norms(id):
    serviceman = serviceman_manager.get_by_id(id)
    norms = norm_manager.get_potential_norms(serviceman)
    norms = norm_manager.refine_norms(serviceman, norms)
    return [norm.to_dict() for norm in norms]


# отримати належності службовця на дату
@app.route("/serviceman/<int:id>/obligation", methods=['get'])
def get_serviceman_obligations(id):
    to_date = none_is_now(request.args.get("to"))
    serviceman = serviceman_manager.get_by_id(id)
    norms = norm_manager.get_potential_norms(serviceman)
    obligations = norm_manager.get_obligations(serviceman, norms, to_date)
    result = [obligation.to_dict() for item_obligations in obligations.values() for obligation in item_obligations]
    return result


@app.route("/serviceman", methods=['get'])
def get_servicemen():
    return [serviceman.to_dict() for serviceman in serviceman_manager.get_all()]


@app.route("/item", methods=['PUT'])
def create_item():
    name = request.json.get('name')
    returnable = bool(request.json.get('returnable'))
    # term = int(request.json.get('term')) # days
    id = item_manager.create_item(name, returnable)
    return {"id": id}, HTTPStatus.CREATED


@app.route("/item/<int:id>", methods=['get'])
def get_item(id):
    item = item_manager.get_by_id(id)
    return item.to_dict()


@app.route("/item/<int:id>", methods=['PUT'])
def update_item(id):
    name = request.json.get('name')
    returnable = bool(request.json.get('returnable'))
    item = item_manager.get_by_id(id)
    item.name = name
    item.returnable = returnable
    id = item_manager.update_item(item)
    return {"id": id}, HTTPStatus.CREATED


@app.route("/item/<int:id>", methods=['POST'])
def add_stock(id):
    date = none_is_now(request.args.get("date"))
    item = item_manager.get_by_id(id)
    # {"size": count}
    shipment_id = item_manager.add_stock(item, request.json, date)
    return {"id": shipment_id}, HTTPStatus.OK


@app.route("/item/<int:id>", methods=['PATCH'])
def remove_size(id):
    size_to_remove = request.json.get("size_to_remove")
    item = item_manager.get_by_id(id)
    return {"id": item_manager.remove_stock(item, size_to_remove)}


@app.route("/item", methods=['get'])
def get_items():
    return [item.to_dict() for item in item_manager.get_all()]


@app.route("/item/stock", methods=['get'])
def get_stock():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    return [dto.to_dict() for dto in item_manager.get_stock(from_date, to_date)]


@app.route("/serviceman/<int:serviceman_id>/item/<int:item_id>", methods=['PUT'])
def issue_item(serviceman_id, item_id):
    date = datetime.strptime(request.json.get('date'), "%d.%m.%Y %H:%M:%S")
    count = request.json.get("count")
    size = request.json.get("size")
    serviceman = serviceman_manager.get_by_id(serviceman_id)
    item = item_manager.get_by_id(item_id)
    granted = datetime.now()
    id = serviceman_manager.issue_item(serviceman, item, size, date, granted, count)
    return {"id": id}, HTTPStatus.CREATED


@app.route("/history/serviceman/<int:serviceman_id>/item/<int:item_id>", methods=['PUT'])
def history_issue_item(serviceman_id, item_id):
    date = datetime.strptime(request.json.get('date'), "%d.%m.%Y %H:%M:%S")
    granted = datetime.strptime(request.json.get('granted'), "%Y-%m-%d")
    count = request.json.get("count")
    serviceman = serviceman_manager.get_by_id(serviceman_id)
    item = item_manager.get_by_id(item_id)
    id = serviceman_manager.history_issue_item(serviceman, item, date, granted, count)
    return {"id": id}, HTTPStatus.CREATED


# задати розмір службовця для певної речі
@app.route("/serviceman/<int:serviceman_id>/item/<int:item_id>/size", methods=['PUT'])
def set_item_size(serviceman_id, item_id):
    size = request.json.get("size")
    serviceman = serviceman_manager.get_by_id(serviceman_id)
    item = item_manager.get_by_id(item_id)
    id = serviceman_manager.set_size(serviceman, item, size)
    return {"id": id}, HTTPStatus.CREATED


@app.route("/requirements", methods=['GET'])
def requirements():
    to_date = datetime.strptime(request.args.get("to"), "%Y-%m-%d")
    return [requirement.to_dict() for requirement in _reqruirements(to_date)]


def _reqruirements(to_date):
    staff = [serviceman for serviceman in serviceman_manager.get_all() if serviceman.termination_date is None]
    norms = list(norm_manager.get_all())
    obligations = [norm_manager.get_obligations(serviceman, norms, to_date) for serviceman in staff]
    return item_manager.get_requirements(obligations)


"""
@app.route("/norm/draft", methods=['PUT'])
def create_draft():
    return {"draft_id": 42}
"""


@app.route("/norm", methods=['PUT'])
def create_norm():
    genders = request.json.get("genders")
    from_rank = request.json.get("from_rank")
    to_rank = request.json.get("to_rank")
    name = request.json.get("name")
    reason = request.json.get("reason")
    from_date = datetime.strptime(request.json.get("from"), "%Y-%m-%d")
    to_date_str = request.json.get("to", "")
    to_date = None if to_date_str =="" else datetime.strptime(to_date_str, "%Y-%m-%d")
    id = norm_manager.create_norm(genders, from_rank, to_rank, name, reason, from_date, to_date)
    return {"id": id}, HTTPStatus.CREATED


@app.route("/norm/<int:norm_id>/group", methods=['PUT'])
def create_norm_group(norm_id):
    name = request.json.get("name")
    obligations = [ObligationDto(item_id=jobligation["item_id"], count=jobligation["count"], term=jobligation["term"]) for jobligation in request.json.get("items")]
    norm_manager.add_group(norm_id, name, obligations)
    return {}, HTTPStatus.CREATED


# отримати всі норми
@app.route("/norm", methods=['GET'])
def get_all_norms():
    return [norm.to_dict() for norm in norm_manager.get_all()]


@app.route("/norm/<int:norm_id>", methods=['GET'])
def get_norm(norm_id):
    return norm_manager.get_norm(norm_id).to_dict_full()


# зберегти норму
@app.route("/norm/<int:norm_id>", methods=["PUT"])
def commit_norm(id):
    return {'id': id}, HTTPStatus.CREATED

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


@app.route("/ranks", methods=['GET'])
def all_ranks():
    return list(ranks[::-1]+officer_ranks[::-1])


# всі групи всіх норм
@app.route("/groups", methods=['GET'])
def all_groups():
    return list(norm_manager.get_groups())


def test1():
    with app.app_context():
        # user_manager.create_user("test", "test", True)
        kozak_id = serviceman_manager.create_service_man("Козак", "Андрій", "Володимирович", True, 13, "друга група")
        from datetime import datetime
        norm_id = norm_manager.create_norm([False, True], 10, 13, "польова форма", "наказ 66 від 19 ДБЯ",
                                           datetime.strptime("2023-11-28", "%Y-%m-%d"), None)
        t_shirt_id = item_manager.create_item("Фуфайка", False)
        t_shirt = item_manager.get_by_id(t_shirt_id)
        norm_manager.add_group(norm_id, "друга група", [ObligationDto(t_shirt_id, 365, 2)])
        norm_manager.add_group(norm_id, "перша група", [ObligationDto(t_shirt_id, 365*2, 1)])
        kozak = serviceman_manager.get_by_id(kozak_id)
        norms = list(norm_manager.get_potential_norms(kozak))
        issue_date = norm_manager.get_obligations(kozak, norms, datetime.strptime("2025-11-28", "%Y-%m-%d"))[t_shirt_id][0].date
        serviceman_manager.issue_item(kozak, t_shirt, "XXL", issue_date, datetime.now(), 1)
        print(norm_manager.get_obligations(kozak, norms, datetime.strptime("2025-11-28", "%Y-%m-%d")))

def test():
    with app.app_context():
        serviceman = serviceman_manager.get_by_id(1)
        rank = len(serviceman.rank_history)-1
        print(rank)
        serviceman_manager.promote(serviceman,rank+1, datetime.now())
        rank = len(serviceman.rank_history) - 1
        print(rank)
        serviceman = serviceman_manager.get_by_id(1)
        rank = len(serviceman.rank_history) - 1
        print(rank)

def test0():
    with app.app_context():
        serviceman = serviceman_manager.get_by_id(53)
        rank = len(serviceman.rank_history)-1
        print(rank)
        norms = norm_manager.get_potential_norms(serviceman)
        norms = list(norms)
        ref = norm_manager.refine_norms(serviceman, norms)
        ols = norm_manager.get_obligations(serviceman, norms, datetime.now())
        reqs = norm_manager.get_obligations(serviceman, norms, datetime.strptime("2025-11-28", "%Y-%m-%d"))
        print(list(norms))
        print(ref)
        print(ols)
        print(reqs)

def test1():
    with app.app_context():
        print(item_manager.get_stock(datetime.strptime("2022-01-01", "%Y-%m-%d"), datetime.strptime("2024-01-01", "%Y-%m-%d")))

def test2():
    with app.app_context():
        serviceman = serviceman_manager.get_by_id(70)
        norms = norm_manager.get_potential_norms(serviceman)
        to_date =datetime.strptime("2034-01-01", "%Y-%m-%d")
        norms = list(norms)
        obligations = norm_manager.get_obligations(serviceman, norms, to_date)
        print(norms)
        for norm in norms:
            for obligation in norm.obligations:
                item = obligation.item
                if item.id == 45:
                    print(obligation)

        print(obligations[45])

if __name__ == '__main__':
    is_test = config("test", False, cast=bool)
    if is_test:
        test2()
    else:
        app.run(host='0.0.0.0')
