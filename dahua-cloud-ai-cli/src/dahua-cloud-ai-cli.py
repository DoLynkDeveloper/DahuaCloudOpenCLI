#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大华云大模型推理套件 CLI Tool
Generated from Dahua Cloud API documentation

USAGE:
  dahua-cloud <command> <subcommand> [flags]

COMMANDS:
  image       图片理解相关 API
  text        文本理解相关 API
  video       视频理解相关 API
  audio       音频理解相关 API
  auth        认证相关命令
  doctor      诊断环境配置

FLAGS:
  -h, --help      显示帮助信息
  -v, --version   显示版本信息
  --json          以 JSON 格式输出结果
  --no-json       以人类可读格式输出结果（默认）

ENVIRONMENT VARIABLES:
  DAHUA_CLOUD_PRODUCT_ID    AppID from Dahua Cloud
  DAHUA_CLOUD_AK            Access Key from Dahua Cloud
  DAHUA_CLOUD_SK            Secret Key from Dahua Cloud

EXAMPLES:
  $ dahua-cloud image analysis --picture-url "https://xxx.jpg" --prompt "描述图片内容"
  $ dahua-cloud image multi-analysis --picture-urls "https://a.jpg,https://b.jpg" --prompt "比较两张图片"
  $ dahua-cloud image summary --picture-url "https://xxx.jpg" --keyword "安全帽"
  $ dahua-cloud image compare --base-url "https://base.jpg" --picture-urls "https://cmp1.jpg,https://cmp2.jpg" --prompt "比对图片"
  $ dahua-cloud text analysis --text "待分析文本" --prompt "提取关键信息"
  $ dahua-cloud text tts --text "你好，世界"
  $ dahua-cloud video analysis --video-url "https://xxx.mp4" --prompt "分析视频内容"
  $ dahua-cloud audio transcribe --audio-urls "https://xxx.mp3"

For more information, visit: https://open.cloud-dahua.com/
"""

__version__ = "1.0.0"

import argparse
import hashlib
import hmac
import json
import os
import platform
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import requests

# =============================================================================
# 常量定义
# =============================================================================

DEFAULT_API_BASE_URL = 'https://open.cloud-dahua.com/'

# =============================================================================
# PowerShell 检测与提示
# =============================================================================

def is_running_in_powershell() -> bool:
    """
    检测当前是否在 PowerShell 环境中运行
    
    Returns:
        bool: 如果在 PowerShell 中运行返回 True，否则返回 False
    """
    # 检查 PSModulePath 环境变量（PowerShell 特有）
    if 'PSModulePath' not in os.environ:
        return False
    
    # 额外检查：确保不是 CMD 或其他 shell
    # PowerShell 会设置 PSModulePath，但 CMD 不会
    ps_module_path = os.environ.get('PSModulePath', '')
    return len(ps_module_path) > 0 and 'PowerShell' in ps_module_path


def get_powershell_url_warning() -> str:
    """
    获取 PowerShell URL 参数异常的帮助提示
    
    Returns:
        str: 格式化的帮助提示信息
    """
    return """
⚠️  PowerShell 参数解析提示

如果 URL 中包含 & 符号，PowerShell 会将其解析为命令分隔符，
导致参数被截断。

解决方法：在命令中添加 --% 停止解析操作符

示例：
  dahua-cloud --% image analysis "https://xxx?a=1&b=2" "prompt"

或者使用引号包裹整个命令：
  dahua-cloud image analysis `"https://xxx?a=1&b=2`" "prompt"
