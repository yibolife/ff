from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect  # 导入 CSRFProtect 扩展
from config import config
import os

# 初始化扩展（新增 CSRFProtect）
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()  # 初始化 CSRF 保护扩展
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

    # 必须设置 SECRET_KEY（CSRF 保护依赖此配置）
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-123456'  # 开发环境临时密钥，生产环境需替换为随机字符串

    # 初始化 CSRF 保护（关联 Flask 应用）
    csrf.init_app(app)  # 关键：启用 CSRF 保护

    # 2. 再拼接上传目录（此时app.config已加载，可获取UPLOAD_FOLDER配置）
    upload_dir = os.path.join(base_dir, app.config.get('UPLOAD_FOLDER', 'uploads'))

    # 核心修改2：打印路径日志（用于验证是否正确指向模板目录）
    print(f"=== 应用初始化路径验证 ===")
    print(f"项目根目录：{base_dir}")
    print(f"模板目录：{template_dir}")
    print(f"模板目录是否存在：{os.path.exists(template_dir)}")
    print(f"home.html是否存在：{os.path.exists(os.path.join(template_dir, 'home.html'))}")
    print(f"上传目录：{upload_dir}")
    print(f"==========================")

    # 创建上传目录（使用绝对路径，避免相对路径混乱）
    os.makedirs(upload_dir, exist_ok=True)
    # 更新配置中的UPLOAD_FOLDER为绝对路径（确保后续文件操作路径正确）
    app.config['UPLOAD_FOLDER'] = upload_dir

    # 初始化扩展（关联Flask应用）
    db.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图（路由拆分到不同模块，添加前缀避免冲突）
    from app.routes.auth import auth_bp  # 登录/注册/身份切换路由（无前缀）
    from app.routes.agent import agent_bp  # 代购用户相关路由（前缀/agent）
    from app.routes.shopping import shopping_bp  # 普通用户相关路由（前缀/shopping）
    from app.routes.binding import binding_bp  # 绑定相关路由（前缀/binding）

    app.register_blueprint(auth_bp)
    app.register_blueprint(agent_bp, url_prefix='/agent')
    app.register_blueprint(shopping_bp, url_prefix='/shopping')
    app.register_blueprint(binding_bp, url_prefix='/binding')

    # 用户加载器（Flask-Login必需，用于从用户ID加载用户对象）
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # 从数据库查询用户

    # 创建数据库表（仅在应用上下文内执行）
    with app.app_context():
        db.create_all()  # 自动创建所有未存在的表
        print("数据库表创建完成（若已存在则跳过）")

    # 首页路由（根路径 /，返回home.html模板）
    @app.route('/')
    def home():
        from flask import render_template
        return render_template('home.html')  # 从指定的template_dir查找模板

    return app

# 禁止在这里导入路由/工具模块（避免循环导入）