import asyncio
import aiohttp
import datetime
import logging
import random
import json
import requests

# 导入我们集成的WeatherSpider类
from CustomLibrary.weather_spider import WeatherSpider

logger = logging.getLogger("ChatServer")

# 天气API配置
with open("src/server/LittleAPIConfig.json", "r") as f:
    WEATHER_API_KEY = json.load(f)["key"]


class WeatherHelper:
    @staticmethod
    async def get_weather_info(city):
        try:
            with open("src/server/LittleAPIConfig.json", "r") as f:
                api_key = json.load(f)["key"]

            re_url = f"https://v2.xxapi.cn/api/weather?city={city}&key={api_key}"

            headers = {
                'User-Agent': 'xiaoxiaoapi/1.0.0'
            }

            weather_response = eval(requests.request("GET",re_url,headers=headers,data={}).text)

            if weather_response["code"] == 200:
                weather_data = weather_response["data"]
                weather_data = WeatherHelper.restruct_weather_data(weather_data)
            else:
                raise Exception(f"获取天气数据失败: {weather_response['code']}")
            logger.info(f"成功获取{city}天气数据: {weather_response}")
            return True, weather_data
        except Exception as e:
            logger.error(f"获取天气信息异常: {str(e)}")
            # 异常时返回模拟数据
            # 修复：get_mock_weather_data是实例方法，需要先创建实例
            city = "未知"
            weather_spider = WeatherSpider()
            mock_data = await asyncio.to_thread(weather_spider.get_mock_weather_data, city)
            logger.warning(f"发生异常，使用模拟天气数据: {city}")
            return True, mock_data
    
    # 不再需要此方法，因为WeatherSpider已经提供了模拟数据功能
    # @staticmethod
    # def get_mock_weather_data(city):
    #     ...

    @staticmethod
    def ensure_weekday(today):
        if today == 0:
            today = "周一"
        elif today == 1:
            today = "周二"
        elif today == 2:
            today = "周三"
        elif today == 3:
            today = "周四"
        elif today == 4:
            today = "周五"
        elif today == 5:
            today = "周六"
        elif today == 6:
            today = "周日"
        elif today >= 7:
            today = WeatherHelper.ensure_weekday(today % 7)
        return today
    
    @staticmethod
    def restruct_weather_data(weather_data):
        num_today = datetime.datetime.today().weekday()
        today = WeatherHelper.ensure_weekday(num_today)
        result = {
            "city": weather_data["city"],
            "weather":"未知",
            "temperature":"0℃",
            "air_quality":"未知",
            "wind":"未知",
            "forecast":[]
        }
        for item in weather_data["data"]:
            if item["date"] == today:
                result["weather"] = item["weather"]
                result["temperature"] = item["temperature"]
                result["air_quality"] = item["air_quality"]
                result["wind"] = item["wind"]
                break
        count = 0
        times = 1
        while count < len(weather_data["data"])-times:
            founded = False
            num_today += 1
            today = WeatherHelper.ensure_weekday(num_today)
            for item in weather_data["data"]:
                if item["date"] == today:
                    result["forecast"].append({
                        "date": item["date"],
                        "weather": item["weather"],
                        "temperature": item["temperature"],
                        "air_quality": item["air_quality"],
                        "wind": item["wind"]
                    })
                    count += 1
                    founded = True
                    break
            if not founded:
                times += 1
        return result

    @staticmethod
    async def format_weather_card(weather_data, city):
        """
        将天气数据格式化为天气卡片消息
        
        Args:
            weather_data: 天气API返回的数据
            city: 城市名称
            
        Returns:
            dict: 格式化后的天气卡片消息
        """
        try:
            # 提取当前天气信息和预报数据
            forecast_data = []
            
            # 处理WeatherSpider格式的数据结构
            if isinstance(weather_data, dict):
                # 提取城市名称
                city_name = weather_data["city"]
                
                # 提取当前天气信息（直接从weather_data中获取）
                weather_status = weather_data["weather"]
                temperature = weather_data.get('temperature', '未知')
                air_quality = weather_data.get('air_quality', '未知')
                wind_info = weather_data.get('wind', '无风')
                
                # 提取预报数据（从'forecast'字段获取）
                if 'forecast' in weather_data and isinstance(weather_data['forecast'], list):
                    forecast_data = weather_data['forecast']
            else:
                # 如果数据不是预期格式，使用默认值
                city_name = city
                weather_status = '未知'
                temperature = '未知'
                air_quality = '未知'
                wind_info = '无风'
            
            # 添加天气图标（参考WeatherSpider）
            weather_icon = WeatherHelper.get_weather_icon(weather_status)
            
            # 构建完整的天气卡片消息，包含当前天气和预报数据
            weather_card = {
                "type": "weather_card",
                "city": city_name,
                "weather": weather_status,
                "weather_icon": weather_icon,
                "temperature": temperature,
                "air_quality": air_quality,
                "wind": wind_info,
                "forecast": forecast_data,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"已格式化天气卡片: {city_name}")
            return weather_card
        except Exception as e:
            logger.error(f"格式化天气卡片异常: {str(e)}")
            # 返回基本的错误信息卡片
            return {
                "type": "weather_card",
                "city": city,
                "weather": "未知",
                "weather_icon": "🌤️",
                "temperature": "未知",
                "air_quality": "未知",
                "wind": "",
                "forecast": [],
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    @staticmethod
    def get_weather_icon(weather_desc):
        """
        使用WeatherSpider的天气图标映射逻辑
        
        Args:
            weather_desc: 天气描述文本
            
        Returns:
            str: 天气图标
        """
        # 修复：get_weather_icon是实例方法，需要先创建实例
        weather_spider = WeatherSpider()
        return weather_spider.get_weather_icon(weather_desc)


