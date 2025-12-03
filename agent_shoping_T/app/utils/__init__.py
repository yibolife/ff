# app/utils/__init__.py
"""
工具模块：存放项目通用工具函数/类（如短信验证、文件处理、数据格式化等）
"""

# 导出短信验证工具的核心函数（对外暴露简洁的导入方式）
from app.utils.sms import send_verify_code

# 若后续新增其他工具模块（如文件处理、数据验证），可在此统一导出
# 示例：
# from app.utils.file_handler import upload_file, delete_file
# from app.utils.data_validator import validate_email, validate_phone

# 定义 __all__（可选，规范导出内容，避免导入冗余）
__all__ = [
    'send_verify_code',  # 短信验证码发送函数
    # 后续新增工具可添加到这里
]