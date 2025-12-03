import sqlite3
import logging
import os
from passlib.hash import pbkdf2_sha256

logger = logging.getLogger("ChatServer")


class DataBaseHelper:
    def __init__(self, db_path="users.db"):
        """
        初始化数据库助手
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """
        初始化数据库，创建用户表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    avatar TEXT DEFAULT NULL,
                    status TEXT DEFAULT 'offline',
                    last_login TEXT DEFAULT NULL
                )
            ''')
            
            # 创建默认管理员用户（如果不存在）
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_password = pbkdf2_sha256.hash("admin123")
                cursor.execute(
                    "INSERT INTO users (username, password, avatar, status) VALUES (?, ?, ?, ?)",
                    ('admin', admin_password, 'admin', 'online')
                )
                logger.info("默认管理员用户已创建")
            
            conn.commit()
            conn.close()
            logger.info(f"数据库初始化完成: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def register_user(self, username, password, avatar=None):
        """
        注册新用户
        
        Args:
            username: 用户名
            password: 明文密码
            avatar: 头像标识（可选）
            
        Returns:
            tuple: (success, message) - (是否成功, 消息)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, "用户名已存在"
            
            # 哈希密码
            hashed_password = pbkdf2_sha256.hash(password)
            
            # 插入新用户
            cursor.execute(
                "INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)",
                (username, hashed_password, avatar)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"用户注册成功: {username}")
            return True, "注册成功"
        except Exception as e:
            logger.error(f"用户注册失败: {str(e)}")
            return False, f"注册失败: {str(e)}"
    
    def verify_user(self, username, password):
        """
        验证用户登录
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            tuple: (success, user_data) - (是否成功, 用户数据)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找用户
            cursor.execute("SELECT id, username, password, avatar FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, None
            
            # 验证密码
            if pbkdf2_sha256.verify(password, user[2]):
                # 更新用户状态
                cursor.execute("UPDATE users SET status = 'online' WHERE id = ?", (user[0],))
                conn.commit()
                conn.close()
                
                user_data = {
                    "id": user[0],
                    "username": user[1],
                    "avatar": user[3]
                }
                logger.info(f"用户登录成功: {username}")
                return True, user_data
            else:
                conn.close()
                return False, None
        except Exception as e:
            logger.error(f"用户验证失败: {str(e)}")
            return False, None
    
    def update_user_status(self, username, status):
        """
        更新用户状态
        
        Args:
            username: 用户名
            status: 状态值（online/offline）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = ? WHERE username = ?", (status, username))
            conn.commit()
            conn.close()
            logger.info(f"用户状态已更新: {username} -> {status}")
        except Exception as e:
            logger.error(f"更新用户状态失败: {str(e)}")
    
    def get_user_avatar(self, username):
        """
        获取用户头像
        
        Args:
            username: 用户名
            
        Returns:
            str or None: 头像标识，不存在返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT avatar FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"获取用户头像失败: {str(e)}")
            return None
    
    def update_user_avatar(self, username, avatar):
        """
        更新用户头像
        
        Args:
            username: 用户名
            avatar: 头像标识
            
        Returns:
            bool: 是否更新成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET avatar = ? WHERE username = ?", (avatar, username))
            conn.commit()
            conn.close()
            logger.info(f"用户头像已更新: {username}")
            return True
        except Exception as e:
            logger.error(f"更新用户头像失败: {str(e)}")
            return False
    
    def get_online_users(self):
        """
        获取在线用户列表
        
        Returns:
            list: 在线用户列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT username, avatar FROM users WHERE status = 'online'")
            users = cursor.fetchall()
            conn.close()
            
            online_users = []
            for user in users:
                online_users.append({
                    "username": user[0],
                    "avatar": user[1] if user[1] else None
                })
            
            return online_users
        except Exception as e:
            logger.error(f"获取在线用户失败: {str(e)}")
            return []
    
    def check_user_exists(self, username):
        """
        检查用户是否存在
        
        Args:
            username: 用户名
            
        Returns:
            tuple: (success, user_data) - (是否成功, 用户数据)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, avatar FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                user_data = {
                    "id": result[0],
                    "username": result[1],
                    "avatar": result[2] if result[2] else None
                }
                return True, user_data
            else:
                return False, None
        except Exception as e:
            logger.error(f"检查用户存在性失败: {str(e)}")
            return False, None
