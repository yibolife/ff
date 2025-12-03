your_project/
├── app/                      # 核心应用目录（所有业务代码放在这里）
│   ├── __init__.py           # 应用初始化（Flask实例、扩展、蓝图注册）
│   ├── models/               # 数据库模型模块
│   │   ├── __init__.py
│   │   ├── user.py           # User模型
│   │   ├── agent.py          # AgentInfo、ContactedTrip模型
│   │   ├── shopping.py       # ShoppingInfo、ShoppingCircle模型
│   │   └── binding.py        # Binding模型
│   ├── forms/                # 表单模块（按功能拆分）
│   │   ├── __init__.py
│   │   ├── auth_forms.py     # 注册、登录、身份选择表单
│   │   ├── agent_forms.py    # 代购行程相关表单
│   │   └── shopping_forms.py # 商品、购物圈相关表单
│   ├── routes/               # 路由模块（按功能拆分蓝图）
│   │   ├── __init__.py
│   │   ├── auth.py           # 认证路由（注册、登录、退出、choice）
│   │   ├── agent.py          # 代购相关路由
│   │   ├── shopping.py       # 购物相关路由
│   │   └── binding.py        # 绑定关系相关路由
│   ├── utils/                # 工具模块
│   │   ├── __init__.py
│   │   └── sms.py            # 短信验证码工具
│   └── static/               # 静态文件（自动创建uploads目录）
│       └── uploads/          # 商品图片上传目录
├── templates/                # 模板文件（保持原有结构）
│   ├── home.html
│   ├── register.html
│   ├── login.html             ok
│   ├── choice.html
│   ├── agent_info.html
│   ├── shopping_info.html
│   ├── shopping_circle.html
│   ├── agent_circle.html
│   ├── binding_detail.html
│   ├── contacted_trips.html
│   ├── purchased_products.html
│   ├── agent_list.html
│   └── chat.html
├── config.py                 # 配置文件（集中管理所有配置）
├── requirements.txt          # 依赖包清单
└── run.py                    # 项目启动入口

# 升级阿里云 SDK 依赖
pip install --upgrade alibabacloud-tea-openapi alibabacloud-dypnsapi20170525 alibabacloud-credentials
