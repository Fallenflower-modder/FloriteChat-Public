import random
import datetime

# 运势列表
fortunes = [
    "今天是你的幸运日，所有事情都会顺利进行！",
    "可能会有小挫折，但总体是个不错的一天。",
    "适合低调行事，避免不必要的风险。",
    "财富运势上升，可能会有意外收入。",
    "桃花运会很好，注意身边的人！",
    "工作运势极佳，适合展示自己的能力。",
    "需要注意健康，多休息多喝水。",
    "贵人运会出现，记得感恩。",
    "思维清晰，适合做重要决定。",
    "人缘会很好，适合社交活动。"
]

class FortuneHelper:
    """运势生成助手类"""
    
    @staticmethod
    def generate_fortune(username):
        """
        根据用户名和当前日期生成随机运势
        
        Args:
            username: 用户名
            
        Returns:
            生成的运势文本
        """
        # 为每个用户生成基于日期和昵称的随机运势
        seed = username + datetime.datetime.now().strftime('%Y%m%d')
        random.seed(seed)
        fortune = random.choice(fortunes)
        
        return fortune
    
    @staticmethod
    def format_fortune_response(username, fortune):
        """
        格式化运势响应消息
        
        Args:
            username: 用户名
            fortune: 运势内容
            
        Returns:
            格式化后的响应文本
        """
        return f"系统: {username} 的今日运势 - {fortune}"
