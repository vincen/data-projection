#!/usr/local/bin python3
# -*- coding: utf8 -*-

__author__ = 'vincen'

import datetime
import time
import requests
import json
import psycopg2


class PullData(object):
    """
    从 ELK 中拉去数据
    """

    URL = 'http://54.223.96.189:9200/_search'
    HEADERS = {'Content-Type': 'application/json'}
    CONFIG = 'request.json'

    def get_today(self):
        """
        获取当天的日期
        :return:
        """
        return datetime.date.today()

    def get_yesterday(self, delta):
        """
        获取昨天的日期
        :return: 日期，格式：1970-01-01
        """
        yesterday = self.get_today() - datetime.timedelta(days=delta)
        return yesterday

    def get_epoch_millis(self, param):
        """
        获得一天开始与结束两个时间戳，单位毫秒
        :param param: 一个日期，格式：1970-01-01
        :return:
        """
        after = param + datetime.timedelta(days=1)
        start_epoch_millis = int(
            time.mktime(
                time.strptime(
                    str(param),
                    "%Y-%m-%d")) *
            1000)
        end_epoch_millis = int(
            time.mktime(
                time.strptime(
                    str(after),
                    "%Y-%m-%d")) * 1000) - 1

        return start_epoch_millis, end_epoch_millis

    def read_config(self):
        # 读取配置文件
        with open(self.CONFIG, 'r') as f:
            data = json.load(f)

        return data

    def request_data(self, param):
        """
        请求数据
        :param param: 开始与结束两个时间戳
        :return:
        """
        # 获得请求参数结构
        request_body = self.read_config().get('request')
        # 构建请求参数
        request_body['query']['bool']['must'][1]['range']['orderCreateAt']['gte'] = param[0]
        request_body['query']['bool']['must'][1]['range']['orderCreateAt']['lte'] = param[1]
        request_body = json.dumps(request_body)
        # 发起请求
        response = requests.post(
            url=self.URL,
            data=request_body,
            headers=self.HEADERS)

        return response.content.decode("utf-8")

    def parse_data(self, data, param2):
        """
        解析数据
        :return:
        """
        raw = json.loads(data)
        al = raw['aggregations']['6']['buckets']
        result = list()
        for i in range(len(al)):
            c = al[i]
            prices = c['3']['buckets'][0]['5']['buckets'][0]['4']['buckets']

            for j in range(len(prices)):
                price = prices[j]['key']
                count = prices[j]['doc_count']

                # pid, product_name, school, price, count
                psp = {
                    "pid" : c['key'],
                    "pn" : c['3']['buckets'][0]['key'],
                    "school" : c['3']['buckets'][0]['5']['buckets'][0]['key'],
                    "price" : price,
                    "count" : count,
                    "order_time" : param2
                }
                result.append(psp)

        return result
 

class PushData(object):
    
    def batch_insert(self, data):
        # postgres = PostgresUtil()
        # ini = IniUtil('server.ini')
        # db_config = ini.get_section_to_map('development-db')

        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='cc3',
            password='cc3',
            database='cc3')
        cur = conn.cursor()
        try:
            cur.executemany('''INSERT INTO order_generalize (pid, product_name, school, price, count, order_time) VALUES (%(pid)s, %(pn)s, %(school)s, %(price)s, %(count)s, %(order_time)s)''', data)
            conn.commit()
        except Exception as e:
            print("it's a bug")
        finally:
            conn.close()



def main():
    rd = PullData()
    ed = PushData()

    r1 = rd.get_yesterday(1)
    print(r1)
    r3 = rd.get_epoch_millis(r1)
    print(r3)
    r4 = rd.request_data(r3)
    # print(r4)
    r5 = rd.parse_data(r4, r1)
    # print(r5)


    ed.batch_insert(r5)



main()
