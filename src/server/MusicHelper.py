import os
import re

class MusicHelper:
    def __init__(self):
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建OickAPIConfig.txt文件的完整路径
        self.api_key_file = os.path.join(current_dir, 'OickAPIConfig.txt')
        # 定义网易云音乐链接的正则表达式
        self.music_url_pattern = r'https://music\.163\.com/#/song\?id=(\d+)'
    
    def get_api_key(self):
        """
        从OickAPIConfig.txt文件中读取APIKey
        """
        try:
            with open(self.api_key_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"读取APIKey失败: {e}")
            return None
    
    def extract_song_id(self, music_url):
        """
        从网易云音乐链接中提取歌曲ID
        """
        match = re.match(self.music_url_pattern, music_url)
        if match:
            return match.group(1)
        return None
    
    def construct_api_url(self, song_id):
        """
        构造完整的API地址
        """
        api_key = self.get_api_key()
        if not api_key:
            return None
        
        base_url = "https://api.oick.cn/api/wyy"
        return f"{base_url}?id={song_id}&apikey={api_key}"
    
    def process_music_command(self, music_url):
        """
        处理音乐指令的主方法
        """
        song_id = self.extract_song_id(music_url)
        if not song_id:
            return None, "无效的网易云音乐链接格式，请使用正确的格式：https://music.163.com/#/song?id={歌曲ID}"
        
        api_url = self.construct_api_url(song_id)
        if not api_url:
            return None, "API地址构造失败，请检查APIKey配置"
        
        return api_url, song_id