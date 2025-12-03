# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
# 导入表单类（与 auth_forms.py 中类名一致：RegistrationForm、LoginForm、AgentChoiceForm）
from app.forms.auth_forms import RegistrationForm, LoginForm, AgentChoiceForm
from app.models.user import User
from app import db
import redis
import os
import re
import random

# 初始化蓝图
auth_bp = Blueprint('auth', __name__)

# Redis/内存字典初始化（存储验证码）
try:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    print("Redis 连接成功，使用 Redis 存储验证码")
except Exception as e:
    print(f"Redis 连接失败：{e}，切换为内存字典存储验证码（开发环境）")
    redis_client = {}


# 测试模式：验证码生成函数（固定返回123456，无需阿里云短信）
def send_verify_code(phone: str, code_length: int = 6) -> dict:
    try:
        # 固定验证码为123456，忽略 code_length 参数（保持接口兼容性）
        verify_code = "123456"
        return {
            "success": True,
            "message": f"验证码已发送至 {phone[:3]}****{phone[-4:]}，5 分钟内有效",
            "code": verify_code
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"验证码生成失败：{str(e)[:20]}",
            "code": None
        }



# ------------------------------
# 登录路由
# ------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('您已登录，无需重复操作', 'info')
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()

        if user:
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('home'))
        else:
            flash('用户名不存在，请检查输入或注册账号', 'danger')

    return render_template('login.html', form=form)


# ------------------------------
# 注册路由（使用 RegistrationForm）
# ------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('您已登录，无需重复注册', 'info')
        return redirect(url_for('home'))

    form = RegistrationForm()  # 使用 RegistrationForm（与导入类名一致）
    if form.validate_on_submit():
        phone = form.phone.data.strip()
        input_code = form.verify_code.data.strip()
        redis_key = f"sms_verify_{phone}"

        # 获取存储的验证码
        stored_code = None
        if isinstance(redis_client, dict):
            stored_code = redis_client.get(redis_key)
        else:
            stored_code = redis_client.get(redis_key)

        # 验证码验证
        if not stored_code:
            flash('验证码已过期，请重新获取', 'danger')
            return render_template('register.html', form=form)
        if input_code != stored_code:
            flash('验证码输入错误，请重新输入', 'danger')
            return render_template('register.html', form=form)

        # 创建新用户
        new_user = User(
            username=form.username.data.strip(),
            phone=phone,
            is_agent=False  # 默认普通用户，可后续切换
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功！请登录', 'success')

            # 注册成功后删除验证码（避免重复使用）
            if isinstance(redis_client, dict):
                redis_client.pop(redis_key, None)
            else:
                redis_client.delete(redis_key)

            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败：{str(e)[:30]}', 'danger')

    return render_template('register.html', form=form)


# ------------------------------
# 发送验证码接口
# ------------------------------
@auth_bp.route('/send-verify-code', methods=['POST'])
def send_verify_code_api():
    try:
        data = request.get_json()
        print(f"前端请求验证码：{data}")

        if not data or 'phone' not in data:
            return jsonify({"success": False, "message": "请传入手机号"}), 400

        phone = data['phone'].strip()
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({"success": False, "message": "请输入有效的 11 位中国大陆手机号"}), 400

        # 防重复发送（60秒内同一手机号不可重复获取）
        redis_key = f"sms_verify_{phone}"
        if isinstance(redis_client, dict):
            if redis_key in redis_client:
                return jsonify({"success": False, "message": "验证码已发送，60 秒内请勿重复获取"}), 200
        else:
            if redis_client.exists(redis_key):
                return jsonify({"success": False, "message": "验证码已发送，60 秒内请勿重复获取"}), 200

        # 生成并发送验证码（此时固定返回123456）
        sms_result = send_verify_code(phone)
        if not sms_result["success"]:
            return jsonify({"success": False, "message": sms_result["message"]}), 200

        # 存储验证码（有效期5分钟）
        verify_code = sms_result["code"]
        print(f"生成的测试验证码：{verify_code}（手机号：{phone}）")  # 新增打印（此时会固定输出123456）
        if isinstance(redis_client, dict):
            redis_client[redis_key] = verify_code
        else:
            redis_client.setex(redis_key, 300, verify_code)

        return jsonify({"success": True, "message": sms_result["message"]}), 200

    except Exception as e:
        error_msg = f"服务器错误：{str(e)[:30]}"
        print(f"发送验证码接口报错：{error_msg}")
        return jsonify({"success": False, "message": error_msg}), 500

# ------------------------------
# 身份选择路由（使用 AgentChoiceForm）
# ------------------------------
@auth_bp.route('/choose-identity', methods=['GET', 'POST'])
@login_required  # 仅登录用户可访问
def choose_identity():
    form = AgentChoiceForm()  # 使用补充的 AgentChoiceForm
    if form.validate_on_submit():
        # 获取用户选择的身份类型
        identity_type = form.identity_type.data
        current_user.is_agent = (identity_type == 'agent')  # True=代购用户，False=普通用户

        try:
            db.session.commit()
            flash(f'身份已成功设置为【{"代购用户" if identity_type == "agent" else "普通用户"}】', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'身份设置失败：{str(e)[:20]}', 'danger')

    # 渲染身份选择模板（需创建 templates/choose_identity.html）
    return render_template('choose_identity.html', form=form)


# ------------------------------
# 退出登录路由
# ------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'info')
    return redirect(url_for('auth.login'))