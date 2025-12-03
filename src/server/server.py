import asyncio
import websockets
import json
import random
import datetime
import re
import os
import logging
import uuid
import time
import aiohttp
import traceback

# 导入功能模块
from FortuneHelper import FortuneHelper
from WeatherHelper import WeatherHelper
from HotSearchHelper import HotSearchHelper
from FilmHelper import FilmHelper
from SixtySecondHelper import SixtySecondHelper
from MusicHelper import MusicHelper
from C2SPraser import C2SPraser
from S2CPackageHelper import S2CPackageHelper
from DataBaseHelper import DataBaseHelper

# 初始化数据库管理器
db_manager = DataBaseHelper()

# 配置日志系统
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
# 修改日志文件名格式为：chat-server-{日期编号}-{服务端启动时间编号（时分秒）}.log
current_time = datetime.datetime.now()
log_file = os.path.join(log_dir, f"chat-server-{current_time.strftime('%Y%m%d')}-{current_time.strftime('%H%M%S')}.log")

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ChatServer")

# 移除硬编码的天气API配置，使用WeatherHelper中的配置

# 存储所有连接的客户端
active_clients = {}
# 存储所有在线用户
online_users = set()
# 用于保护共享资源的锁
clients_lock = asyncio.Lock()

# Chatbot配置和提示词
chatbot_config = {}
chatbot_tips = ""

# 加载chatbot配置和提示词
def load_chatbot_config():
    """加载聊天机器人配置和提示词"""
    global chatbot_config, chatbot_tips
    
    # 加载配置文件
    config_path = os.path.join(os.path.dirname(__file__), 'chatbot-config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            chatbot_config = json.load(f)
        logger.info(f"成功加载chatbot配置: {config_path}")
    except Exception as e:
        logger.error(f"加载chatbot配置失败: {str(e)}")
        chatbot_config = {"api_key": "", "model_name": "gpt-3.5-turbo", "enabled": False}
    
    # 加载提示词文件
    tips_path = os.path.join(os.path.dirname(__file__), 'chatbot-tips.txt')
    try:
        with open(tips_path, 'r', encoding='utf-8') as f:
            chatbot_tips = f.read().strip()
        logger.info(f"成功加载chatbot提示词: {tips_path}")
    except Exception as e:
        logger.error(f"加载chatbot提示词失败: {str(e)}")
        chatbot_tips = "你是一个友好的聊天助手。"

# 运势列表和天气信息获取函数已移至对应模块
# 使用FortuneHelper和WeatherHelper代替

# 定义获取天气信息的异步函数，调用WeatherHelper
async def get_weather_info(city):
    """
    获取指定城市的天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        tuple: (success, data) - success为布尔值表示是否成功，data为天气数据或错误信息
    """
    return await WeatherHelper.get_weather_info(city)

# format_weather_card函数已移至WeatherHelper类中

# 获取百度热搜列表
async def get_baidu_hot_search():
    """从百度获取热搜列表"""
    # 调用HotSearchHelper来获取热搜数据
    return await HotSearchHelper.get_baidu_hot_search()

# 格式化热搜内容为卡片形式
def format_hot_searches(hot_searches):
    """将热搜列表格式化为卡片展示形式"""
    # 调用HotSearchHelper来格式化热搜内容
    return HotSearchHelper.format_hot_searches(hot_searches)

# 大模型API调用函数 - 支持流式响应
async def call_llm_api(prompt, stream=False, on_chunk=None):
    """调用大模型API获取回复，支持流式响应
    
    Args:
        prompt: 用户提问
        stream: 是否使用流式响应
        on_chunk: 流式响应回调函数，接收单个文本片段
        
    Returns:
        完整响应文本（非流式时）
    """
    global chatbot_config, chatbot_tips
    
    # 检查配置是否有效
    if not chatbot_config.get('enabled') or not chatbot_config.get('api_key'):
        logger.warning("大模型对话功能未启用或API密钥未配置")
        error_msg = "抱歉，大模型对话功能暂未启用。请联系管理员配置API密钥。"
        if on_chunk:
            await on_chunk(error_msg)
        return error_msg
    
    try:
        # 构建消息列表，包含系统提示和用户消息
        messages = [
            {"role": "system", "content": chatbot_tips},
            {"role": "user", "content": prompt}
        ]
        
        # 准备请求数据，启用stream参数
        request_data = {
            "model": chatbot_config.get("model_name", "gpt-3.5-turbo"),
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
            "stream": stream  # 启用流式响应
        }
        
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {chatbot_config['api_key']}"
        }
        
        # 发送异步请求
        async with aiohttp.ClientSession() as session:
            api_base = chatbot_config.get("api_base", "https://api.openai.com/v1")
            url = f"{api_base}/chat/completions"
            
            if stream:
                # 流式响应处理
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        full_response = ""
                        # 逐行读取流式响应
                        async for line in response.content:
                            if line.strip():
                                # 处理SSE格式的响应行
                                line_str = line.decode('utf-8').strip()
                                # 跳过data: [DONE] 结束标记
                                if line_str == 'data: [DONE]':
                                    break
                                # 提取data: 后面的JSON部分
                                if line_str.startswith('data: '):
                                    json_str = line_str[6:]
                                    try:
                                        chunk_data = json.loads(json_str)
                                        # 提取文本片段
                                        if chunk_data.get('choices'):
                                            delta = chunk_data['choices'][0].get('delta', {})
                                            if 'content' in delta:
                                                chunk_text = delta['content']
                                                full_response += chunk_text
                                                # 调用回调函数处理文本片段
                                                if on_chunk:
                                                    await on_chunk(chunk_text)
                                    except json.JSONDecodeError:
                                        logger.warning(f"解析流式响应失败: {json_str}")
                        return full_response.strip()
                    else:
                        error_msg = f"抱歉，调用大模型API时出错 (HTTP {response.status})"
                        logger.error(f"大模型API调用失败: HTTP {response.status}, {await response.text()}")
                        if on_chunk:
                            await on_chunk(error_msg)
                        return error_msg
            else:
                # 非流式响应处理（保持原有逻辑）
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        error_msg = f"抱歉，调用大模型API时出错 (HTTP {response.status})"
                        logger.error(f"大模型API调用失败: HTTP {response.status}, {await response.text()}")
                        return error_msg
    
    except Exception as e:
        logger.error(f"大模型API调用异常: {str(e)}")
        logger.debug(traceback.format_exc())
        error_msg = f"抱歉，调用大模型API时发生异常: {str(e)}"
        if on_chunk:
            await on_chunk(error_msg)
        return error_msg

