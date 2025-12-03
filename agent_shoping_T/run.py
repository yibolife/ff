from app import create_app

# 创建app实例（默认开发环境）
app = create_app(config_name='development')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)