#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# 创建app
def create_app():
    app = Flask(__name__)

    # 设置连接数据库的URL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Lenin1918@47.106.239.211:3306/fund'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    # 查询时会显示原始SQL语句
    app.config['SQLALCHEMY_ECHO'] = True
    app.db = SQLAlchemy(app)

    return app

