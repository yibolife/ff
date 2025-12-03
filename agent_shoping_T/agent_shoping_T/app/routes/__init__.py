# 导出所有蓝图，便于app初始化时注册
from app.routes.auth import auth_bp
from app.routes.agent import agent_bp
from app.routes.shopping import shopping_bp
from app.routes.binding import binding_bp