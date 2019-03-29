#!/usr/local/bin python3
# -*- coding: utf8 -*-

__author__ = 'vincen'

from flask import Flask, redirect, url_for, escape, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import datetime, base64, json, time
from logging.config import dictConfig
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

########################################################################
#                           global varialbe
########################################################################
app = Flask(__name__)
app.debug = True                # enable debug mode
app.config['SECRET_KEY'] = 'nroad is a good company'        # a secret key using by token
# database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://cc3:cc3@localhost/cc3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_AS_ASCII"] = False        # jsonify serialize chinese word, not original unicode
dictConfig({                        # loggin config
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'file': {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': 'nroad.log',
        'formatter': 'default',
        'maxBytes': 102400,
        'backupCount': 3
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
})
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
log = app.logger

SCHOOL = {
    '10704': '西安科技大学',    '12712': '西安欧亚学院',    '11664': '西安邮电大学',
    '10698': '西安交通大学',    '10722': '咸阳师范学院',    '10716': '陕西中医药大学',
    '10697': '西北大学',        '00000': 'ALL'
}
########################################################################
#                                   api
########################################################################
@app.route('/now', methods=['GET'])
def current_time():
    _now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return jsonify({'now': _now}), 200

@app.route('/v1/login', methods=['POST'])
def login():
    _secret_iden = request.json.get('iden')
    _origin_iden = base64.urlsafe_b64decode(_secret_iden)
    _up = json.loads(_origin_iden)
    _up_username = _up.get('username').strip()
    _up_password = _up.get('password').strip()
    _userService = UserService()
    _user = _userService.find_user(_up_username)
    log.info(_user.nickname + ' signed in')
    if _user.verify_password(_up_password):
        _token = Auths.generate_auth_token(_user)
        return jsonify({'token': _token.decode('ascii')}), 200
    else:
        abort_if_none(_user, 404, 'User not found')

@app.route("/v1/users", methods=['POST'])
def create_user_api1():
    _current = Auths.verify_auth_token(request)
    if _current is not None:
        _username = request.json.get('username')
        _nickname = request.json.get('nickname')
        _password = request.json.get('password')
        _user_service = UserService()
        if _username is None or _password is None:
            abort(400, 'missing arguments')
        if _user_service.find_user(_username) is not None:
            abort(400, 'existing user')
        _user = _user_service.create_user(_username, _nickname, _password)
        return (jsonify({'username': _user.username}), 201,
                {'Location': url_for('read_user_api1', pkid=_user.pkid, _external=True)})
    else:
        return abort(401, 'unauthorized')

@app.route("/v1/users", methods=['GET'])
def read_user_api1():
    _current = Auths.verify_auth_token(request)
    if _current is not None:
        return jsonify({'username': _current.username, 'nickname': _current.nickname})
    else:
        abort(401, 'unauthorized')

@app.route("/v1/permissions", methods=['POST'])
def create_permission_api1():
    _current = Auths.verify_auth_token(request)
    if _current is not None:
        user_id = request.json.get('userid')
        school_code = request.json.get('schoolcode')
        carrier = request.json.get('carrier')
        p = Permission(user_id = user_id, school_code = school_code, carrier = carrier)
        permission_service = PermissionService()
        p = permission_service.create_permission(p)
        return (jsonify({'user_id': p.user_id, 'school': p.school_code, 'carrier': p.carrier}), 201)
    else:
        abort(401, 'unauthorized')

@app.route("/v1/permissions", methods=['GET'])
def read_permissions_api1():
    _current = Auths.verify_auth_token(request)
    if _current is not None:
        permission_service = PermissionService()
        temp = permission_service.get_permission(_current.pkid)
        return jsonify({'result': temp, 'school': SCHOOL}), 200
    else:
        return abort(401, 'unauthorized')

@app.route("/v1/data/overview", methods=['GET'])
def get_data_overview_api1():
    _current = Auths.verify_auth_token(request)
    if _current is not None:
        order_service = OrderService()
        result = order_service.get_data_overview()
        return jsonify({'result': result}), 200
    else:
        return abort(401, 'unauthorized')

@app.route("/v1/data/statistic/new/<string:code>", methods=['GET'])
def get_data_statistic_new_api1(code):
    _current = Auths.verify_auth_token(request)         # check token
    if _current is not None:
        start = request.args.get("start")
        end = request.args.get("end")
        order_service = OrderService()
        result = order_service.get_data_statistic_new(_current.pkid, start, end, code)
        if result is not None:
            return jsonify({'result': result}), 200
        else:
            abort(403, 'forbidden')
    else:
        abort(401, 'unauthorized')

@app.route("/v1/data/statistic/total/<string:code>", methods=['GET'])
def get_data_statistic_total_api1(code):
    _current = Auths.verify_auth_token(request)
    if _current is not None:
        start = request.args.get("start")
        end = request.args.get("end")
        order_service = OrderService()
        result = order_service.get_data_statistic_total(_current.pkid, start, end, code)
        if result is not None:
            return jsonify({'result': result}), 200
        else:
            abort(403, 'forbidden')
    else:
        abort(401, 'unauthorized')

########################################################################
#                               service
########################################################################
class OrderService(object):
    def get_data_statistic_new(self, user_id, start, end, code):
        _permission_service = PermissionService()
        _permission = _permission_service.get_permission_by_user_and_school(user_id, code)
        if _permission is None:
            return None
        _order_dao = OrderDao()
        _temps = _order_dao.get_data_statistic_new(start, end, code, _permission.carrier)
        _result = dict()
        for temp in _temps:
            torder = TOrder(*temp)
            value = _result.get(torder.order_time)
            if value is None:
                value = dict()
                value['order_time'] = torder.order_time
                value[torder.school] = torder.orders
            else:
                value[torder.school] = torder.orders
            _result[torder.order_time] = value
        return list(_result.values())

    def get_data_statistic_total(self, user_id, start, end, code):
        _permission_service = PermissionService()
        _permission = _permission_service.get_permission_by_user_and_school(user_id, code)
        if _permission is None:
            return None
        _order_dao = OrderDao()
        _temps = _order_dao.get_data_statistic_total(start, end, code, _permission.carrier)
        _result = dict()
        for temp in _temps:
            torder = TOrder(*temp)
            value = _result.get(torder.order_time)
            if value is None:
                value = dict()
                value['order_time'] = torder.order_time
                value[torder.school] = torder.orders
            else:
                value[torder.school] = torder.orders
            _result[torder.order_time] = value
        return list(_result.values())

    def get_data_overview(self):
        order_dao = OrderDao()
        temp1 = order_dao.get_new_orders_in_yesterday()
        new_orders_in_yesterday = temp1[0]
        temp2 = order_dao.get_top1_orders_in_yesterday()
        top1_orders_in_yesterday = {'school': temp2[0], 'count': temp2[1]}
        temp3 = order_dao.get_total_orders_count()
        total_orders_count = temp3[0]
        temp4 = order_dao.get_top1_orders_count()
        top1_orders_count = {'school': temp4[0], 'count': temp4[1]}
        result = {"new_orders_in_yesterday": new_orders_in_yesterday, 
                  "top1_orders_in_yesterday": top1_orders_in_yesterday,
                  "total_orders_count": total_orders_count,
                  "top1_orders_count": top1_orders_count
        }
        return result


class UserService(object):
    def create_user(self, username, nickname, password):
        user = User(username = username, nickname = nickname)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def find_user(self, username):
        return User.query.filter_by(username=username).first()


class PermissionService(object):
    def create_permission(self, permission):
        db.session.add(permission)
        db.session.commit()
        return permission
    
    def get_permission(self, userid):
        permissions = Permission.query.filter_by(user_id = userid).all()
        result = []
        for perm in permissions:
            result.append(perm.to_dict())
        return result

    def get_permission_by_user_and_school(self, user_id, school_code):
        return Permission.query.filter_by(user_id = user_id, school_code = school_code).first()

########################################################################
#                                dao
########################################################################
class OrderDao(object):
    SQL_1 = "SELECT SUM ( orders ) FROM v_order "
    SQL_2 = '''
            SELECT t.school, SUM ( t.orders ) FROM v_order t 
            {param} 
            GROUP BY t.school 
            HAVING SUM ( t.orders ) = (
                SELECT MAX( r.topcount ) 
                FROM ( 
                    SELECT P.school sch, SUM ( P.orders ) topcount FROM v_order P 
                    {param}
                    GROUP BY P.school ) r );
        '''
    CONDITION = "WHERE order_time = :order_time "
    SQL_3 = '''
            SELECT CAST(o.order_time AS varchar), o.school, SUM ( o.orders ) total 
            FROM v_order_2 o
            WHERE o.order_time >= :start AND o.order_time <= :end 
                {param}
            GROUP BY o.order_time, o.school
            ORDER BY o.order_time DESC;
        '''
    SQL_4 = '''
            SELECT CAST(o.order_time AS varchar), o.school, SUM ( o.orders ) total 
            FROM v_order_3 o
            WHERE o.order_time >= :start AND o.order_time <= :end 
                {param}
            GROUP BY o.order_time, o.school
            ORDER BY o.order_time DESC;
        '''

    def __init__(self):
        self.yesterday = Utils().get_yesterday().strftime("%Y-%m-%d")

    def get_new_orders_in_yesterday(self):
        sql = self.SQL_1 + self.CONDITION
        return db.session.execute(sql, {"order_time": self.yesterday}).fetchone()

    def get_top1_orders_in_yesterday(self):
        sql = self.SQL_2.format(param=self.CONDITION)
        return db.session.execute(sql, {"order_time": self.yesterday}).fetchone()

    def get_total_orders_count(self):
        sql = self.SQL_1
        return db.session.execute(sql).fetchone()

    def get_top1_orders_count(self):
        sql = self.SQL_2.format(param="")
        return db.session.execute(sql).fetchone()

    def get_data_statistic_new(self, start, end, code, carrier):
        _params = {"start": start, "end": end}
        _cond = ''
        if code != '00000':
            _cond = 'AND o.school = :school '
            _params["school"] = SCHOOL.get(code)
        if carrier != 'ALL':
            _cond += 'AND carrier = :carrier '
            _params["carrier"] = carrier
        sql = self.SQL_3.format(param=_cond)
        return db.session.execute(sql, _params).fetchall()

    def get_data_statistic_total(self, start, end, code, carrier):
        _params = {"start": start, "end": end}
        _cond = ''
        if code != '00000':
            _cond = 'AND o.school = :school '
            _params["school"] = SCHOOL.get(code)
        if carrier != 'ALL':
            _cond += 'AND carrier = :carrier '
            _params["carrier"] = carrier
        sql = self.SQL_4.format(param=_cond)
        return db.session.execute(sql, _params).fetchall()

########################################################################
#                               domain
########################################################################
class Order(db.Model):
    __tablename__ = 't_order'

    pkid = db.Column(db.Integer, primary_key = True)
    pid = db.Column(db.String(255))
    product_name = db.Column(db.String(255))
    price = db.Column(db.Float)
    school = db.Column(db.String(255))
    count = db.Column(db.Integer)
    order_time = db.Column(db.Date)

    def to_dict(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        data = dict.get("order_time")
        dict["order_time"] = data.strftime('%Y-%m-%d')
        return dict


class Product(db.Model):
    __tablename__ = 't_product'
    
    pkid = db.Column(db.Integer, primary_key = True)
    pid = db.Column(db.String(255))
    product_name = db.Column(db.String(255))
    school = db.Column(db.String(255))
    carrier = db.Column(db.String(255))
    is_boss = db.Column(db.Boolean)
    percentage = db.Column(db.Float)

    def to_dict(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict


class User(db.Model):
    __tablename__ = 't_user'

    pkid = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(255))
    nickname = db.Column(db.String(255))
    password = db.Column(db.String(255))

    def hash_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Permission(db.Model):
    __tablename__ = 't_permission'

    pkid = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    school_code = db.Column(db.String(255))
    carrier = db.Column(db.String(255))

    def to_dict(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        data = dict.get("school_code")
        dict["school"] = SCHOOL.get(data)
        return dict

########################################################################
#                         transfer object
########################################################################
class TOrder(object):
    order_time = None
    school = None
    orders = None
  
    def __init__(self, order_time, school, orders):
        self.order_time = order_time
        self.school = school
        self.orders = orders
    
    def to_dict(self):
        dict = self.__dict__
        if "_sa_instance_state" in dict:
            del dict["_sa_instance_state"]
        return dict

########################################################################
#                                   utils
########################################################################
class Utils(object):
    def get_yesterday(self):
        """
        :return: yesterday，format : 1970-01-01
        """
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        return yesterday

########################################################################
#                                   utils
########################################################################
class Auths(object):
    @staticmethod
    def generate_auth_token(user, expiration = 600):
        log.info(user)
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({'pkid': user.pkid})
    
    @staticmethod
    def verify_auth_token(request):
        token = request.headers.get('Authorization')
        if token is None:
            return None
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None                 # token expired
        except BadSignature:
            return None                 # invalid token
        user = User.query.get(data['pkid'])
        return user

########################################################################
#                             Test Running
########################################################################
if __name__ == '__main__':
    # entry the application in development environment
    # support cors
    CORS(app, supports_credentials=True)
    app.run(host='0.0.0.0', port=5000)
