import re
import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger("ChatServer")


class FilmHelper:
    @staticmethod
    def extract_movie_url(message):
        """
        从消息中提取电影URL
        
        Args:
            message: 包含@电影命令的消息
            
        Returns:
            str or None: 提取到的URL，如果没有有效的URL则返回None
        """
        match = re.search(r'@电影\s+(https?://[^\s]+)', message)
        if match:
            url = match.group(1)
            # 验证URL格式是否有效
            parsed_url = urlparse(url)
            if parsed_url.scheme in ['http', 'https'] and parsed_url.netloc:
                return url
        return None

    @staticmethod
    def create_movie_message(url, sender):
        """
        创建电影播放消息
        
        Args:
            url: 电影URL
            sender: 发送者名称
            
        Returns:
            dict: 格式化的电影消息对象
        """
        return {
            "type": "movie",
            "url": url,
            "sender": sender,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }

    @staticmethod
    def create_error_message(error_type="format"):
        """
        创建错误消息
        
        Args:
            error_type: 错误类型，可选值："format" 或 "invalid"
            
        Returns:
            dict: 错误消息对象
        """
        messages = {
            "format": "请提供电影链接，格式为 @电影 URL",
            "invalid": "不支持的电影链接格式。"
        }
        
        return {
            "type": "error",
            "message": messages.get(error_type, "发生错误，请重试")
        }
