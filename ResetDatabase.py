import sqlite3
import os
from passlib.hash import pbkdf2_sha256

# 定义数据库路径
db_path = 'users.db'

def reset_database(keep_admin=True):
    """
    重置数据库：清空users表中的所有账户数据
    
    Args:
        keep_admin: 是否保留默认管理员用户
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"数据库文件 {db_path} 不存在！")
            return False
        
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 清空users表中的所有数据
        cursor.execute("DELETE FROM users")
        print(f"已清空 {db_path} 中的所有账户数据！")
        
        # 如果需要保留默认管理员用户，则重新创建
        if keep_admin:
            admin_password = pbkdf2_sha256.hash("2Sir,wtndydlpn?")
            cursor.execute(
                "INSERT INTO users (username, password, avatar, status) VALUES (?, ?, ?, ?)",
                ('DrownedCloud', admin_password, 'admin', 'online')
            )
            print("已重新创建默认管理员用户: DrownedCloud (密码: 2Sir,wtndydlpn?)")
        
        conn.commit()
        print("数据库重置操作已提交！")
        
        # 关闭数据库连接
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False

if __name__ == "__main__":
    print("=== 数据库重置工具 ===")
    print("此工具将清空users.db中的所有账户数据")
    print("默认会保留管理员账户(DrownedCloud/2Sir,wtndydlpn?)")
    print()
    
    # 获取用户确认
    confirm = input("是否继续执行？(y/n): ").strip().lower()
    if confirm != 'y':
        print("操作已取消！")
        exit()
    
    print()
    print("正在重置数据库...")
    success = reset_database()
    
    print()
    if success:
        print("✅ 数据库重置完成！")
    else:
        print("❌ 数据库重置失败！")