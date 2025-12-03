import random
from typing import Optional
from flask import current_app  # 核心：使用上下文获取配置，避免循环导入
from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


# 修复：删除 TeaOpenApiException 导入，改用通用异常捕获
# 若后续升级 SDK 后需精准捕获，可参考阿里云官方文档调整异常类路径

class AliyunSmsClient:
    """阿里云短信验证码发送客户端"""

    @staticmethod
    def _get_credential() -> CredentialClient:
        """从应用配置获取阿里云访问凭证"""
        access_key_id = current_app.config.get('ALIYUN_ACCESS_KEY_ID')
        access_key_secret = current_app.config.get('ALIYUN_ACCESS_KEY_SECRET')

        if not access_key_id or not access_key_secret:
            raise ValueError(
                "阿里云AccessKey配置缺失！请在环境变量或config.py中设置："
                "ALIYUN_ACCESS_KEY_ID 和 ALIYUN_ACCESS_KEY_SECRET"
            )

        return CredentialClient(
            config={
                "access_key_id": access_key_id,
                "access_key_secret": access_key_secret
            }
        )

    @staticmethod
    def create_sms_client() -> Dypnsapi20170525Client:
        """创建短信服务客户端"""
        credential = AliyunSmsClient._get_credential()

        region_id = current_app.config.get('REGION_ID', 'cn-beijing')
        endpoint = current_app.config.get('ENDPOINT', 'dypnsapi.aliyuncs.com')

        config = dypnsapi_20170525_models.Config(credential=credential)
        config.region_id = region_id
        config.endpoint = endpoint

        return Dypnsapi20170525Client(config)

    @staticmethod
    def generate_verify_code(length: int = 6) -> str:
        """生成指定长度的数字验证码（默认6位）"""
        if length < 4 or length > 8:
            raise ValueError("验证码长度必须在4-8位之间")
        return str(random.randint(10 ** (length - 1), 10 ** length - 1))

    @staticmethod
    def send_sms_verify_code(phone: str, code_length: int = 6) -> dict:
        """
        发送短信验证码

        Args:
            phone: 接收验证码的手机号（11位中国大陆手机号）
            code_length: 验证码长度（默认6位）

        Returns:
            dict: 发送结果，格式为 {"success": bool, "message": str, "code": str}
        """
        # 1. 验证手机号格式
        if not phone or len(phone) != 11 or not phone.startswith(("13", "14", "15", "16", "17", "18", "19")):
            return {
                "success": False,
                "message": "请输入有效的11位中国大陆手机号",
                "code": None
            }

        # 2. 生成验证码
        try:
            verify_code = AliyunSmsClient.generate_verify_code(code_length)
        except ValueError as e:
            return {
                "success": False,
                "message": f"验证码生成失败：{str(e)}",
                "code": None
            }

        # 3. 获取短信配置（签名、模板）
        sms_sign = current_app.config.get('SMS_SIGN')
        template_code = current_app.config.get('TEMPLATE_CODE')

        if not sms_sign or not template_code:
            return {
                "success": False,
                "message": "短信配置缺失！请设置 SMS_SIGN（签名）和 TEMPLATE_CODE（模板ID）",
                "code": None
            }

        # 4. 发送短信（调用阿里云SDK）
        try:
            sms_client = AliyunSmsClient.create_sms_client()

            request = dypnsapi_20170525_models.SendSmsVerifyCodeRequest(
                phone_number=phone,
                sign_name=sms_sign,
                template_code=template_code,
                template_param=f'{{"code":"{verify_code}","min":"5"}}'  # 5分钟有效期
            )

            response = sms_client.send_sms_verify_code_with_options(request, util_models.RuntimeOptions())

            # 校验阿里云响应状态（兼容不同SDK版本的响应格式）
            if hasattr(response, 'body'):
                body = response.body
                # 适配常见的响应格式（code为OK表示成功）
                if hasattr(body, 'code') and body.code == 'OK':
                    return {
                        "success": True,
                        "message": f"短信验证码已发送至{phone[:3]}****{phone[-4:]}，5分钟内有效",
                        "code": verify_code
                    }
                else:
                    # 提取错误信息（兼容不同响应字段）
                    err_msg = getattr(body, 'message', getattr(body, 'err_msg', '未知错误'))
                    return {
                        "success": False,
                        "message": f"短信发送失败：{err_msg}",
                        "code": None
                    }
            else:
                return {
                    "success": False,
                    "message": "短信发送失败：未获取到有效响应",
                    "code": None
                }

        # 修复：捕获阿里云SDK通用异常（替代TeaOpenApiException）
        except Exception as e:
            # 提取异常信息（兼容不同SDK版本的异常格式）
            err_msg = str(e)
            if hasattr(e, 'message'):
                err_msg = e.message
            elif hasattr(e, 'err_msg'):
                err_msg = e.err_msg
            return {
                "success": False,
                "message": f"阿里云短信服务异常：{err_msg}",
                "code": None
            }


# 对外暴露的简化接口（项目中直接调用此函数）
def send_verify_code(phone: str, code_length: int = 6) -> dict:
    """发送短信验证码（对外统一接口）"""
    return AliyunSmsClient.send_sms_verify_code(phone, code_length)


# 测试代码（需手动激活应用上下文，正常运行时无需执行）
if __name__ == "__main__":
    from app import create_app
    import os

    # 测试环境变量配置（实际部署时通过环境变量或config.py配置）
    os.environ['ALIYUN_ACCESS_KEY_ID'] = "你的阿里云AccessKeyID"
    os.environ['ALIYUN_ACCESS_KEY_SECRET'] = "你的阿里云AccessKeySecret"
    os.environ['SMS_SIGN'] = "你的短信签名"
    os.environ['TEMPLATE_CODE'] = "你的短信模板ID"

    app = create_app('development')
    with app.app_context():
        result = send_verify_code("13800138000")
        print("短信发送结果：", result)