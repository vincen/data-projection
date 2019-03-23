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
# enable debug mode
app.debug = True
# a secret key using by token
app.config['SECRET_KEY'] = 'nroad is a good company'
# database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://cc3:cc3@localhost/cc3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# jsonify serialize chinese word, not original unicode
app.config["JSON_AS_ASCII"] = False
# loggin config
dictConfig({
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

########################################################################
#                                   api
########################################################################
@app.route('/now', methods=['GET'])
def current_time():
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return jsonify({'now': now}), 200

@app.route('/v1/login', methods=['POST'])
def login():
    secret_iden = request.json.get('iden')
    origin_iden = base64.urlsafe_b64decode(secret_iden)
    up = json.loads(origin_iden)
    up_username = up.get('username').strip()
    log.info(up_username + ' signed in')
    up_password = up.get('password').strip()
    userService = UserService()
    user = userService.find_user(up_username)
    if user.verify_password(up_password):
        token = user.generate_auth_token()
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

# @app.route("/v1/users", methods=['PUT'])
# def update_user_api1():
#     username = request.json.get('username')
#     password = request.json.get('password')
#     userService = UserService()
#     user = userService.update_password(username, password)
#     return jsonify({'result': 'success'}), 200

@app.route("/v1/users/<int:pkid>", methods=['GET'])
def read_user_api1(pkid):
    user = User.query.get(pkid)
    if not user:
        abort(400)
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

@app.route("/v1/yesterday/new", methods=['GET'])
def new_orders_yesterday_api1():
    order_service = OrderService()
    temp = order_service.get_new_orders_in_yesterday()
    return jsonify({'result': temp[0]}), 200

@app.route("/v1/yesterday/top1", methods=['GET'])
def top1_orders_yesterday_api1():
    order_service = OrderService()
    temp = order_service.get_top1_orders_in_yesterday()
    result = {'school': temp[0], 'count': temp[1]}
    return jsonify({'result': result}), 200

@app.route("/v1/total/all", methods=['GET'])
def all_orders_count_api1():
    order_service = OrderService()
    temp = order_service.get_total_orders_count()
    return jsonify({'result': temp[0]}), 200

@app.route("/v1/total/top1", methods=['GET'])
def top1_orders_count_api1():
    order_service = OrderService()
    temp = order_service.get_top1_orders_count()
    result = {'school': temp[0], 'count': temp[1]}
    return jsonify({'result': result}), 200

@app.route("/v1/data/overview", methods=['GET'])
def get_data_overview_api1():
    order_service = OrderService()
    result = order_service.get_data_overview()
    return jsonify({'result': result}), 200


@app.route("/v1/daily/detail", methods=['GET'])
def daily_detail_count_api1():
    order_service = OrderService()
    # temp = order_service.get_daily_detail_count()

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

    def get_daily_detail_count(self, start_date, end_date, school_code):
        sql = '''
            SELECT
                o.order_time,
                o.school,
                r.carrier,
                CAST(SUM ( COUNT * CASE WHEN is_boss THEN percentage ELSE 1 END ) AS INT) AS orders 
            FROM
                order_generalize o, product r 
            WHERE
                o.pid = r.pid 
                AND order_time >= :start 
                AND order_time <= :end
                AND o.school = :school 
                AND carrier = :carrier 
            GROUP BY
                o.order_time,
                o.school,
                r.carrier 
            ORDER BY
                o.order_time DESC;
        '''
        return db.session.execute(sql, {"start": start_date, "end": end_date, "school": school_code}).fetchall()

    def get_data_overview(self):
        order_dao = OrderDao()
        temp1 = order_dao.get_new_orders_in_yesterday()
        new_orders_in_yesterday = temp1[0]
        log.info(temp1)
        temp2 = order_dao.get_top1_orders_in_yesterday()
        log.info(temp2)
        top1_orders_in_yesterday = {'school': temp2[0], 'count': temp2[1]}
        temp3 = order_dao.get_total_orders_count()
        total_orders_count = temp3[0]
        log.info(temp3)
        temp4 = order_dao.get_top1_orders_count()
        top1_orders_count = {'school': temp4[0], 'count': temp4[1]}
        log.info(temp4)
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

    # def update_password(self, username, password):
    #     old_user = User.query.filter_by(username = username)
    #     new_user = User(username = old_user.)
    #     user.hash_password(password)
    #     db.session.update(user)
    #     db.session.commit()
    #     return user


class PermissionService(object):
    def create_permission(self, permission):
        db.session.add(permission)
        db.session.commit()
        return permission


########################################################################
#                                dao
########################################################################
class OrderDao(object):
    def __init__(self):
        self.yesterday = Utils().get_yesterday().strftime("%Y-%m-%d")

    def get_new_orders_in_yesterday(self):
        sql = "SELECT sum(t.orders) FROM v_order t WHERE t.order_time = :order_time"
        return db.session.execute(sql, {"order_time": self.yesterday}).fetchone()

    def get_top1_orders_in_yesterday(self):
        sql = '''
            SELECT t.school, SUM ( t.orders ) 
            FROM v_order t 
            WHERE t.order_time = :order_time 
            GROUP BY t.school 
            HAVING
                SUM ( t.orders ) = (
                SELECT MAX( r.topcount ) 
                FROM ( 
                    SELECT P.school sch, SUM ( P.orders ) topcount 
                    FROM v_order P 
                    WHERE P.order_time = :order_time 
                    GROUP BY P.school ) r 
                );
        '''
        return db.session.execute(sql, {"order_time": self.yesterday}).fetchone()

        # results = None
        # connection = db.engine.raw_connection()
        # try:
        #     cursor = connection.cursor()
        #     cursor.callproc("top1_orders_in_yesterday", [self.yesterday])
        #     results = list(cursor.fetchall())
        #     cursor.close()
        #     connection.commit()
        # finally:
        #     connection.close()
        # return resutls

        # resutls = db.session.execute("SELECT top1_orders_in_yesterday('2019-03-20')").fetchall()
        # log.info(results)
        # return results


    def get_total_orders_count(self):
        sql = "SELECT sum(t.orders) FROM v_order t"
        return db.session.execute(sql).fetchone()

    def get_top1_orders_count(self):
        sql = '''
            SELECT t.school, SUM ( t.orders ) 
            FROM v_order t 
            GROUP BY t.school 
            HAVING
                SUM ( t.orders ) = (
                SELECT MAX( r.topcount ) 
                FROM ( 
                    SELECT P.school sch, SUM ( P.orders ) topcount 
                    FROM v_order P 
                    GROUP BY P.school ) r 
                );
        '''
        return db.session.execute(sql).fetchone()




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
        data = data.strftime('%Y-%m-%d')
        dict["order_time"] = data
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
    
    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({'pkid': self.pkid})
    
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None     # token expired
        except BadSignature:
            return None     # invalid token
        user = User.query.get(data['pkid'])
        return user


class Permission(db.Model):
    __tablename__ = 't_permission'

    pkid = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    school_code = db.Column(db.String(255))
    carrier = db.Column(db.String(255))

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
#                             Test Running
########################################################################
if __name__ == '__main__':
    # entry the application in development environment
    app.run()
