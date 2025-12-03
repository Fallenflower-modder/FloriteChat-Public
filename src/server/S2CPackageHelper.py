import datetime
import logging
import json
import os

logger = logging.getLogger("ChatServer")


class S2CPackageHelper:
    @staticmethod
    def create_system_message(message, user="系统"):
        """
        创建系统消息
        
        Args:
            message: 消息内容
            user: 发送者（默认为"系统"）
            
        Returns:
            dict: 系统消息对象
        """
        return {
            "type": "system",
            "message": message,
            "user": user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_error_message(message):
        """
        创建错误消息
        
        Args:
            message: 错误消息内容
            
        Returns:
            dict: 错误消息对象
        """
        return {
            "type": "error",
            "message": message,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_command_response(message):
        """
        创建命令响应消息
        
        Args:
            message: 响应内容
            
        Returns:
            dict: 命令响应消息对象
        """
        return {
            "type": "command",
            "message": message,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_chat_message(message, sender, user=None, avatar=None):
        """
        创建聊天消息
        
        Args:
            message: 消息内容
            sender: 发送者
            user: 用户名称（默认为None，使用sender）
            avatar: 头像标识（默认为None）
            
        Returns:
            dict: 聊天消息对象
        """
        chat_message = {
            "type": "message",
            "message": message,
            "sender": sender,
            "user": user if user is not None else sender,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        if avatar:
            chat_message["avatar"] = avatar
        
        return chat_message
    
    @staticmethod
    def create_stream_message(message, sender, stream_id, stream_type="chunk", avatar=None):
        """
        创建流式消息（用于大模型响应）
        
        Args:
            message: 消息内容
            sender: 发送者
            stream_id: 流式响应ID
            stream_type: 流式类型（start/chunk/end）
            avatar: 头像标识
            
        Returns:
            dict: 流式消息对象
        """
        stream_message = {
            "type": "message",
            "message": message,
            "sender": sender,
            "user": sender,
            "stream_id": stream_id,
            "stream_type": stream_type,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        if avatar:
            stream_message["avatar"] = avatar
        
        return stream_message
        
    @staticmethod
    def create_sse_stream_message(message, event_type="chunk"):
        """
        创建SSE流式消息（用于大模型对话，对应@苹果派指令）
        
        Args:
            message: 消息内容
            event_type: 事件类型（start/chunk/end），默认为chunk
            
        Returns:
            dict: SSE流式消息对象
        """
        return {
            "type": "sse_stream",
            "message": message,
            "event_type": event_type,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
    @staticmethod
    def create_movie_message(url, sender="系统"):
        """
        创建电影消息（对应@电影指令）
        
        Args:
            url: 电影链接
            sender: 发送者
            
        Returns:
            dict: 电影消息对象
        """
        return {
            "type": "movie",
            "url": url,
            "sender": sender,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
    @staticmethod
    def create_hot_search_message(message, user="热搜榜", avatar="🔥"):
        """
        创建热搜消息（对应@热搜指令）
        
        Args:
            message: 热搜内容
            user: 发送者名称
            avatar: 头像标识
            
        Returns:
            dict: 热搜消息对象
        """
        hot_search_message = {
            "type": "hot_search",
            "message": message,
            "user": user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        if avatar:
            hot_search_message["avatar"] = avatar
            
        return hot_search_message
        
    @staticmethod
    def create_weather_card_message(weather_data, city, request_user):
        """
        创建天气卡片消息（对应@天气指令）
        
        Args:
            weather_data: 天气数据对象
            city: 城市名称
            request_user: 请求天气的用户
            
        Returns:
            dict: 天气卡片消息对象
        """
        return {
            "type": "weather_card",
            "city": city,
            "weather_data": weather_data,
            "request_user": request_user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_news_message(message, image_content=None, user="新闻资讯", avatar="📰"):
        """
        创建新闻消息（对应@新闻指令）
        
        Args:
            message: 新闻内容
            image_content: 图片内容信息（包含图片ID和路径）
            user: 发送者名称
            avatar: 头像标识
            
        Returns:
            dict: 新闻消息对象
        """
        # 确保消息内容不为空
        if not message:
            message = "暂无新闻内容"
        
        # 重写数据封装结构，确保包含所有必要字段
        news_message = {
            "type": "message",  # 使用message类型以便与普通消息处理方式一致
            "content": message,  # 使用content字段存储主要内容
            "message": message,  # 同时添加message字段以兼容客户端的严格检查
            "user": user,       # 保留user字段以确保兼容性
            "sender": user,     # 确保sender字段存在
            "news_type": "daily",  # 添加新闻类型标识
            "time": datetime.datetime.now().strftime("%H:%M:%S"),  # 确保time字段存在
            "has_image": False  # 默认为False
        }
        
        if avatar:
            news_message["avatar"] = avatar
            
        if image_content and isinstance(image_content, dict):
            # 确保图片信息结构完整
            news_message["has_image"] = True
            news_message["image_info"] = image_content  # 包含图片ID和路径等信息
            # 直接添加图片路径和ID供客户端使用
            # 修改图片路径为客户端images目录
            original_path = image_content.get("path", "")
            # 提取文件名，构建新路径
            image_filename = os.path.basename(original_path) if original_path else ""
            # 修改为正确的客户端图片路径
            news_message["image_path"] = f"src/client/images/{image_filename}" if image_filename else ""
            news_message["image_id"] = image_content.get("image_id", "")
        
        # 确保所有必要字段都有默认值，防止前端出现字段缺失错误
        if "image_path" not in news_message:
            news_message["image_path"] = ""
        if "image_id" not in news_message:
            news_message["image_id"] = ""
            
        logger.debug(f"创建新闻消息: {news_message}")
        return news_message
    
    @staticmethod
    def create_private_message(message, from_user):
        """
        创建私聊消息
        
        Args:
            message: 消息内容
            from_user: 发送者
            
        Returns:
            dict: 私聊消息对象
        """
        return {
            "type": "private_message",
            "message": message,
            "from": from_user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_private_message_sent(message, to_user):
        """
        创建私聊消息发送确认
        
        Args:
            message: 消息内容
            to_user: 接收者
            
        Returns:
            dict: 私聊发送确认消息对象
        """
        return {
            "type": "private_message_sent",
            "message": message,
            "to": to_user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_online_users_update_message(users):
        """
        创建在线用户列表更新消息
        
        Args:
            users: 在线用户列表
            
        Returns:
            dict: 在线用户更新消息对象
        """
        return {
            "type": "online_users_update",
            "online_users": users,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_login_response_message(success, message, user_data=None):
        """
        创建登录响应消息
        
        Args:
            success: 是否登录成功
            message: 响应消息内容
            user_data: 用户数据对象（登录成功时提供）
            
        Returns:
            dict: 登录响应消息对象
        """
        login_response = {
            "type": "login_response",
            "success": success,
            "message": message,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        if success and user_data:
            login_response["user_data"] = user_data
            
        return login_response
        
    @staticmethod
    def create_system_message_with_users(message, user="系统", online_users=None):
        """
        创建带用户列表的系统消息
        
        Args:
            message: 消息内容
            user: 发送者
            online_users: 在线用户列表
            
        Returns:
            dict: 带用户列表的系统消息对象
        """
        system_message = {
            "type": "system",
            "message": message,
            "user": user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        if online_users:
            system_message["online_users"] = online_users
            
        return system_message
    
    @staticmethod
    def create_register_response(success, message):
        """
        创建注册响应消息
        
        Args:
            success: 是否注册成功
            message: 响应消息内容
            
        Returns:
            dict: 注册响应消息对象
        """
        return {
            "type": "register_response",
            "success": success,
            "message": message,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_message(user, content, avatar=None):
        """
        创建常规消息
        
        Args:
            user: 发送者
            content: 消息内容
            avatar: 头像标识
            
        Returns:
            dict: 常规消息对象
        """
        message = {
            "type": "message",
            "content": content,
            "user": user,
            "sender": user,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        if avatar:
            message["avatar"] = avatar
            
        return message
    
    @staticmethod
    def create_room_joined_message(new_room):
        """
        创建房间加入确认消息
        
        Args:
            new_room: 新加入的房间名称
            
        Returns:
            dict: 房间加入确认消息对象
        """
        return {
            "type": "room_joined",
            "message": f"已加入房间: {new_room}",
            "room": new_room,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_heartbeat_response():
        """
        创建心跳响应消息
        
        Returns:
            dict: 心跳响应消息对象
        """
        return {
            "type": "pong",
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def create_music_message(api_url, sender, song_id):
        """
        创建音乐分享消息（对应@音乐指令）
        
        Args:
            api_url: 音乐API地址
            sender: 发送者
            song_id: 歌曲ID
            
        Returns:
            dict: 音乐分享消息对象
        """
        return {
            "type": "music",
            "api_url": api_url,
            "song_id": song_id,
            "sender": sender,
            "user": sender,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
    
    @staticmethod
    def serialize_message(message_data):
        """
        序列化消息数据为JSON字符串
        
        Args:
            message_data: 消息数据对象
            
        Returns:
            str or None: 序列化后的JSON字符串，失败返回None
        """
        try:
            return json.dumps(message_data)
        except Exception as e:
            logger.error(f"消息序列化失败: {str(e)}")
            return None
