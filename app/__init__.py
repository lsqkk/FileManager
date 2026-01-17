# app/__init__.py
from flask import Flask
import os

def create_app():
    """创建Flask应用"""
    # 创建Flask应用，指定模板和静态文件夹
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # 配置
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB最大文件
    
    # 注册蓝图
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app