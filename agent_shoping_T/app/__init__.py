from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO  # 新增
from config import config
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
socketio = SocketIO()  # 新增SocketIO实例

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_name='default'):
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(base_dir, 'templates')

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=template_dir,
        static_folder=os.path.join(base_dir, 'static')
    )
    app.config.from_object(config[config_name])

    # 必须设置 SECRET_KEY
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-123456'

    # 初始化扩展
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    # 初始化SocketIO（关键：启用eventlet异步+跨域）
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")

    # 路径配置
    upload_dir = os.path.join(base_dir, app.config.get('UPLOAD_FOLDER', 'uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir

    # 打印路径日志
    print(f"=== 应用初始化路径验证 ===")
    print(f"项目根目录：{base_dir}")
    print(f"模板目录：{template_dir}")
    print(f"模板目录是否存在：{os.path.exists(template_dir)}")
    print(f"home.html是否存在：{os.path.exists(os.path.join(template_dir, 'home.html'))}")
    print(f"上传目录：{upload_dir}")
    print(f"==========================")

    # 注册蓝图（新增chat_bp）
    from app.routes.auth import auth_bp
    from app.routes.agent import agent_bp
    from app.routes.shopping import shopping_bp
    from app.routes.binding import binding_bp
    from app.routes.chat import chat_bp  # 新增聊天蓝图

    app.register_blueprint(auth_bp)
    app.register_blueprint(agent_bp, url_prefix='/agent')
    app.register_blueprint(shopping_bp, url_prefix='/shopping')
    app.register_blueprint(binding_bp, url_prefix='/binding')
    app.register_blueprint(chat_bp, url_prefix='/chat')  # 注册聊天蓝图

    # 用户加载器
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 创建数据库表
    with app.app_context():
        db.create_all()
        print("数据库表创建完成（若已存在则跳过）")

    # 首页路由
    @app.route('/')
    def home():
        from flask import render_template
        return render_template('home.html')

    return app