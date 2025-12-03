import requests
import json

class WeatherSpider:
    def __init__(self):
        # 使用WeatherSpider的API配置
        self.api_key = "d7af19e505ae006b"
        self.api_url = "https://v2.xxapi.cn/api/weather"
    
    def get_weather_data(self, city):
        """
        获取指定城市的天气数据
        返回适合FloriteChat使用的JSON格式
        """
        url = f"{self.api_url}?city={city}&key={self.api_key}"
        headers = {
            'User-Agent': 'xiaoxiaoapi/1.0.0'
        }
        
        try:
            response = requests.request("GET",url,headers=headers,data={})
            data = response.json()
            
            if data.get('code') == 200:
                api_data = data.get('data')
                return self.format_weather_data(city, api_data)
            else:
                print(f"API错误: {data.get('msg')}")
                return self.get_mock_weather_data(city)
        except Exception as e:
            print(f"请求天气数据失败: {str(e)}")
            # 返回模拟数据以便在API不可用时也能展示页面
            return self.get_mock_weather_data(city)
    
    def format_weather_data(self, city, api_data):
        """
        格式化天气数据为FloriteChat需要的格式
        """
        # 提取当前天气信息
        current_data = api_data[0] if api_data else {}
        
        # 构建符合FloriteChat格式的响应
        weather_info = {
            'city': city,
            'weather': current_data.get('weather', '未知'),
            'temperature': current_data.get('temperature', '0').split('-')[0] if current_data.get('temperature') else '0',
            'air_quality': current_data.get('air_quality', '未知'),
            'wind': current_data.get('wind', '无风'),
            'alert': self._generate_alert(current_data),
            'forecast': self._generate_forecast(api_data),
            'timestamp': self._get_current_time()
        }
        
        return weather_info
    
    def get_mock_weather_data(self, city):
        """
        提供模拟天气数据用于测试
        返回适合FloriteChat使用的格式
        """
        mock_data = {
            "city": city,
            "weather": "晴",
            "temperature": "19℃",
            "air_quality": "轻度",
            "wind": "北风1级",
            "alert": "暴雨与道路冰雪预警",
            "forecast": [
                {
                    "date": "周日",
                    "weather": "晴",
                    "temperature": "19℃"
                },
                {
                    "date": "周一",
                    "weather": "晴",
                    "temperature": "17℃"
                },
                {
                    "date": "周二",
                    "weather": "多云",
                    "temperature": "17℃"
                },
                {
                    "date": "周三",
                    "weather": "阴",
                    "temperature": "13℃"
                },
                {
                    "date": "周四",
                    "weather": "多云",
                    "temperature": "12℃"
                },
                {
                    "date": "周五",
                    "weather": "多云",
                    "temperature": "14℃"
                }
            ],
            "timestamp": self._get_current_time()
        }
        return mock_data
    
    def get_weather_icon(self, weather_desc):
        """
        根据天气描述返回对应的图标
        """
        weather_icons = {
            '晴': '☀️',
            '多云': '⛅',
            '阴': '☁️',
            '雨': '🌧️',
            '雪': '❄️',
            '雾': '🌫️'
        }
        
        for key, icon in weather_icons.items():
            if key in weather_desc:
                return icon
        return '🌤️'
    
    def _generate_alert(self, current_data):
        """
        生成天气预警信息
        """
        # 在实际应用中，这里可能会从API数据中提取真实的预警信息
        # 现在返回一个模拟的预警
        return "暴雨与道路冰雪预警"
    
    def _generate_forecast(self, api_data):
        """
        生成未来天气预报数据
        """
        forecast = []
        for day in api_data:
            forecast.append({
                "date": day.get('date', ''),
                "weather": day.get('weather', ''),
                "temperature": day.get('temperature', '').split('-')[0] if day.get('temperature') else ''
            })
        return forecast
    
    def _get_current_time(self):
        """
        获取当前时间
        """
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")