"""


def check_and_print_powershell_warning():
    """
    检查是否在 PowerShell 中运行，如果是则打印 URL 参数警告
    """
    if platform.system() == 'Windows' and is_running_in_powershell():
        print(get_powershell_url_warning(), file=sys.stderr)
TOKEN_EXPIRY_SECONDS = 3600

# API Endpoints
API_AUTH_TOKEN = '/open-api/api-base/auth/getAppAccessToken'

# 图片理解
API_IMAGE_ANALYSIS = '/open-api/api-ai/largeModelDetect/imageAnalysis'
API_MULTI_IMAGE_ANALYSIS = '/open-api/api-ai/largeModelDetect/multiImageAnalysis'
API_IMAGE_SUMMARY = '/open-api/api-ai/largeModelDetect/extractPicSummaryByKeyword'
API_IMAGE_COMPARE = '/open-api/api-ai/largeModelDetect/contrastImage'

# 文本理解
API_TEXT_ANALYSIS = '/open-api/api-ai/largeModelDetect/textAnalysis'
API_TEXT_TO_AUDIO = '/open-api/api-ai/largeModelDetect/textToAudio'

# 视频理解
API_VIDEO_ANALYSIS = '/open-api/api-ai/largeModelDetect/videoAnalysis'

# 音频理解
API_AUDIO_TO_TEXT = '/open-api/api-ai/largeModelDetect/audioToText'

# HTTP Timeouts (seconds)
TIMEOUT_AUTH = 60
TIMEOUT_API = 120

# Environment Variable Names
ENV_CLOUD_ID = 'DAHUA_CLOUD_PRODUCT_ID'
ENV_CLOUD_AK = 'DAHUA_CLOUD_AK'
ENV_CLOUD_SK = 'DAHUA_CLOUD_SK'


# =============================================================================
# 认证相关函数
# =============================================================================

def get_token_sign(access_key: str, timestamp: str, nonce: str, secret: str) -> str:
    """
    获取 Token 时的签名计算
    签名因子: access_key + timestamp + nonce
    """
    auth_factor = f'{access_key}{timestamp}{nonce}'
    signature = hmac.new(
        secret.encode('utf-8'),
        auth_factor.encode('utf-8'),
        hashlib.sha512
    ).hexdigest().upper()
    return signature


def business_api_sign(access_key: str, app_access_token: str, timestamp: str, nonce: str, secret: str) -> str:
    """
    业务 API 的签名计算
    签名因子: access_key + app_access_token + timestamp + nonce
    """
    auth_factor = f'{access_key}{app_access_token}{timestamp}{nonce}'
    signature = hmac.new(
        secret.encode('utf-8'),
        auth_factor.encode('utf-8'),
        hashlib.sha512
    ).hexdigest().upper()
    return signature


# =============================================================================
# API 客户端类
# =============================================================================

class DahuaApiClient:
    """大华云 API 客户端"""

    def __init__(self, app_id: str, access_key: str, secret_key: str,
                 api_base_url: str = DEFAULT_API_BASE_URL):
        self.config = {
            'app_id': app_id,
            'access_key': access_key,
            'secret_key': secret_key,
            'api_base_url': api_base_url.rstrip('/')
        }
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.token_expiry: int = 0

    def _generate_headers(self, is_auth: bool = False) -> Dict[str, str]:
        """生成请求头"""
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())
        trace_id = f"tid-{int(time.time())}"

        if is_auth:
            signature = get_token_sign(
                self.config['access_key'],
                timestamp,
                nonce,
                self.config['secret_key']
            )
            return {
                'Content-Type': 'application/json',
                'AccessKey': self.config['access_key'],
                'Timestamp': timestamp,
                'Nonce': nonce,
                'Sign': signature,
                'ProductId': self.config['app_id'],
                'X-TraceId-Header': trace_id,
                'Version': 'V1',
                'Sign-Type': 'simple'
            }
        else:
            if not self.access_token:
                raise ValueError("Access token not available. Call get_app_access_token() first.")
            signature = business_api_sign(
                self.config['access_key'],
                self.access_token,
                timestamp,
                nonce,
                self.config['secret_key']
            )
            return {
                'Content-Type': 'application/json',
                'AccessKey': self.config['access_key'],
                'Timestamp': timestamp,
                'Nonce': nonce,
                'Sign': signature,
                'ProductId': self.config['app_id'],
                'X-TraceId-Header': trace_id,
                'Version': 'V1',
                'Sign-Type': 'simple',
                'AppAccessToken': self.access_token
            }

    def get_app_access_token(self) -> Optional[str]:
        """获取 AppAccessToken"""
        current_time = int(time.time())
        if self.access_token and current_time < self.token_expiry:
            return self.access_token

        url = f"{self.config['api_base_url']}{API_AUTH_TOKEN}"
        headers = self._generate_headers(is_auth=True)
        payload = {
            'accessKey': self.config['access_key'],
            'productId': self.config['app_id']
        }

        try:
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=TIMEOUT_AUTH
            )
            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                self.access_token = result['data']['appAccessToken']
                expires_in = result['data'].get('expiresIn', TOKEN_EXPIRY_SECONDS)
                self.token_expiry = current_time + expires_in - 60
                return self.access_token
            else:
                raise ValueError(f"Failed to get access token: {result.get('msg')}")
        except requests.RequestException as e:
            raise ValueError(f"Request failed: {e}")

    def call_api(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """调用具体 API"""
        self.get_app_access_token()
        url = f"{self.config['api_base_url']}{endpoint}"
        headers = self._generate_headers(is_auth=False)

        response = self.session.post(
            url,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_API
        )
        response.raise_for_status()
        return response.json()


# =============================================================================
# API 调用函数 - 图片理解
# =============================================================================

def image_analysis(client: DahuaApiClient, picture_url: str, prompt: str) -> Dict[str, Any]:
    """单图分析"""
    payload = {
        'pictureUrl': picture_url,
        'prompt': prompt
    }
    return client.call_api(API_IMAGE_ANALYSIS, payload)


def multi_image_analysis(client: DahuaApiClient, picture_urls: List[str], prompt: str) -> Dict[str, Any]:
    """多图分析"""
    payload = {
        'pictureUrls': picture_urls,
        'prompt': prompt
    }
    return client.call_api(API_MULTI_IMAGE_ANALYSIS, payload)


def image_summary(client: DahuaApiClient, picture_url: str, keyword: str) -> Dict[str, Any]:
    """图片摘要"""
    payload = {
        'pictureUrl': picture_url,
        'keyword': keyword
    }
    return client.call_api(API_IMAGE_SUMMARY, payload)


def image_compare(client: DahuaApiClient, base_picture_url: str, picture_urls: List[str], prompt: str) -> Dict[str, Any]:
    """基图比对"""
    payload = {
        'basePictureUrl': base_picture_url,
        'pictureUrls': picture_urls,
        'prompt': prompt
    }
    return client.call_api(API_IMAGE_COMPARE, payload)


# =============================================================================
# API 调用函数 - 文本理解
# =============================================================================

def text_analysis(client: DahuaApiClient, text: str, prompt: str) -> Dict[str, Any]:
    """文本分析"""
    payload = {
        'text': text,
        'prompt': prompt
    }
    return client.call_api(API_TEXT_ANALYSIS, payload)


def text_to_audio(client: DahuaApiClient, text: str, volume: int = 50, speech_rate: float = 1.0,
                  tone: float = 1.0, voice: int = 0, audio_format: int = 0) -> Dict[str, Any]:
    """文字转语音"""
    payload = {
        'text': text,
        'volume': volume,
        'speechRate': speech_rate,
        'tone': tone,
        'voice': voice,
        'audioFormat': audio_format
    }
    return client.call_api(API_TEXT_TO_AUDIO, payload)


# =============================================================================
# API 调用函数 - 视频理解
# =============================================================================

def video_analysis(client: DahuaApiClient, video_url: str, prompt: str) -> Dict[str, Any]:
    """视频分析"""
    payload = {
        'videoUrl': video_url,
        'prompt': prompt
    }
    return client.call_api(API_VIDEO_ANALYSIS, payload)


# =============================================================================
# API 调用函数 - 音频理解
# =============================================================================

def audio_to_text(client: DahuaApiClient, audio_urls: List[str]) -> Dict[str, Any]:
    """语音转文字"""
    payload = {
        'audioUrls': audio_urls
    }
    return client.call_api(API_AUDIO_TO_TEXT, payload)


# =============================================================================
# 输出处理
# =============================================================================

def output_result(result: Dict[str, Any], output_file: Optional[str] = None, 
                  json_output: bool = True) -> None:
    """
    输出结果到控制台或文件
    
    Args:
        result: API 返回的结果
        output_file: 输出文件路径，None 则输出到控制台
        json_output: 是否以 JSON 格式输出（机器可读）
    """
    if json_output:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        # 人类可读的格式
        output = format_human_readable(result)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"结果已保存到: {output_file}")
    else:
        print(output)


def format_human_readable(result: Dict[str, Any]) -> str:
    """将结果格式化为人类可读的文本"""
    lines = []
    
    data = result.get('data', {})
    
    # 特殊处理 doctor 命令的输出
    if 'checks' in data and 'summary' in data:
        lines.append("")
        lines.append(f"诊断结果: {data['summary']}")
        lines.append("")
        lines.append("检查项:")
        lines.append("")
        
        for check in data['checks']:
            name = check.get('name', '')
            status = check.get('status', '')
            value = check.get('value', '')
            
            if value:
                lines.append(f"  {status:<10} {name:<35} {value}")
            else:
                lines.append(f"  {status:<10} {name}")
        
        # 如果有帮助信息，显示配置指南
        help_info = data.get('help')
        if help_info:
            lines.append("")
            lines.append("=" * 60)
            lines.append(f"配置指南: {help_info.get('title', '')}")
            lines.append("=" * 60)
            lines.append("")
            
            # 显示 README 参考
            readme_ref = help_info.get('readme_reference')
            if readme_ref:
                lines.append(readme_ref)
                lines.append("")
            
            # 显示故障排除信息
            troubleshooting = help_info.get('troubleshooting')
            if troubleshooting:
                lines.append("故障排除:")
                for item in troubleshooting:
                    lines.append(f"  {item}")
                lines.append("")
            
            # 显示各平台配置命令
            if help_info.get('windows_powershell'):
                lines.append("Windows PowerShell:")
                for cmd in help_info.get('windows_powershell', []):
                    lines.append(f"  {cmd}")
                lines.append("")
            
            if help_info.get('windows_cmd'):
                lines.append("Windows CMD:")
                for cmd in help_info.get('windows_cmd', []):
                    lines.append(f"  {cmd}")
                lines.append("")
            
            if help_info.get('linux_mac'):
                lines.append("Linux / macOS:")
                for cmd in help_info.get('linux_mac', []):
                    lines.append(f"  {cmd}")
                lines.append("")
            
            # 显示永久配置说明
            if help_info.get('permanent'):
                lines.append(help_info.get('permanent', ''))
                lines.append(f"  Windows: {help_info.get('windows_permanent', '')}")
                lines.append(f"  Linux/Mac: {help_info.get('linux_mac_permanent', '')}")
                lines.append("")
        
        return '\n'.join(lines)
    
    # 处理错误情况
    if not result.get('success'):
        lines.append(f"错误: {result.get('msg', '未知错误')}")
        return '\n'.join(lines)
    
    # 处理 AI 分析结果（图片分析、文本分析、视频分析等）
    if isinstance(data, dict):
        # 优先提取 content 字段（AI 分析结果的主要内容）
        if 'content' in data:
            content = data['content']
            if isinstance(content, str):
                lines.append(content)
            elif isinstance(content, dict):
                # 如果 content 是字典，递归提取文本内容
                lines.append(extract_text_content(content))
            elif isinstance(content, list):
                for item in content:
                    lines.append(str(item))
            else:
                lines.append(str(content))
        
        # 提取其他常见的 AI 结果字段
        elif 'result' in data:
            result_val = data['result']
            if isinstance(result_val, str):
                lines.append(result_val)
            else:
                lines.append(json.dumps(result_val, ensure_ascii=False, indent=2))
        
        elif 'text' in data:
            lines.append(data['text'])
        
        elif 'answer' in data:
            lines.append(data['answer'])
        
        elif 'description' in data:
            lines.append(data['description'])
        
        # 处理 contents 字段（音频转文字等接口返回）
        elif 'contents' in data:
            contents = data['contents']
            if isinstance(contents, list):
                if len(contents) == 1:
                    lines.append(f"识别文本内容：{contents[0]}")
                else:
                    lines.append("识别文本内容：")
                    for i, item in enumerate(contents, 1):
                        lines.append(f"  [{i}] {item}")
            else:
                lines.append(f"识别文本内容：{contents}")
        
        # 语音转文字特殊处理
        elif 'audioToTextResults' in data:
            results = data['audioToTextResults']
            if isinstance(results, list):
                lines.append("语音识别结果:")
                for i, item in enumerate(results, 1):
                    if isinstance(item, dict):
                        text = item.get('text', '')
                        lines.append(f"[{i}] {text}")
                    else:
                        lines.append(f"[{i}] {item}")
            else:
                lines.append(str(results))
        
        # 文字转语音特殊处理
        elif 'audioUrl' in data or 'audioUrls' in data:
            audio_url = data.get('audioUrl') or data.get('audioUrls')
            lines.append(f"语音文件地址: {audio_url}")
        
        # 默认处理：遍历所有字段
        else:
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{key}:")
                    lines.append(json.dumps(value, ensure_ascii=False, indent=2))
                else:
                    lines.append(f"{key}: {value}")
    
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                lines.append(f"[{i}] {extract_text_content(item)}")
            else:
                lines.append(f"[{i}] {item}")
    else:
        lines.append(str(data))
    
    return '\n'.join(lines)


def extract_text_content(data: Dict[str, Any]) -> str:
    """从字典中提取文本内容"""
    # 按优先级尝试提取文本字段
    text_fields = ['content', 'text', 'result', 'answer', 'description', 'message', 'value', 'contents']
    for field in text_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                return value
            elif isinstance(value, dict):
                return extract_text_content(value)
            elif isinstance(value, list) and value:
                if isinstance(value[0], str):
                    return '\n'.join(value)
                elif isinstance(value[0], dict):
                    return '\n'.join([extract_text_content(item) for item in value])
    
    # 如果没有找到文本字段，返回所有值的字符串表示
    return '\n'.join([f"{k}: {v}" for k, v in data.items() if not isinstance(v, (dict, list))])


# =============================================================================
# Doctor 诊断功能
# =============================================================================

def run_doctor() -> Dict[str, Any]:
    """
    运行环境诊断，检查必要的配置
    
    Returns:
        诊断结果字典
    """
    checks = []
    all_passed = True
    env_vars_configured = True
    
    # 检查 DAHUA_CLOUD_PRODUCT_ID
    product_id = os.getenv(ENV_CLOUD_ID)
    if product_id:
        checks.append({
            "name": f"环境变量 {ENV_CLOUD_ID}",
            "status": "✓ 已配置",
            "value": f"{product_id[:4]}****{product_id[-4:]}" if len(product_id) > 8 else "****"
        })
    else:
        checks.append({
            "name": f"环境变量 {ENV_CLOUD_ID}",
            "status": "✗ 未配置",
            "value": None
        })
        all_passed = False
        env_vars_configured = False
    
    # 检查 DAHUA_CLOUD_AK
    access_key = os.getenv(ENV_CLOUD_AK)
    if access_key:
        checks.append({
            "name": f"环境变量 {ENV_CLOUD_AK}",
            "status": "✓ 已配置",
            "value": f"{access_key[:4]}****{access_key[-4:]}" if len(access_key) > 8 else "****"
        })
    else:
        checks.append({
            "name": f"环境变量 {ENV_CLOUD_AK}",
            "status": "✗ 未配置",
            "value": None
        })
        all_passed = False
        env_vars_configured = False
    
    # 检查 DAHUA_CLOUD_SK
    secret_key = os.getenv(ENV_CLOUD_SK)
    if secret_key:
        checks.append({
            "name": f"环境变量 {ENV_CLOUD_SK}",
            "status": "✓ 已配置",
            "value": f"{secret_key[:4]}****{secret_key[-4:]}" if len(secret_key) > 8 else "****"
        })
    else:
        checks.append({
            "name": f"环境变量 {ENV_CLOUD_SK}",
            "status": "✗ 未配置",
            "value": None
        })
        all_passed = False
        env_vars_configured = False
    
    # 检查网络连接
    network_ok = False
    try:
        response = requests.get(DEFAULT_API_BASE_URL, timeout=5)
        checks.append({
            "name": "网络连接",
            "status": "✓ 正常",
            "value": f"可连接到 {DEFAULT_API_BASE_URL}"
        })
        network_ok = True
    except requests.RequestException:
        checks.append({
            "name": "网络连接",
            "status": "⚠ 警告",
            "value": f"无法连接到 {DEFAULT_API_BASE_URL}，请检查网络"
        })
    
    # 如果环境变量都已配置且网络正常，验证凭据有效性
    if env_vars_configured and network_ok:
        try:
            client = DahuaApiClient(product_id, access_key, secret_key)
            token = client.get_app_access_token()
            if token:
                checks.append({
                    "name": "API 凭据验证",
                    "status": "✓ 有效",
                    "value": "成功获取 Access Token"
                })
            else:
                checks.append({
                    "name": "API 凭据验证",
                    "status": "✗ 无效",
                    "value": "无法获取 Access Token"
                })
                all_passed = False
        except ValueError as e:
            checks.append({
                "name": "API 凭据验证",
                "status": "✗ 无效",
                "value": str(e)
            })
            all_passed = False
        except requests.RequestException as e:
            checks.append({
                "name": "API 凭据验证",
                "status": "⚠ 请求失败",
                "value": f"API 请求失败: {e}"
            })
            all_passed = False
    
    result = {
        "success": all_passed,
        "data": {
            "summary": "所有检查通过" if all_passed else "部分检查未通过",
            "checks": checks
        }
    }
    
    if not all_passed:
        if not env_vars_configured:
            result["msg"] = "环境变量未配置"
            result["data"]["help"] = {
                "title": "如何配置环境变量",
                "readme_reference": "详细配置说明请参考 README.md 文件",
                "windows_powershell": [
                    f"$env:{ENV_CLOUD_ID} = 'your-product-id'",
                    f"$env:{ENV_CLOUD_AK} = 'your-access-key'",
                    f"$env:{ENV_CLOUD_SK} = 'your-secret-key'"
                ],
                "windows_cmd": [
                    f"set {ENV_CLOUD_ID}=your-product-id",
                    f"set {ENV_CLOUD_AK}=your-access-key",
                    f"set {ENV_CLOUD_SK}=your-secret-key"
                ],
                "linux_mac": [
                    f"export {ENV_CLOUD_ID}=your-product-id",
                    f"export {ENV_CLOUD_AK}=your-access-key",
                    f"export {ENV_CLOUD_SK}=your-secret-key"
                ],
                "permanent": "建议将环境变量添加到系统配置中：",
                "windows_permanent": "系统属性 → 高级 → 环境变量 → 新建用户变量",
                "linux_mac_permanent": "添加到 ~/.bashrc 或 ~/.zshrc 文件"
            }
        else:
            result["msg"] = "环境变量配置无效"
            result["data"]["help"] = {
                "title": "凭据验证失败",
                "readme_reference": "请检查环境变量值是否正确，详细说明请参考 README.md 文件",
                "troubleshooting": [
                    "1. 确认 Product ID、Access Key、Secret Key 是否正确",
                    "2. 确认账号是否有 API 调用权限",
                    "3. 检查网络连接是否正常"
                ]
            }
    
    return result


def run_init() -> Dict[str, Any]:
    """
    交互式初始化配置，引导用户设置环境变量
    配置会永久保存到系统环境变量中
    """
    print("\n" + "=" * 50)
    print("大华云 CLI 初始化配置")
    print("=" * 50)
    print()
    
    # 检查现有环境变量配置
    existing_product_id = os.getenv(ENV_CLOUD_ID)
    existing_access_key = os.getenv(ENV_CLOUD_AK)
    existing_secret_key = os.getenv(ENV_CLOUD_SK)
    
    if existing_product_id or existing_access_key or existing_secret_key:
        print("检测到已有环境变量配置：")
        if existing_product_id:
            # 隐藏部分信息以保护敏感数据（格式：前4位+****+后4位）
            masked_id = f"{existing_product_id[:4]}****{existing_product_id[-4:]}" if len(existing_product_id) > 8 else "****"
            print(f"  {ENV_CLOUD_ID}: {masked_id}")
        if existing_access_key:
            masked_ak = f"{existing_access_key[:4]}****{existing_access_key[-4:]}" if len(existing_access_key) > 8 else "****"
            print(f"  {ENV_CLOUD_AK}: {masked_ak}")
        if existing_secret_key:
            masked_sk = f"{existing_secret_key[:4]}****{existing_secret_key[-4:]}" if len(existing_secret_key) > 8 else "****"
            print(f"  {ENV_CLOUD_SK}: {masked_sk}")
        print()
        
        # 询问用户是否覆盖
        choice = input("是否重新配置？(y/n): ").strip().lower()
        if choice in ('n', 'no', '否'):
            print()
            print("已取消配置，保留现有设置。")
            return None
        elif choice not in ('y', 'yes', '是'):
            print()
            print("输入无效，保留现有设置。")
            return None
        
        print()
    
    print("请输入大华云开发者平台的凭据信息：")
    print("(获取方式: https://open.cloud-dahua.com/ → 产品管理)")
    print()
    
    # 交互式输入
    product_id = input(f"{ENV_CLOUD_ID}: ").strip()
    while not product_id:
        print("错误: Product ID 不能为空")
        product_id = input(f"{ENV_CLOUD_ID}: ").strip()
    
    access_key = input(f"{ENV_CLOUD_AK}: ").strip()
    while not access_key:
        print("错误: Access Key 不能为空")
        access_key = input(f"{ENV_CLOUD_AK}: ").strip()
    
    secret_key = input(f"{ENV_CLOUD_SK}: ").strip()
    while not secret_key:
        print("错误: Secret Key 不能为空")
        secret_key = input(f"{ENV_CLOUD_SK}: ").strip()
    
    print()
    print("正在保存配置...")
    
    try:
        # 1. 设置当前会话变量（立即生效）
        os.environ[ENV_CLOUD_ID] = product_id
        os.environ[ENV_CLOUD_AK] = access_key
        os.environ[ENV_CLOUD_SK] = secret_key
        
        # 2. 永久保存到系统配置
        if sys.platform == 'win32':
            # Windows: 使用 PowerShell 设置用户环境变量
            import subprocess
            
            # 设置 Product ID
            subprocess.run([
                'powershell', '-Command',
                f'[Environment]::SetEnvironmentVariable("{ENV_CLOUD_ID}", "{product_id}", "User")'
            ], check=True, capture_output=True)
            
            # 设置 Access Key
            subprocess.run([
                'powershell', '-Command',
                f'[Environment]::SetEnvironmentVariable("{ENV_CLOUD_AK}", "{access_key}", "User")'
            ], check=True, capture_output=True)
            
            # 设置 Secret Key
            subprocess.run([
                'powershell', '-Command',
                f'[Environment]::SetEnvironmentVariable("{ENV_CLOUD_SK}", "{secret_key}", "User")'
            ], check=True, capture_output=True)
            
        else:
            # Linux/Mac: 写入 shell 配置文件
            shell_rc = os.path.expanduser('~/.bashrc')
            # 检测当前 shell
            shell = os.environ.get('SHELL', '')
            if 'zsh' in shell:
                shell_rc = os.path.expanduser('~/.zshrc')
            elif 'bash' in shell:
                if sys.platform == 'darwin':  # macOS
                    shell_rc = os.path.expanduser('~/.bash_profile')
            
            # 检查是否已存在配置
            config_exists = False
            if os.path.exists(shell_rc):
                with open(shell_rc, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if ENV_CLOUD_ID in content:
                        config_exists = True
            
            # 追加配置
            with open(shell_rc, 'a', encoding='utf-8') as f:
                if not config_exists:
                    f.write('\n# 大华云 CLI 配置\n')
                    f.write(f'export {ENV_CLOUD_ID}="{product_id}"\n')
                    f.write(f'export {ENV_CLOUD_AK}="{access_key}"\n')
                    f.write(f'export {ENV_CLOUD_SK}="{secret_key}"\n')
                else:
                    # 更新现有配置
                    import re
                    with open(shell_rc, 'r', encoding='utf-8') as f_read:
                        content = f_read.read()
                    
                    # 替换现有值
                    content = re.sub(
                        rf'export {ENV_CLOUD_ID}=.*',
                        f'export {ENV_CLOUD_ID}="{product_id}"',
                        content
                    )
                    content = re.sub(
                        rf'export {ENV_CLOUD_AK}=.*',
                        f'export {ENV_CLOUD_AK}="{access_key}"',
                        content
                    )
                    content = re.sub(
                        rf'export {ENV_CLOUD_SK}=.*',
                        f'export {ENV_CLOUD_SK}="{secret_key}"',
                        content
                    )
                    
                    with open(shell_rc, 'w', encoding='utf-8') as f_write:
                        f_write.write(content)
        
        print()
        print("✓ 配置已保存！")
        print()
        print("[INFO] 环境变量已写入用户配置（永久生效）")
        print()
        
        if sys.platform == 'win32':
            print("[注意] 请重新打开终端使配置生效")
        else:
            shell_rc_display = '~/.bashrc'
            shell = os.environ.get('SHELL', '')
            if 'zsh' in shell:
                shell_rc_display = '~/.zshrc'
            elif 'bash' in shell and sys.platform == 'darwin':
                shell_rc_display = '~/.bash_profile'
            
            print("[注意] 请运行以下命令使配置生效：")
            print(f"  source {shell_rc_display}")
            print()
            print("或者重新打开终端")
        
        print()
        print("验证配置: dahua-cloud doctor")
        print()
        
        return {
            "success": True,
            "data": {
                "message": "配置已保存",
                "configured": True
            }
        }
        
    except Exception as e:
        print()
        print(f"✗ 保存配置失败: {e}")
        print()
        print("您可以手动设置环境变量：")
        if sys.platform == 'win32':
            print(f"  $env:{ENV_CLOUD_ID} = '{product_id}'")
            print(f"  $env:{ENV_CLOUD_AK} = '{access_key}'")
            print(f"  $env:{ENV_CLOUD_SK} = '{secret_key}'")
        else:
            print(f"  export {ENV_CLOUD_ID}='{product_id}'")
            print(f"  export {ENV_CLOUD_AK}='{access_key}'")
            print(f"  export {ENV_CLOUD_SK}='{secret_key}'")
        
        return {
            "success": False,
            "data": {
                "message": f"保存配置失败: {e}",
                "configured": False
            }
        }


# =============================================================================
# 命令行参数解析
# =============================================================================

def create_client() -> DahuaApiClient:
    """从环境变量创建客户端"""
    app_id = os.getenv(ENV_CLOUD_ID)
    access_key = os.getenv(ENV_CLOUD_AK)
    secret_key = os.getenv(ENV_CLOUD_SK)

    if not all([app_id, access_key, secret_key]):
        missing = []
        if not app_id:
            missing.append(ENV_CLOUD_ID)
        if not access_key:
            missing.append(ENV_CLOUD_AK)
        if not secret_key:
            missing.append(ENV_CLOUD_SK)
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return DahuaApiClient(app_id, access_key, secret_key)


def parse_list_argument(value: str) -> List[str]:
    """解析逗号分隔的列表参数"""
    return [item.strip() for item in value.split(',') if item.strip()]


class CustomHelpFormatter(argparse.HelpFormatter):
    """自定义帮助格式化器，遵循 CLI Guidelines"""
    
    def __init__(self, prog):
        super().__init__(prog, max_help_position=30, width=100)
    
    def _format_usage(self, usage, actions, groups, prefix):
        """自定义 USAGE 格式"""
        if prefix is None:
            prefix = 'USAGE:'
        # 根据 prog 层级智能生成 usage
        # prog 形如 "dahua-cloud-ai-cli.py" 或 "dahua-cloud-ai-cli.py image"
        parts = self._prog.split()
        if len(parts) > 1:
            # 子命令级别: dahua-cloud image <subcommand> [flags]
            subcommand = parts[-1]
            return f'\n{prefix}\n  dahua-cloud {subcommand} <subcommand> [flags]\n'
        else:
            # 顶级: dahua-cloud <command> <subcommand> [flags]
            return f'\n{prefix}\n  dahua-cloud <command> <subcommand> [flags]\n'
    
    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            return self._format_subparsers(action)
        return super()._format_action(action)
    
    def _format_subparsers(self, action):
        parts = []
        parts.append('')
        parts.append('COMMANDS:')
        parts.append('')
        
        for choice_action in action._choices_actions:
            name = choice_action.dest
            description = choice_action.help or ''
            parts.append(f'  {name:<15} {description}')
        parts.append('')
        return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(
        description='大华云大模型推理套件 CLI',
        formatter_class=CustomHelpFormatter,
        add_help=False
    )

    # 全局选项
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                       help='显示帮助信息')
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}',
                       help='显示版本信息')
    parser.add_argument('--json', action='store_true',
                       help='以 JSON 格式输出结果')
    parser.add_argument('--no-json', action='store_false', dest='json', default=True,
                       help='以人类可读格式输出结果（默认）')

    subparsers = parser.add_subparsers(dest='category', title=argparse.SUPPRESS, metavar='')

    # 创建父解析器用于共享参数
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--json', action='store_true',
                              help='以 JSON 格式输出结果')
    parent_parser.add_argument('--no-json', action='store_false', dest='json', default=True,
                              help='以人类可读格式输出结果（默认）')
    parent_parser.add_argument('--output', '-o', type=str, help='将API响应结果保存到指定文件路径')

    # =========================================================================
    # 图片理解命令组
    # =========================================================================
    image_parser = subparsers.add_parser('image', description='图片理解相关 API',
                                        help='图片理解相关 API',
                                        formatter_class=CustomHelpFormatter,
                                        add_help=False)
    image_parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                              help='显示帮助信息')
    image_subparsers = image_parser.add_subparsers(dest='action', title=argparse.SUPPRESS, metavar='')

    # 单图分析
    img_analysis = image_subparsers.add_parser('analysis', help='单图分析', parents=[parent_parser])
    img_analysis.add_argument('picture_url_pos', nargs='?', metavar='picture-url', help='图片 URL（位置参数）')
    img_analysis.add_argument('prompt_pos', nargs='?', metavar='prompt', help='分析提示词（位置参数）')
    img_analysis.add_argument('--picture-url', '-u', type=str, help='图片 URL')
    img_analysis.add_argument('--prompt', '-p', type=str, help='分析提示词')

    # 多图分析
    img_multi = image_subparsers.add_parser('multi-analysis', help='多图分析', parents=[parent_parser])
    img_multi.add_argument('--picture-urls', type=str, required=True, help='图片 URL 列表（逗号分隔）')
    img_multi.add_argument('--prompt', '-p', type=str, required=True, help='分析提示词')

    # 图片摘要
    img_summary = image_subparsers.add_parser('summary', help='图片摘要', parents=[parent_parser])
    img_summary.add_argument('picture_url_pos', nargs='?', metavar='picture-url', help='图片 URL（位置参数）')
    img_summary.add_argument('keyword_pos', nargs='?', metavar='keyword', help='关键词（位置参数）')
    img_summary.add_argument('--picture-url', '-u', type=str, help='图片 URL')
    img_summary.add_argument('--keyword', '-k', type=str, help='关键词')

    # 基图比对
    img_compare = image_subparsers.add_parser('compare', help='基图比对', parents=[parent_parser])
    img_compare.add_argument('--base-url', type=str, required=True, help='基准图片 URL')
    img_compare.add_argument('--picture-urls', type=str, required=True, help='待对比图片 URL 列表（逗号分隔）')
    img_compare.add_argument('--prompt', '-p', type=str, required=True, help='比对提示词')

    # =========================================================================
    # 文本理解命令组
    # =========================================================================
    text_parser = subparsers.add_parser('text', description='文本理解相关 API',
                                       help='文本理解相关 API',
                                       formatter_class=CustomHelpFormatter,
                                       add_help=False)
    text_parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                             help='显示帮助信息')
    text_subparsers = text_parser.add_subparsers(dest='action', title=argparse.SUPPRESS, metavar='')

    # 文本分析
    txt_analysis = text_subparsers.add_parser('analysis', help='文本分析', parents=[parent_parser])
    txt_analysis.add_argument('text_pos', nargs='?', metavar='text', help='待分析文本（位置参数）')
    txt_analysis.add_argument('prompt_pos', nargs='?', metavar='prompt', help='分析提示词（位置参数）')
    txt_analysis.add_argument('--text', '-t', type=str, help='待分析文本')
    txt_analysis.add_argument('--prompt', '-p', type=str, help='分析提示词')

    # 文字转语音
    txt_tts = text_subparsers.add_parser('tts', help='文字转语音', parents=[parent_parser])
    txt_tts.add_argument('text_pos', nargs='?', metavar='text', help='待转换文本（位置参数，不超过500字符）')
    txt_tts.add_argument('--text', '-t', type=str, help='待转换文本（不超过500字符）')
    txt_tts.add_argument('--volume', type=int, default=50, help='音量 (0-100，默认50)')
    txt_tts.add_argument('--speech-rate', type=float, default=1.0, help='语速 (0.5-2，默认1.0)')
    txt_tts.add_argument('--tone', type=float, default=1.0, help='语调 (0.5-2，默认1.0)')
    txt_tts.add_argument('--voice', type=int, default=0, help='音色 (0-3，默认0女声)')
    txt_tts.add_argument('--audio-format', type=int, default=0, help='音频格式 (0-mp3, 1-wav，默认0)')

    # =========================================================================
    # 视频理解命令组
    # =========================================================================
    video_parser = subparsers.add_parser('video', description='视频理解相关 API',
                                        help='视频理解相关 API',
                                        formatter_class=CustomHelpFormatter,
                                        add_help=False)
    video_parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                              help='显示帮助信息')
    video_subparsers = video_parser.add_subparsers(dest='action', title=argparse.SUPPRESS, metavar='')

    # 视频分析
    vid_analysis = video_subparsers.add_parser('analysis', help='视频分析', parents=[parent_parser])
    vid_analysis.add_argument('video_url_pos', nargs='?', metavar='video-url', help='视频 URL（位置参数）')
    vid_analysis.add_argument('prompt_pos', nargs='?', metavar='prompt', help='分析提示词（位置参数）')
    vid_analysis.add_argument('--video-url', '-u', type=str, help='视频 URL')
    vid_analysis.add_argument('--prompt', '-p', type=str, help='分析提示词')

    # =========================================================================
    # 音频理解命令组
    # =========================================================================
    audio_parser = subparsers.add_parser('audio', description='音频理解相关 API',
                                        help='音频理解相关 API',
                                        formatter_class=CustomHelpFormatter,
                                        add_help=False)
    audio_parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                              help='显示帮助信息')
    audio_subparsers = audio_parser.add_subparsers(dest='action', title=argparse.SUPPRESS, metavar='')

    # 语音转文字
    aud_transcribe = audio_subparsers.add_parser('transcribe', help='语音转文字', parents=[parent_parser])
    aud_transcribe.add_argument('audio_urls_pos', nargs='?', metavar='audio-urls', help='音频 URL 列表（位置参数，逗号分隔，最多3个）')
    aud_transcribe.add_argument('--audio-urls', type=str, help='音频 URL 列表（逗号分隔，最多3个）')

    # =========================================================================
    # Doctor 诊断命令
    # =========================================================================
    # init 命令 - 初始化配置
    init_parser = subparsers.add_parser('init', description='初始化配置环境变量',
                                        help='初始化配置环境变量（交互式）')
    init_parser.add_argument('--json', action='store_true',
                             help='以 JSON 格式输出结果')
    init_parser.add_argument('--no-json', action='store_false', dest='json', default=True,
                             help='以人类可读格式输出结果（默认）')
    
    # doctor 命令 - 诊断环境配置
    doctor_parser = subparsers.add_parser('doctor', description='诊断环境配置',
                                         help='诊断环境配置')
    doctor_parser.add_argument('--json', action='store_true',
                              help='以 JSON 格式输出结果')
    doctor_parser.add_argument('--no-json', action='store_false', dest='json', default=True,
                              help='以人类可读格式输出结果（默认）')

    # 解析参数
    args = parser.parse_args()

    if not args.category:
        parser.print_help()
        sys.exit(1)

    # 处理 init 命令
    if args.category == 'init':
        result = run_init()
        if result is None:
            sys.exit(0)
        output_result(result, None, json_output=args.json)
        if not result.get('success'):
            sys.exit(1)
        sys.exit(0)

    # 处理 doctor 命令
    if args.category == 'doctor':
        result = run_doctor()
        output_result(result, None, json_output=args.json)
        if not result.get('success'):
            sys.exit(1)
        sys.exit(0)

    # 合并位置参数和选项参数（优先使用选项参数）
    if args.category == 'image':
        if args.action == 'analysis':
            picture_url = args.picture_url if args.picture_url else getattr(args, 'picture_url_pos', None)
            prompt = args.prompt if args.prompt else getattr(args, 'prompt_pos', None)
            if not picture_url or not prompt:
                print("error: 需要提供 picture-url 和 prompt", file=sys.stderr)
                check_and_print_powershell_warning()
                sys.exit(1)
            args.picture_url = picture_url
            args.prompt = prompt
        elif args.action == 'summary':
            picture_url = args.picture_url if args.picture_url else getattr(args, 'picture_url_pos', None)
            keyword = args.keyword if args.keyword else getattr(args, 'keyword_pos', None)
            if not picture_url or not keyword:
                print("error: 需要提供 picture-url 和 keyword", file=sys.stderr)
                check_and_print_powershell_warning()
                sys.exit(1)
            args.picture_url = picture_url
            args.keyword = keyword
    elif args.category == 'text':
        if args.action == 'analysis':
            text = args.text if args.text else getattr(args, 'text_pos', None)
            prompt = args.prompt if args.prompt else getattr(args, 'prompt_pos', None)
            if not text or not prompt:
                print("error: 需要提供 text 和 prompt", file=sys.stderr)
                check_and_print_powershell_warning()
                sys.exit(1)
            args.text = text
            args.prompt = prompt
        elif args.action == 'tts':
            text = args.text if args.text else getattr(args, 'text_pos', None)
            if not text:
                print("error: 需要提供 text", file=sys.stderr)
                check_and_print_powershell_warning()
                sys.exit(1)
            args.text = text
    elif args.category == 'video':
        if args.action == 'analysis':
            video_url = args.video_url if args.video_url else getattr(args, 'video_url_pos', None)
            prompt = args.prompt if args.prompt else getattr(args, 'prompt_pos', None)
            if not video_url or not prompt:
                print("error: 需要提供 video-url 和 prompt", file=sys.stderr)
                check_and_print_powershell_warning()
                sys.exit(1)
            args.video_url = video_url
            args.prompt = prompt
    elif args.category == 'audio':
        if args.action == 'transcribe':
            audio_urls = args.audio_urls if args.audio_urls else getattr(args, 'audio_urls_pos', None)
            if not audio_urls:
                print("error: 需要提供 audio-urls", file=sys.stderr)
                check_and_print_powershell_warning()
                sys.exit(1)
            args.audio_urls = audio_urls

    try:
        client = create_client()
        result = None

        # 图片理解
        if args.category == 'image':
            if args.action == 'analysis':
                result = image_analysis(client, args.picture_url, args.prompt)
            elif args.action == 'multi-analysis':
                urls = parse_list_argument(args.picture_urls)
                result = multi_image_analysis(client, urls, args.prompt)
            elif args.action == 'summary':
                result = image_summary(client, args.picture_url, args.keyword)
            elif args.action == 'compare':
                urls = parse_list_argument(args.picture_urls)
                result = image_compare(client, args.base_url, urls, args.prompt)
            else:
                image_parser.print_help()
                sys.exit(1)

        # 文本理解
        elif args.category == 'text':
            if args.action == 'analysis':
                result = text_analysis(client, args.text, args.prompt)
            elif args.action == 'tts':
                result = text_to_audio(
                    client, args.text, args.volume, args.speech_rate,
                    args.tone, args.voice, args.audio_format
                )
            else:
                text_parser.print_help()
                sys.exit(1)

        # 视频理解
        elif args.category == 'video':
            if args.action == 'analysis':
                result = video_analysis(client, args.video_url, args.prompt)
            else:
                video_parser.print_help()
                sys.exit(1)

        # 音频理解
        elif args.category == 'audio':
            if args.action == 'transcribe':
                urls = parse_list_argument(args.audio_urls)
                result = audio_to_text(client, urls)
            else:
                audio_parser.print_help()
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

        # 输出结果
        if result:
            if result.get('success'):
                output_result(result, getattr(args, 'output', None), json_output=args.json)
            else:
                print(f"Error: {result.get('msg')}", file=sys.stderr)
                sys.exit(1)

    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"error: request failed - {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nerror: interrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"error: unexpected error - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
