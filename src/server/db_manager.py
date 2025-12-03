import sqlite3
import hashlib
import os

class DatabaseManager:
    def __init__(self, db_path='accounts.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库，创建用户表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 创建用户表，包含用户ID、用户名和密码哈希
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"数据库初始化错误: {e}")
        finally:
            if conn:
                conn.close()
    
    def _hash_password(self, password):
        """对密码进行哈希处理"""
        # 使用SHA-256算法哈希密码，并添加盐值增强安全性
        salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt + password_hash
    
    def _verify_password(self, stored_password, provided_password):
        """验证密码是否正确"""
        # 从存储的密码中提取盐值和哈希值
        salt = stored_password[:32]
        stored_hash = stored_password[32:]
        # 使用相同的盐值对提供的密码进行哈希
        password_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        # 比较哈希值是否匹配
        return password_hash == stored_hash
    
    def register_user(self, username, password):
        """注册新用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "用户名已存在"
            
            # 哈希密码
            password_hash = self._hash_password(password)
            
            # 插入新用户
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                          (username, password_hash))
            user_id = cursor.lastrowid
            conn.commit()
            return True, user_id
        except sqlite3.Error as e:
            print(f"注册用户错误: {e}")
            return False, "注册失败"
        finally:
            if conn:
                conn.close()
    
    def check_user_exists(self, username):
        """仅检查用户是否存在于数据库中，用于会话验证"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result is None:
                # 用户不存在
                return False, None
                
            user_id = result[0]
            return True, user_id
                
        except sqlite3.Error as e:
            print(f"检查用户是否存在时出错: {e}")
            return False, None
        finally:
            if conn:
                conn.close()
    
    def verify_user(self, username, password):
        """验证用户登录信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询用户信息
            cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                return False, None  # 用户不存在
            
            user_id, stored_password = result
            
            # 验证密码
            if self._verify_password(stored_password, password):
                return True, user_id  # 验证成功
            else:
                return False, None  # 密码错误
        except sqlite3.Error as e:
            print(f"验证用户错误: {e}")
            return False, None
        finally:
            if conn:
                conn.close()
    
    def get_user_by_id(self, user_id):
        """根据用户ID获取用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                return result[0]  # 返回用户名
            return None
        except sqlite3.Error as e:
            print(f"获取用户信息错误: {e}")
            return None
        finally:
            if conn:
                conn.close()

# 创建全局数据库管理器实例
db_manager = DatabaseManager()