import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')  # 优先从环境变量获取

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', f'sqlite:///{os.path.join(BASE_DIR, "site67.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传16MB

    # 短信配置（阿里云）
    ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID', '')
    ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET', '')
    SMS_SIGN = os.getenv('SMS_SIGN', '云清科技验证服务')
    TEMPLATE_CODE = os.getenv('TEMPLATE_CODE', '100001')
    REGION_ID = 'cn-beijing'
    ENDPOINT = 'dypnsapi.aliyuncs.com'


# 开发环境配置（可扩展生产/测试环境）
class DevelopmentConfig(Config):
    DEBUG = True


# 生产环境配置（示例）
class ProductionConfig(Config):
    DEBUG = False
    # 生产环境建议使用更复杂的SECRET_KEY，通过环境变量传入


# 配置映射（便于切换环境）
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}