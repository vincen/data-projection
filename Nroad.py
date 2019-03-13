#!/usr/local/bin python3
# -*- coding: utf8 -*-

__author__ = 'vincen'

from flask import Flask, redirect, session, url_for, escape, request, jsonify
from flask_sqlalchemy import SQLAlchemy
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

########################################################################
#                           global varialbe
########################################################################
app = Flask(__name__)
# enable debug mode
app.debug = True
# flask session needs a secret key
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://cc3:cc3@localhost/cc3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# jsonify serialize chinese word, not original unicode
app.config["JSON_AS_ASCII"] = False
db = SQLAlchemy(app)


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
    # def __repr__(self):
    #     return '{"pkid":%s, "pid":%s}' % (self.pkid, self.pid)



########################################################################
#                                   utils
########################################################################
# def new_alchemy_encoder():
#     _visited_objs = []

#     class AlchemyEncoder(json.JSONEncoder):
#         def default(self, obj):
#             if isinstance(obj.__class__, DeclarativeMeta):
#                 # don't re-visit self
#                 if obj in _visited_objs:
#                     return None
#                 _visited_objs.append(obj)

#                 # an SQLAlchemy class
#                 fields = {}
#                 for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
#                     data = obj.__getattribute__(field)
#                     try:
#                         if isinstance(data, datetime):
#                             data = data.strftime('%Y-%m-%d %H:%M:%S')
#                         json.dumps(data)  # this will fail on non-encodable values, like other classes
#                         fields[field] = data
#                     except TypeError:
#                         fields[field] = None
#                 return fields

#             return json.JSONEncoder.default(self, obj)
#     return AlchemyEncoder



########################################################################
#                             Test Running
########################################################################
if __name__ == '__main__':
    # entry the application in development environment
    app.run()