from flask import Flask



app = Flask("__name__", instance_relative_config=True)


# 加载配置
app.config.from_object('config')
app.config.from_pyfile('config.py')


from .routes import *
