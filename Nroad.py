#!/usr/local/bin python3
# -*- coding: utf8 -*-

__author__ = 'vincen'

from flask import Flask, redirect, url_for, escape, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import datetime
from crypt import crypt
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

########################################################################
#                           global varialbe
########################################################################
app = Flask(__name__)
# enable debug mode
app.debug = True
# flask session needs a secret key
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# a secret key using by token
app.config['SECRET_KEY'] = 'nroad is a good company'
# database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://cc3:cc3@localhost/cc3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# jsonify serialize chinese word, not original unicode
app.config["JSON_AS_ASCII"] = False
db = SQLAlchemy(app)
salt = 'wangxing'

SCHOOL = {
        '10704': '西安科技大学',
        '12712': '西安欧亚学院',
        '11664': '西安邮电大学',
        '10716': '陕西中医药大学',
        '10722': '咸阳师范学院',
        '10698': '西安交通大学',
        '10697': '西北大学',
        '0820' : 0
    }


########################################################################
#                                   api
########################################################################
@app.route('/v1')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not Logged in'

@app.route("/v1/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''

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
def create_user():
    username = request.json.get('username')
    nickname = request.json.get('nickname')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)      # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)      # existing user
    user = User(username = username, nickname = nickname)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('read_user', pkid=user.pkid, _external=True)})

@app.route("/v1/users/<int:pkid>", methods=['GET'])
def read_user(pkid):
    user = User.query.get(pkid)
    if not user:
        abort(400)
    return jsonify({'username': user.username, 'nickname': user.nickname})


@app.route("/v1/yesterday/new", methods=['GET'])
def new_orders_yesterday_api1():
    """
    new orders in yesterday
    """
    order_service = OrderService()
    temp = order_service.get_new_orders_in_yesterday()
    return jsonify({'result': temp[0]}), 200

@app.route("/v1/yesterday/top1", methods=['GET'])
def top1_orders_yesterday_api1():
    """
    top 1 in yesterday
    """
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

@app.route("/v1/daily/detail", methods=['GET'])
def daily_detail_count_api1():
    psss

########################################################################
#                               service
########################################################################
class OrderService(object):

    def __init__(self):
        self.yesterday = Utils().get_yesterday().strftime("%Y-%m-%d")
    
    def get_orders(self):
        orders = Order.query.all()
        result = []
        for order in orders:
            result.append(order.to_dict())
        return result
    
    def get_new_orders_in_yesterday(self):
        
        # sql = "SELECT sum(t.count) FROM order_generalize t WHERE t.order_time = :order_time"
        # result = db.session.execute(sql, {"order_time": yesterday}).fetchone()
        return db.session.query(db.func.sum(Order.count)).filter(Order.order_time == self.yesterday).one()
        # return result
    
    def get_top1_orders_in_yesterday(self):
        sql = '''
            SELECT t.school, SUM ( t.count ) 
            FROM order_generalize t 
            WHERE t.order_time = :order_time 
            GROUP BY t.school 
            HAVING
                SUM ( t.count ) = (
                SELECT MAX( r.topcount ) 
                FROM ( 
                    SELECT P.school sch, SUM ( P.count ) topcount 
                    FROM order_generalize P 
                    WHERE P.order_time = :order_time 
                    GROUP BY P.school ) r 
                );
        '''
        return db.session.execute(sql, {"order_time": self.yesterday}).fetchone()

    def get_total_orders_count(self):
        return db.session.query(db.func.sum(Order.count)).one()
    
    def get_top1_orders_count(self):
        sql = '''
            SELECT t.school, SUM ( t.count ) 
            FROM order_generalize t 
            GROUP BY t.school 
            HAVING
                SUM ( t.count ) = (
                SELECT MAX( r.topcount ) 
                FROM ( 
                    SELECT P.school sch, SUM ( P.count ) topcount 
                    FROM order_generalize P 
                    GROUP BY P.school ) r 
                );
        '''
        return db.session.execute(sql).fetchone()

    def get_daily_detail_count(self):
        pass


########################################################################
#                           dao
########################################################################
# class OrderDao(object):
    # def get


########################################################################
#                               domain
########################################################################
class Order(db.Model):

    __tablename__ = 'order_generalize'

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

    __tablename__ = 'product'
    
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
    __tablename__ = 'user'

    pkid = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(255))
    nickname = db.Column(db.String(255))
    password = db.Column(db.String(255))

    def hash_password(self, password):
        self.password = crypt(password, salt=salt)

    def verify_password(self, password):
        p2 = crypt(password, salt=salt)
        if p2 == self.password:
            return True
        else:
            return False
    
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