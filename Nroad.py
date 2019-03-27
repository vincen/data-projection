#!/usr/local/bin python3
# -*- coding: utf8 -*-

__author__ = 'vincen'

from flask import Flask, redirect, url_for, escape, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import datetime, base64, json, time
from logging.config import dictConfig
from flask_bcrypt import Bcrypt
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
    secret_iden = request.json.get('iden')
    origin_iden = base64.urlsafe_b64decode(secret_iden)
    up = json.loads(origin_iden)
    up_username = up.get('username').strip()
    up_password = up.get('password').strip()
    userService = UserService()
    user = userService.find_user(up_username)
    log.info(user.nickname + ' signed in')
    if user.verify_password(up_password):
        token = Auths.generate_auth_token(user)
        return jsonify({'token': token.decode('ascii')}), 200
    else:
        abort_if_none(user, 404, 'User not found')

@app.route('/v1/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route("/v1/dashboard")
def dashboard():
    order_service = OrderService()
    temp = order_service.get_orders()
    return jsonify({'tasks': temp}), 200

@app.route("/v1/users", methods=['POST'])
def create_user_api1():
    username = request.json.get('username')
    nickname = request.json.get('nickname')
    password = request.json.get('password')
    userService = UserService()
    if username is None or password is None:
        abort(400)      # missing arguments
    if userService.find_user(username) is not None:
        abort(400)      # existing user
    user = userService.create_user(username, nickname, password)
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('read_user_api1', pkid=user.pkid, _external=True)})

@app.route("/v1/users/<int:pkid>", methods=['GET'])
def read_user_api1(pkid):
    user = User.query.get(pkid)
    if not user:
        abort(404)
    return jsonify({'username': user.username, 'nickname': user.nickname})

@app.route("/v1/permissions", methods=['POST'])
def create_permission_api1():
    user_id = request.json.get('userid')
    school_code = request.json.get('schoolcode')
    carrier = request.json.get('carrier')
    p = Permission(user_id = user_id, school_code = school_code, carrier = carrier)
    permissionService = PermissionService()
    p = permissionService.create_permission(p)
    return (jsonify({'user_id': p.user_id, 'school': p.school_code, 'carrier': p.carrier}), 201)

@app.route("/v1/permissions", methods=['GET'])
def read_permissions_api1():
    user = Auths.verify_auth_token(request)
    if user is not None:
        permission_service = PermissionService()
        temp = permission_service.get_permission(user.pkid)
        return jsonify({'result': temp, 'school': SCHOOL}), 200
    else:
        return abort(401, 'unauthorized')

@app.route("/v1/data/overview", methods=['GET'])
def get_data_overview_api1():
    order_service = OrderService()
    result = order_service.get_data_overview()
    return jsonify({'result': result}), 200

@app.route("/v1/data/statistic/<string:code>/<string:carr>", methods=['GET'])
def get_data_statistic_api1(code, carr):
    user = Auths.verify_auth_token(request)         # check token
    if user is not None:
        start = request.args.get("start")
        end = request.args.get("end")
        order_service = OrderService()
        if Auths.check_permission(user.pkid, code, carr):
            result = order_service.get_data_statistic(start, end, code, carr)
            log.info(result)
            return jsonify({'result': result}), 200
        else:
            abort(403, 'forbidden')
    else:
        abort(401, 'unauthorized')

########################################################################
#                               service
########################################################################
class OrderService(object):
    
    def get_orders(self):
        orders = Order.query.all()
        result = []
        for order in orders:
            result.append(order.to_dict())
        return result

    def get_data_statistic(self, start, end, code, carrier):
        params = {"start": start, "end": end}
        _param = ''
        if code != '00000':
            _param = 'AND o.school = :school '
            params["school"] = SCHOOL.get(code)
        if carrier != 'ALL':
            _param += 'AND carrier = :carrier '
            params["carrier"] = carrier
        order_dao = OrderDao()
        result = order_dao.get_data_statistic(params, _param)
        return result
        


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
                    GROUP BY P.school ) r 
                );
        '''
    CONDITION = "WHERE order_time = :order_time "
    SQL_3 = '''
            SELECT CAST(o.order_time AS varchar), o.school, SUM ( o.orders ) total 
            FROM v_order o
            WHERE
                o.order_time >= :start 
                AND o.order_time <= :end 
                {param}
            GROUP BY
                o.order_time,
                o.school
            ORDER BY
                o.order_time DESC;
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

    def get_data_statistic(self, params, cond):
        sql = self.SQL_3.format(param=cond)
        return db.session.execute(sql, params).fetchall()

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
#                               vo
########################################################################
class OrderVO(object):
    

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
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None     # token expired
        except BadSignature:
            return None     # invalid token
        user = User.query.get(data['pkid'])
        return user
    
    @staticmethod
    def check_permission(userid, code, carrier):
        perms = Permission.query.filter_by(user_id = userid, school_code = code, carrier = carrier).all()
        if len(perms) >= 1:
            return True
        else:
            return False

########################################################################
#                             Test Running
########################################################################
if __name__ == '__main__':
    # entry the application in development environment
    app.run()
