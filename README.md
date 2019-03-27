# 配置说明

## 数据库

见 initdb.sql 。

# 代码说明

## job.py

同步数据使用。定时从 ELK 中获取数据，同步到 postgresql 数据库中。

## Nroad.py

所有代码。

## 常量说明

```python
CARRIER = {CTCC: '中国电信',  CMCC: '中国移动',   CUCC: '中国联通',   ALL: 'all of carriers' }
```

# API

## 1 获取服务器时间

### 1.1 request method

> /now			GET

### 1.2 response value

```json
{
  "now": "2019-03-26 10:41:00"
}
```

## 2 登录

### 2.1 request method

> /v1/login			POST

### 2.2 request parameters

```json
to be encoded:
{
    "username": "gaox@nroad.com.cn",
    "password": "vincen"
}

encoded by base64 safe mode:
{"iden":"ewogICAgIW1lIjJvYWQuY29tLmNuIiwKICAgIW5jZW4iCn0="}
```

### 2.3 response value

```json
{
  "token": "eyJhbGciOiJIUzUxMiIsImlhdCI6MTU1MzQ0Nzc1OSwiZXhwIjoxNTUzNDQ4MzU5fQ.eyJwa2lkIjoxfQ.QJfJPfVi53cP5S928lsMbc-7bSr-pHpjuCZhWow64R_f2t3ap13HP5pdRhkNAZaMpF_6Y1671Y3jMwUMYemDBA"
}
```

### 2.4 header

```python
Authorization eyJhbGciOiJIUzUxMiIsImlhdCI6MTU1MzQ0Nzc1OSwiZXhwIjoxNTUzNDQ4MzU5fQ.eyJwa2lkIjoxfQ.QJfJPfVi53cP5S928lsMbc-7bSr-pHpjuCZhWow64R_f2t3ap13HP5pdRhkNAZaMpF_6Y1671Y3jMwUMYemDBA

```

## 3 获取权限

### 3.1 request method

> /v1/permissions			GET

### 3.2 response value

```json
{
  "result": [
    {
      "carrier": "ALL", 
      "pkid": 1, 
      "school": "ALL", 
      "school_code": "00000", 
      "user_id": 1
    }
  ], 
  "school": {
    "00000": "ALL", 
    "10697": "西北大学", 
    "10698": "西安交通大学", 
    "10704": "西安科技大学", 
    "10716": "陕西中医药大学", 
    "10722": "咸阳师范学院", 
    "11664": "西安邮电大学", 
    "12712": "西安欧亚学院"
  }
}
```

## 4 数据概览

### 4.1 request method

> /v1/data/overview			GET

### 4.2 response value

```json
{
  "result": {
    "new_orders_in_yesterday": 1403, 
    "top1_orders_count": {
      "count": 12425, 
      "school": "西安欧亚学院"
    }, 
    "top1_orders_in_yesterday": {
      "count": 1073, 
      "school": "西安欧亚学院"
    }, 
    "total_orders_count": 40567
  }
}
```

## 5 数据统计

### 5.1 request method

> /v1/data/statistic			GET

### 5.2 request parameters

| parameters  | vlaue      | optional |
| ----------- | ---------- | -------- |
| school_code | 10697      | yes      |
| start       | 2019-02-15 | no       |
| end         | 2019-03-25 | no       |



### 5.2 response value