# 处理@命令
async def handle_at_command(message, user_info):
    """处理@命令消息"""
    sender = user_info['name']
    logger.info(f"开始处理@命令: '{message}' from {sender}")
    
    if message.startswith('@运势'):
        # 使用FortuneHelper处理运势查询
        logger.info(f"处理@运势命令 for {sender}")
        # 获取运势信息
        fortune_message = S2CPackageHelper.create_command_response(FortuneHelper.format_fortune_response(sender,FortuneHelper.generate_fortune(sender)))
        # 发送给指定用户
        await user_info['websocket'].send(json.dumps(fortune_message))
        logger.info(f"{sender} 请求运势，响应发送成功")
    
    elif message.startswith('@电影'):
        # 使用FilmHelper处理电影链接
        url = FilmHelper.extract_movie_url(message)
        if url:
            # 使用S2CPackageHelper创建电影消息
            movie_message = S2CPackageHelper.create_movie_message(url, sender)
            # 广播电影播放消息
            await broadcast_message(movie_message, room=user_info['room'])
            logger.info(f"{sender} 发送了电影链接: {url}")
        else:
            # 使用S2CPackageHelper创建错误消息
            error_message = S2CPackageHelper.create_error_message("请提供电影链接，格式为 @电影 URL")
            await user_info['websocket'].send(json.dumps(error_message))
    
    elif message.startswith('@热搜'):
        # 处理热搜指令
        logger.info(f"处理@热搜命令 for {sender}")
        
        # 首先向发送者发送一个正在获取的提示
        command_message = S2CPackageHelper.create_command_response("正在获取最新热搜榜单...")
        await user_info['websocket'].send(json.dumps(command_message))
        
        # 获取百度热搜列表
        hot_searches = await get_baidu_hot_search()
        
        # 格式化热搜内容为卡片形式
        formatted_content = format_hot_searches(hot_searches)
        
        # 使用S2CPackageHelper创建热搜消息
        hot_search_message = S2CPackageHelper.create_hot_search_message(hot_searches)
        # 广播热搜内容给所有用户
        await broadcast_message(hot_search_message, room=user_info['room'])
        
        logger.info(f"热搜列表已发送，共 {len(hot_searches)} 条")
        
    elif message.startswith('@音乐'):
        # 处理音乐指令
        logger.info(f"处理@音乐命令 for {sender}")
        
        # 提取音乐链接
        music_url = message[len('@音乐'):].strip()
        if not music_url:
            # 使用S2CPackageHelper创建错误消息
            error_message = S2CPackageHelper.create_error_message("请提供网易云音乐链接，格式为 @音乐 URL")
            await user_info['websocket'].send(json.dumps(error_message))
            return
        
        try:
            # 创建MusicHelper实例
            music_helper = MusicHelper()
            # 处理音乐链接
            api_url, song_id = music_helper.process_music_command(music_url)
            
            if not api_url:
                error_message = S2CPackageHelper.create_error_message("无效的网易云音乐链接格式，请使用正确的格式：https://music.163.com/#/song?id={歌曲ID}")
                await user_info['websocket'].send(json.dumps(error_message))
                return
            
            # 使用S2CPackageHelper创建音乐消息
            music_message = S2CPackageHelper.create_music_message(api_url, sender, song_id)
            # 广播音乐消息
            await broadcast_message(music_message, room=user_info['room'])
            logger.info(f"{sender} 分享了音乐: {music_url}，API地址: {api_url}")
            
        except Exception as e:
            logger.error(f"处理音乐时出错: {str(e)}", exc_info=True)
            error_message = S2CPackageHelper.create_error_message("处理音乐链接失败，请稍后重试")
            await user_info['websocket'].send(json.dumps(error_message))
    
    elif message.startswith('@新闻'):
        # 处理新闻指令
        logger.info(f"处理@新闻命令 for {sender}")
        
        # 首先向发送者发送一个正在获取的提示
        command_message = S2CPackageHelper.create_command_response("正在获取最新新闻资讯...")
        await user_info['websocket'].send(json.dumps(command_message))
        
        try:
            # 异步调用SixtySecondHelper的main函数
            logger.info("异步调用SixtySecondHelper.main()")
            # 使用asyncio.to_thread来在单独的线程中运行同步函数
            success = await asyncio.to_thread(SixtySecondHelper.main)
            
            logger.info(f"SixtySecondHelper.main() 返回结果: {success}")
            
            # 新闻文本内容（默认内容）
            news_content = "每天60秒，看懂世界。"
            
            # 图片路径 - 指向客户端src/client/images目录下的news.png
            image_filename = "news.png"
            image_path = f"src/client/images/{image_filename}"
            # 本地图片路径（服务器端用于检查文件是否存在）
            local_image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client", "images", "news.png")
            has_image = success and os.path.exists(local_image_path)
            
            logger.info(f"新闻图片存在检查: {has_image}")
            
            # 图片信息对象
            image_content = None
            if has_image:
                # 生成唯一的图片ID
                image_id = f"news_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                image_content = {
                    "image_id": image_id,
                    "path": image_path,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # 创建一个图片预加载消息
                image_preload_message = {
                    "type": "image_preload",
                    "image_id": image_id,
                    "image_path": image_path,
                    "time": datetime.datetime.now().strftime("%H:%M:%S")
                }
                
                logger.info(f"发送图片预加载消息: {image_id}，路径: {image_path}")
                # 广播图片预加载消息给所有用户
                await broadcast_message(image_preload_message, room=user_info['room'])
                
                # 添加延迟确保图片预加载消息先到达客户端
                # 后续会添加等待客户端加载完成信号的逻辑
                await asyncio.sleep(1.0)
            
            # 使用S2CPackageHelper创建新闻消息，使用新的数据结构
            news_message = S2CPackageHelper.create_news_message(news_content, image_content=image_content)
            
            # 广播新闻内容给所有用户
            # 注意：后续会修改为等待客户端加载完成信号后再发送
            logger.info(f"准备发送新闻消息，等待图片预加载完成")
            await broadcast_message(news_message, room=user_info['room'])
            
            logger.info(f"新闻资讯已发送，图片状态: {'已包含' if has_image else '未包含'}")
            
        except Exception as e:
            logger.error(f"处理新闻时出错: {str(e)}", exc_info=True)
            error_message = S2CPackageHelper.create_error_message("获取新闻资讯失败")
            await user_info['websocket'].send(json.dumps(error_message))
        
    elif message.startswith('@苹果派'):
            # 检查是否启用流式响应
            use_stream = chatbot_config.get("enabled", True)
            
            if not use_stream:
                # 非流式响应模式
                logger.info(f"处理@苹果派命令（非流式）for {sender}")
                sender = user_info['name']
                user_message = message[len('@苹果派'):].strip()
                
                if not user_message:
                    response = "🍎 苹果派: 你好！我是苹果派AI助手，有什么可以帮助你的吗？\n⚠服务器未启用大模型对话，你将只能收到这一条回复！⚠"
                    response_data = {
                        "type": "command",
                        "message": response,
                        "time": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                    await user_info['websocket'].send(json.dumps(response_data))
                else:
                    # 广播用户的原始问题消息
                    await broadcast_message({
                        "type": "message",
                        "message": message,
                        "user": sender,
                        "sender": sender
                    }, room=user_info['room'])
                    
                    # 调用大模型API获取完整响应
                    response = await call_llm_api(user_message, stream=False)
                    
                    # 使用S2CPackageHelper创建非流式苹果派消息
                    response_data = S2CPackageHelper.create_message("苹果派", response)
                    
                    await broadcast_message(response_data, room=user_info['room'])
            else:
                # 大模型对话功能 - 使用SSE协议返回流式响应
                logger.info(f"处理@苹果派命令（流式）for {sender}")
                sender = user_info['name']
                # 提取用户实际的对话内容（去掉@苹果派前缀）
                user_message = message[len('@苹果派'):].strip()
                
                if not user_message:
                    # 如果用户没有提供具体问题，发送提示消息
                    response = "🍎 苹果派: 你好！我是苹果派AI助手，有什么可以帮助你的吗？"
                    response_data = {
                        "type": "command",
                        "message": response,
                        "time": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                    logger.info(f"{sender} 请求苹果派，准备发送提示: {response_data}")
                    await user_info['websocket'].send(json.dumps(response_data))
                else:
                    logger.info(f"{sender} 请求大模型对话: {user_message}")
                    
                    # 生成唯一的响应ID，用于跟踪流式响应
                    response_id = str(uuid.uuid4())[:8]
                    
                    # 累积完整响应
                    full_response = ""
                    
                    # 发送SSE开始信号
                    start_sse_message = S2CPackageHelper.create_sse_stream_message("", event_type="start")
                    await broadcast_message(start_sse_message, room=user_info['room'])
                    logger.info(f"发送SSE流式响应开始信号")
                    
                    # 定义流式响应的回调函数
                    async def on_chunk(chunk_text):
                        nonlocal full_response
                        full_response += chunk_text
                        
                        # 使用S2CPackageHelper创建sse_stream消息
                        sse_message = S2CPackageHelper.create_sse_stream_message(chunk_text)
                        # 广播文本片段作为SSE消息
                        await broadcast_message(sse_message, room=user_info['room'])
                        
                        logger.debug(f"发送流式响应片段，长度: {len(chunk_text)}")
                    
                    # 使用流式API调用大模型
                    await call_llm_api(user_message, stream=True, on_chunk=on_chunk)
                    
                    # 发送SSE结束信号
                    end_sse_message = S2CPackageHelper.create_sse_stream_message("", event_type="end")
                    await broadcast_message(end_sse_message, room=user_info['room'])
                    logger.info(f"发送SSE流式响应结束信号")
                    logger.info(f"大模型流式回复完成，总内容长度: {len(full_response)} 字符")
    
    elif message.startswith('@天气'):
        # 处理天气查询指令
        logger.info(f"处理@天气命令 for {sender}")
        sender = user_info['name']
        # 提取城市名称（去掉@天气前缀）
        parts = message.split(' ', 1)
        if len(parts) > 1:
            city = parts[1].strip()
            logger.info(f"{sender} 请求天气信息: {city}")
            
            # 首先向发送者发送一个正在获取的提示
            response_data = S2CPackageHelper.create_command_response(f"正在获取{city}的天气信息...")
            logger.info(f"{sender} 请求天气，准备发送提示: {response_data}")
            await user_info['websocket'].send(json.dumps(response_data))
            
            # 获取天气信息
            success, weather_data = await get_weather_info(city)
            
            if success:
                # 格式化天气数据为天气卡片
                weather_card = await WeatherHelper.format_weather_card(weather_data, city)
                # 使用S2CPackageHelper创建天气卡片消息
                weather_card_message = S2CPackageHelper.create_weather_card_message(weather_card, city, sender)
                # 广播天气卡片给所有用户
                await broadcast_message(weather_card_message, room=user_info['room'])
                logger.info(f"天气信息已发送: {city}")
            else:
                # 使用S2CPackageHelper创建错误消息
                response_data = S2CPackageHelper.create_error_message(weather_data)  # weather_data包含错误信息
                logger.info(f"{sender} 请求天气失败，准备发送错误: {response_data}")
                await user_info['websocket'].send(json.dumps(response_data))
        else:
            # 使用S2CPackageHelper创建错误消息
            response_data = S2CPackageHelper.create_error_message("请提供地名，格式: @天气 <地名>")
            logger.info(f"{sender} @天气命令格式错误，准备发送错误: {response_data}")
            await user_info['websocket'].send(json.dumps(response_data))

    elif '@' in message and len(message) > 1:
        # 处理@用户的情况
        logger.info(f"处理@用户私聊命令 from {sender}: {message}")
        parts = message.split(' ', 1)
        if len(parts) > 1:
            target_user = parts[0][1:]  # 去掉@符号
            content = parts[1]
            
            # 查找目标用户
            found = False
            for client_id, client_info in active_clients.items():
                if client_info['name'] == target_user:
                    # 使用S2CPackageHelper创建私聊消息
                    private_message = S2CPackageHelper.create_private_message(content, sender)
                    await client_info['websocket'].send(json.dumps(private_message))
                    
                    # 使用S2CPackageHelper创建私聊发送确认消息
                    private_sent_message = S2CPackageHelper.create_private_message_sent(content, target_user)
                    await user_info['websocket'].send(json.dumps(private_sent_message))
                    
                    found = True
                    logger.info(f"私聊消息 from {sender} to {target_user}: {content}")
                    break
            
            if not found:
                # 使用S2CPackageHelper创建错误消息
                error_message = S2CPackageHelper.create_error_message(f"用户 {target_user} 不在线或不存在")
                await user_info['websocket'].send(json.dumps(error_message))

async def send_active_users(room=None):
    """发送在线用户列表给指定房间或所有客户端"""
    logger.info(f"开始发送在线用户列表，房间: {room}")
    
    # 使用锁保护共享资源访问
    async with clients_lock:
        # 获取指定房间的在线用户列表
        if room:
            users = [client_info['name'] for client_id, client_info in active_clients.items() 
                    if client_info['room'] == room]
        else:
            users = [client_info['name'] for client_id, client_info in active_clients.items()]
    
    logger.info(f"准备广播在线用户列表，用户数量: {len(users)}")
    
    # 使用S2CPackageHelper创建在线用户更新消息
    online_users_message = S2CPackageHelper.create_online_users_update_message(users)
    
    # 广播在线用户列表
    await broadcast_message(online_users_message, room=room)
    
    logger.info("在线用户列表广播完成")

async def broadcast_message(message, room=None, exclude_client=None):
    """广播消息给所有客户端或指定房间的客户端，优化版"""
    logger.info(f"开始广播消息，类型: {message.get('type')}，房间: {room}，排除客户端: {exclude_client}")
    
    message_data = {
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }
    message_data.update(message)
    
    # 确保消息格式兼容客户端期望
    # 客户端期望'sender'字段，而不是'user'字段
    if 'user' in message_data and 'sender' not in message_data:
        message_data['sender'] = message_data['user']
    
    # 预先准备好消息的JSON字符串
    message_json = json.dumps(message_data)
    
    # 使用锁保护共享资源访问并获取要发送的客户端列表
    async with clients_lock:
        clients_to_send = []
        for client_id, client_info in active_clients.items():
            # 排除指定客户端
            if exclude_client and client_id == exclude_client:
                continue
            # 如果指定了房间，只发送给该房间的客户端
            if room and client_info['room'] != room:
                continue
            clients_to_send.append((client_id, client_info))
    
    logger.info(f"准备向 {len(clients_to_send)} 个客户端发送消息: {message_data}")
    
    # 收集断开连接的客户端，稍后一次性处理
    disconnected_clients = []
    disconnected_users = []
    
    # 向每个客户端发送消息，避免一个客户端的失败影响其他客户端
    for client_id, client_info in clients_to_send:
        try:
            # 记录发送的消息详情
            if client_info.get('authenticated') and client_info.get('name'):
                logger.info(f"向客户端 {client_id} (用户: {client_info['name']}) 广播消息: {message_data.get('type')}")
            else:
                logger.info(f"向未认证客户端 {client_id} 广播消息: {message_data.get('type')}")
            
            await client_info['websocket'].send(message_json)
            logger.debug(f"成功发送消息给客户端 {client_id} ({client_info['name']})")
        except Exception as e:
            logger.error(f"发送消息给客户端 {client_id} ({client_info['name']}) 时出错: {str(e)}")
            # 记录断开连接的客户端，稍后统一处理
            disconnected_clients.append(client_id)
            disconnected_users.append(client_info['name'])
    
    # 批量处理断开连接的客户端
    if disconnected_clients:
        logger.info(f"开始批量清理 {len(disconnected_clients)} 个断开连接的客户端")
        
        # 一次性从active_clients中删除所有断开连接的客户端
        async with clients_lock:
            for client_id in disconnected_clients:
                if client_id in active_clients:
                    del active_clients[client_id]
        
        # 如果有用户断开连接，发送一条统一的系统消息和更新用户列表
        if disconnected_users:
            users_str = "、".join(disconnected_users)
            system_message = S2CPackageHelper.create_system_message(f"{users_str} 连接中断")
            await broadcast_message(system_message, exclude_client=exclude_client)
            # 更新在线用户列表
            await send_active_users()
    
    logger.info("消息广播完成")

# 处理客户端连接的协程函数
async def handle_client(*args):
    """处理单个客户端连接（兼容格式）
    
    兼容不同版本的websockets库调用方式，既支持单个参数也支持两个参数
    
    Args:
        websocket: WebSocket连接对象
        path: 连接路径（websockets.serve要求的参数）
    """
    # 判断参数情况
    if len(args) == 1:
        websocket = args[0]
        path = "/"  # 默认路径
    elif len(args) == 2:
        websocket, path = args
    else:
        logger.error(f"收到无效的参数数量: {len(args)}")
        return
        
    client_id = str(uuid.uuid4())[:8]
    user_info = {
        "id": client_id,
        "name": f"Guest_{client_id}",
        "websocket": websocket,
        "room": "lobby",
        "last_activity": time.time(),
        "authenticated": False,  # 添加认证状态标志
        "user_id": None  # 添加用户ID字段，用于存储数据库中的用户ID
    }
    
    try:
        logger.info(f"新客户端连接: {user_info['name']} (ID: {client_id})")
        # 使用锁保护共享资源访问
        async with clients_lock:
            active_clients[client_id] = user_info
        
        # 发送欢迎消息
        welcome_message = S2CPackageHelper.create_system_message(f"欢迎加入FloriteChat！您的临时ID是: {client_id}")
        await websocket.send(json.dumps(welcome_message))
        
        # 不再广播初始临时ID的加入消息，只在用户设置昵称后广播一条加入消息
        
        # 定期更新活动时间的任务
        async def heartbeat():
            while True:
                try:
                    await asyncio.sleep(10)
                    if client_id in active_clients:
                        active_clients[client_id]['last_activity'] = time.time()
                        logger.debug(f"更新客户端活动时间: {client_id}")
                except:
                    break
        
        # 启动心跳任务
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # 接收消息循环
        while True:
            # 设置接收超时，避免连接长时间空闲
            try:
                # 等待消息，设置超时
                message = await asyncio.wait_for(websocket.recv(), timeout=30)
                
                # 跳过空消息
                if not message:
                    continue
                    
                # 更新最后活动时间
                active_clients[client_id]['last_activity'] = time.time()
                
                # 处理ping响应
                if message == "pong":
                    logger.debug(f"收到客户端 {client_id} 的pong响应")
                    continue
                # 处理ping响应
                elif message == "ping":
                    # 使用S2CPackageHelper创建心跳响应消息
                    pong_message = S2CPackageHelper.create_heartbeat_response()
                    await websocket.send(json.dumps(pong_message))
                    logger.debug(f"向客户端 {client_id} 发送pong响应")
                    continue
                
                # 尝试解析JSON消息
                try:
                    data = json.loads(message)
                    logger.info(f"收到消息 from {user_info['name']}: {data}")
                    
                    # 处理注册请求
                    if data.get('type') == 'register':
                        username = data.get('username')
                        password = data.get('password')
                        
                        if not username or not password:
                            # 使用S2CPackageHelper创建注册响应消息
                            response_data = S2CPackageHelper.create_register_response(False, "用户名和密码不能为空")
                            logger.info(f"向客户端 {client_id} 发送注册响应: {response_data}")
                            await websocket.send(json.dumps(response_data))
                        else:
                            # 调用数据库管理器进行注册
                            success, result = db_manager.register_user(username, password)
                            if success:
                                logger.info(f"用户注册成功: {username}, 用户ID: {result}")
                                # 使用S2CPackageHelper创建注册响应消息
                                response_data = S2CPackageHelper.create_register_response(True, "注册成功")
                                logger.info(f"向客户端 {client_id} 发送注册响应: {response_data}")
                                await websocket.send(json.dumps(response_data))
                            else:
                                logger.warning(f"用户注册失败: {username}, 原因: {result}")
                                # 使用S2CPackageHelper创建注册响应消息
                                response_data = S2CPackageHelper.create_register_response(False, result)
                                logger.info(f"向客户端 {client_id} 发送注册响应: {response_data}")
                                await websocket.send(json.dumps(response_data))
                        continue
                    
                    # 处理登录请求（验证用户身份）
                    elif data.get('type') == 'login':
                        username = data.get('username')
                        password = data.get('password')
                        
                        if not username or not password:
                            # 使用S2CPackageHelper创建登录响应消息
                            response_data = S2CPackageHelper.create_login_response_message(False, "用户名和密码不能为空")
                            logger.info(f"向客户端 {client_id} 发送登录响应: {response_data}")
                            await websocket.send(json.dumps(response_data))
                        else:
                            # 使用密码验证用户身份
                            success, user_data = db_manager.verify_user(username, password)
                            if success:
                                # 检查用户名是否已在聊天室中
                                if username in online_users:
                                    # 使用S2CPackageHelper创建登录响应消息
                                    response_data = S2CPackageHelper.create_login_response_message(False, "该用户名已在聊天室中登录")
                                    logger.info(f"向客户端 {client_id} 发送登录响应: {response_data}")
                                    await websocket.send(json.dumps(response_data))
                                else:
                                    # 更新用户信息
                                    user_info['name'] = username
                                    user_info['authenticated'] = True
                                    user_info['user_id'] = user_data['id']
                                    
                                    logger.info(f"用户登录成功: {username} (数据库ID: {user_data['id']})")
                                    # 使用S2CPackageHelper创建登录响应消息
                                    response_data = S2CPackageHelper.create_login_response_message(True, "登录成功", user_data)
                                    logger.info(f"向客户端 {client_id} 发送登录响应: {response_data}")
                                    await websocket.send(json.dumps(response_data))
                                    
                                    # 更新在线用户列表
                                    online_users.add(username)
                                    
                                    # 使用S2CPackageHelper创建系统消息
                                    join_message = S2CPackageHelper.create_system_message_with_users(f"{username} 加入了聊天室", user=username, online_users=list(online_users))
                                    # 广播用户加入消息
                                    await broadcast_message(join_message, exclude_client=client_id)
                                    
                                    # 发送更新后的在线用户列表
                                    await send_active_users()
                            else:
                                logger.warning(f"用户登录失败: {username}，用户名或密码错误")
                                # 使用S2CPackageHelper创建登录响应消息
                                response_data = S2CPackageHelper.create_login_response_message(False, "用户名或密码错误")
                                logger.info(f"向客户端 {client_id} 发送登录响应: {response_data}")
                                await websocket.send(json.dumps(response_data))
                        continue
                    
                    # 检查用户是否已认证（注册和登录请求除外）
                    if not user_info['authenticated']:
                        response_data = {
                            "type": "error",
                            "message": "请先登录后再发送消息"
                        }
                        logger.info(f"向未认证客户端 {client_id} 发送错误: {response_data}")
                        await websocket.send(json.dumps(response_data))
                        continue
                    
                    # 处理不同类型的消息
                    if isinstance(data, dict):
                        # 处理客户端初始连接消息
                        if 'username' in data and user_info['authenticated']:
                            # 已认证用户的连接，用户名已经在登录时设置
                            # 不需要再进行昵称设置，直接确认连接成功
                            response_data = {
                                "type": "connection_success",
                                "message": "连接成功"
                            }
                            logger.info(f"向客户端 {client_id} 发送: {response_data}")
                            await websocket.send(json.dumps(response_data))
                        # 移除未认证用户的昵称设置和自动认证功能
                        # 现在用户必须通过正规登录流程才能获得认证状态
                        
                        # 处理图片预加载完成信号
                        elif data['type'] == 'image_preload_complete':
                            logger.info(f"收到图片预加载完成信号: image_id={data.get('image_id')}, status={data.get('status')}")
                            
                            # 这里可以存储预加载状态或触发后续操作
                            # 由于我们已经在handle_at_command中添加了延迟，这里主要是记录状态
                            if data.get('status') == 'success':
                                logger.info(f"图片预加载成功，image_id={data.get('image_id')}")
                                # 如果需要，可以在这里执行额外的操作
                            else:
                                logger.warning(f"图片预加载失败，image_id={data.get('image_id')}, error={data.get('error')}")
                            
                            continue
                        
                        # 处理常规聊天消息 - 仅允许已认证用户
                        elif data['type'] == 'message' and 'message' in data:
                            if not user_info['authenticated']:
                                # 未认证用户不允许发送消息
                                response_data = {
                                    "type": "error",
                                    "message": "请先登录后再发送消息"
                                }
                                logger.info(f"向未认证客户端 {client_id} 发送错误: {response_data}")
                                await websocket.send(json.dumps(response_data))
                                continue
                            
                            content = data['message'].strip()
                             
                            # 处理@命令
                            if content.startswith('@'):
                                # 先以普通消息方式广播@指令消息
                                logger.info(f"发送@指令消息 from {user_info['name']}: {content}")
                                await broadcast_message({
                                    "type": "message",
                                    "message": content,
                                    "user": user_info['name']
                                }, room=user_info['room'])
                                # 然后再进行指令处理
                                await handle_at_command(content, user_info)
                            else:
                                # 普通消息广播
                                logger.info(f"发送消息 from {user_info['name']}: {content}")
                                await broadcast_message({
                                    "type": "message",
                                    "message": content,
                                    "user": user_info['name']
                                }, room=user_info['room'])
                        
                        # 处理加入房间消息
                        elif data['type'] == 'join_room' and 'room' in data:
                            new_room = data['room'].strip()
                            old_room = user_info['room']
                            
                            # 检查是否已经在该房间
                            if old_room != new_room:
                                # 更新用户房间
                                user_info['room'] = new_room
                                logger.info(f"用户 {user_info['name']} 从 {old_room} 加入 {new_room}")
                                
                                # 发送确认消息给用户
                                room_message = S2CPackageHelper.create_room_joined_message(new_room)
                                await websocket.send(json.dumps(room_message))
                                
                                # 广播用户房间变更
                                system_message = S2CPackageHelper.create_system_message(f"{user_info['name']} 加入了房间 {new_room}", user=user_info['name'])
                                await broadcast_message(system_message, new_room)
                        
                        # 处理心跳消息
                        elif data['type'] == 'ping':
                            # 使用S2CPackageHelper创建心跳响应消息
                            pong_message = S2CPackageHelper.create_heartbeat_response()
                            await websocket.send(json.dumps(pong_message))
                        
                        # 其他未识别的消息类型
                        else:
                            logger.warning(f"未知消息类型: {data['type']} 来自 {user_info['name']}")
                            error_message = S2CPackageHelper.create_error_message("未知消息类型")
                            await websocket.send(json.dumps(error_message))
                    else:
                        # 非结构化消息处理
                        content = message.strip()
                        logger.info(f"收到非结构化消息 from {user_info['name']}: {content}")
                        
                        # 处理@命令
                        if content.startswith('@'):
                            # 先以普通消息方式广播@指令消息
                            logger.info(f"发送@指令消息 from {user_info['name']}: {content}")
                            await broadcast_message({
                                "type": "message",
                                "message": content,
                                "user": user_info['name'],
                                "sender": user_info['name']  # 添加sender字段以兼容客户端
                            }, room=user_info['room'])
                            # 然后再进行指令处理
                            logger.info(f"检测到@命令，调用handle_at_command处理: {content}")
                            await handle_at_command(content, user_info)
                            # 处理完@命令后返回，避免后续处理
                            return
                        else:
                            # 普通消息广播
                            await broadcast_message({
                                "type": "message",
                                "message": content,
                                "user": user_info['name'],
                                "sender": user_info['name']  # 添加sender字段以兼容客户端
                            }, room=user_info['room'])
                except json.JSONDecodeError:
                    # 处理非JSON格式消息
                    content = message.strip()
                    logger.info(f"收到非JSON消息 from {user_info['name']}: {content}")
                    
                    # 处理@命令
                    if content.startswith('@'):
                        # 先以普通消息方式广播@指令消息
                        logger.info(f"发送@指令消息 from {user_info['name']}: {content}")
                        await broadcast_message({
                            "type": "message",
                            "message": content,
                            "user": user_info['name']
                        }, room=user_info['room'])
                        # 然后再进行指令处理
                        logger.info(f"在JSON解析错误中检测到@命令，调用handle_at_command处理: {content}")
                        await handle_at_command(content, user_info)
                        # 处理完@命令后返回，避免后续处理
                        return
                    else:
                        # 普通消息广播
                        await broadcast_message({
                            "type": "message",
                            "message": content,
                            "user": user_info['name']
                        }, room=user_info['room'])
            except asyncio.TimeoutError:
                # 超时处理，可能是网络问题或客户端无响应
                logger.warning(f"客户端 {client_id} 接收超时，可能网络不稳定")
                system_message = S2CPackageHelper.create_system_message("连接超时，请检查网络连接")
                await websocket.send(json.dumps(system_message))
            except Exception as e:
                # 其他异常
                logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
                error_message = S2CPackageHelper.create_error_message(f"处理消息时出错: {str(e)}")
                await websocket.send(json.dumps(error_message))
    
    except websockets.ConnectionClosedError as e:
        logger.info(f"客户端 {user_info['name']} 连接关闭: {str(e)}")
    except Exception as e:
        logger.error(f"客户端 {user_info['name']} 发生错误: {str(e)}", exc_info=True)
    finally:
        # 清理资源
        try:
            # 取消心跳任务
            heartbeat_task.cancel()
        except UnboundLocalError:
            pass
        
        # 移除客户端
        async with clients_lock:
            if client_id in active_clients:
                del active_clients[client_id]
                logger.info(f"从active_clients中移除客户端: {client_id} ({user_info['name']})")
        
        # 关键修复：当用户断开连接时，从online_users集合中移除用户名
        if user_info.get('authenticated', False) and user_info['name'] in online_users:
            online_users.remove(user_info['name'])
            logger.info(f"从online_users中移除用户: {user_info['name']}")
        
        # 使用S2CPackageHelper创建系统消息并广播用户离开消息
        leave_message = S2CPackageHelper.create_system_message_with_users(
            f"{user_info['name']} 离开了聊天室", 
            user=user_info['name']
        )
        await broadcast_message(leave_message, exclude_client=client_id)
        
        # 发送更新后的在线用户列表（关键修复！确保浏览器关闭时正确更新用户列表）
        logger.info(f"发送更新后的在线用户列表，用户 {user_info['name']} 已离开")
        await send_active_users()
        
        logger.info(f"客户端 {user_info['name']} (ID: {client_id}) 已断开连接")

# 启动WebSocket服务器
async def main():
    # 加载chatbot配置
    load_chatbot_config()
    
    # 配置WebSocket服务器
    async with websockets.serve(
        handle_client,
        "0.0.0.0", 
        8766,
        ping_interval=15.0,
        ping_timeout=20.0,
        close_timeout=10.0
    ):
        logger.info(f"WebSocket服务器已启动，监听端口8766，大模型对话功能状态: {'已启用' if chatbot_config.get('enabled') else '已禁用'}")
        await asyncio.Future()  # 保持服务器运行

if __name__ == "__main__":
    logger.info("正在启动聊天服务器...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止服务器...")
    finally:
        logger.info("服务器已停止")


