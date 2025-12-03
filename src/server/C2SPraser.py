import json
import logging
import re

logger = logging.getLogger("ChatServer")


class C2SPraser:
    @staticmethod
    def parse_json_message(message):
        """
        解析JSON格式的消息
        
        Args:
            message: 原始消息字符串
            
        Returns:
            dict or None: 解析后的消息对象，如果解析失败返回None
        """
        try:
            data = json.loads(message)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return None
    
    @staticmethod
    def validate_message_structure(data, required_fields=None, optional_fields=None):
        """
        验证消息结构是否符合要求
        
        Args:
            data: 消息数据
            required_fields: 必需字段列表
            optional_fields: 可选字段列表
            
        Returns:
            tuple: (is_valid, error_message) - 是否有效及错误信息
        """
        if not isinstance(data, dict):
            return False, "消息格式必须是JSON对象"
            
        # 检查必需字段
        if required_fields:
            for field in required_fields:
                if field not in data:
                    return False, f"缺少必需字段: {field}"
        
        # 检查消息类型
        if 'type' not in data:
            return False, "消息必须包含type字段"
        
        return True, None
    
    @staticmethod
    def parse_register_message(data):
        """
        解析注册消息
        
        Args:
            data: 消息数据
            
        Returns:
            tuple: (is_valid, username, password, error_message)
        """
        # 验证消息结构
        is_valid, error = C2SPraser.validate_message_structure(data, 
                                                             required_fields=['username', 'password'])
        if not is_valid:
            return False, None, None, error
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # 验证用户名和密码
        if not username:
            return False, None, None, "用户名不能为空"
        if not password:
            return False, None, None, "密码不能为空"
        if len(username) < 3 or len(username) > 20:
            return False, None, None, "用户名长度必须在3-20个字符之间"
        if len(password) < 6:
            return False, None, None, "密码长度必须至少为6个字符"
        
        return True, username, password, None
    
    @staticmethod
    def parse_login_message(data):
        """
        解析登录消息
        
        Args:
            data: 消息数据
            
        Returns:
            tuple: (is_valid, username, password, error_message)
        """
        # 验证消息结构
        is_valid, error = C2SPraser.validate_message_structure(data, 
                                                             required_fields=['username', 'password'])
        if not is_valid:
            return False, None, None, error
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # 验证用户名和密码
        if not username:
            return False, None, None, "用户名不能为空"
        if not password:
            return False, None, None, "密码不能为空"
        
        return True, username, password, None
    
    @staticmethod
    def parse_chat_message(data):
        """
        解析聊天消息
        
        Args:
            data: 消息数据
            
        Returns:
            tuple: (is_valid, content, error_message)
        """
        # 验证消息结构
        is_valid, error = C2SPraser.validate_message_structure(data, 
                                                             required_fields=['message'])
        if not is_valid:
            return False, None, error
        
        content = data.get('message', '').strip()
        
        if not content:
            return False, None, "消息内容不能为空"
        
        return True, content, None
    
    @staticmethod
    def parse_room_change_message(data):
        """
        解析房间切换消息
        
        Args:
            data: 消息数据
            
        Returns:
            tuple: (is_valid, room_name, error_message)
        """
        # 验证消息结构
        is_valid, error = C2SPraser.validate_message_structure(data, 
                                                             required_fields=['room'])
        if not is_valid:
            return False, None, error
        
        room_name = data.get('room', '').strip()
        
        if not room_name:
            return False, None, "房间名称不能为空"
        
        return True, room_name, None
    
    @staticmethod
    def is_at_command(content):
        """
        检查内容是否为@命令
        
        Args:
            content: 消息内容
            
        Returns:
            bool: 是否为@命令
        """
        return content.startswith('@')
    
    @staticmethod
    def extract_at_command_info(content):
        """
        提取@命令信息
        
        Args:
            content: 命令内容
            
        Returns:
            tuple: (command, params) - 命令名称和参数
        """
        parts = content.split(' ', 1)
        command = parts[0].lower()  # 命令名称转为小写
        params = parts[1].strip() if len(parts) > 1 else ""
        
        return command, params
