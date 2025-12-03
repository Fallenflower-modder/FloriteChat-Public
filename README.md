# FloriteChat

一个功能丰富的局域网多人实时聊天应用，采用B/S架构，基于WebSocket技术实现即时通讯，集成大模型对话功能。

## 功能特点

- **实时聊天**：支持文字和emoji表情的实时发送与接收
- **多服务器支持**：可配置多个服务器地址，灵活连接
- **@命令功能**：内置丰富的指令可供使用
- **SSE流式响应**：AI回复实时流式显示，提升用户体验
- **优化的Emoji选择器**：每行固定7个emoji，布局整齐规范
- **用户在线列表**：显示当前聊天室在线用户
- **用户唯一性检查**：确保昵称不重复
- **响应式设计**：适配各种屏幕尺寸

## 技术栈

- **服务端**：Python 3 + WebSocket + SSE (Server-Sent Events)
- **客户端**：HTML5 + CSS3 + JavaScript
- **数据传输**：WebSocket协议
- **AI集成**：支持大模型API调用，实现智能对话功能

## 项目结构

```
FloriteChat/
├── src/
│   ├── server/           # 服务端代码
│   │   ├── server.py         # WebSocket服务器实现
│   │   ├── config.json       # 服务器配置文件
│   │   ├── chatbot-config.json # AI聊天机器人配置
│   │   ├── chatbot-tips.txt  # AI聊天提示词配置
│   │   └── logs/             # 服务端日志目录
│   └── client/           # 客户端代码
│       ├── login.html    # 登录页面
│       ├── chat.html     # 聊天室页面
│       ├── css/          # 样式文件
│       │   ├── style.css # 基础样式
│       │   ├── login.css # 登录页样式
│       │   └── chat.css  # 聊天室样式
│       ├── js/           # JavaScript文件
│       │   ├── login.js  # 登录页面逻辑
│       │   └── chat.js   # 聊天室逻辑
│       └── images/       # 图片资源
├── venv/                 # Python虚拟环境
├── logs/                 # 应用日志目录
├── start_server.py       # 服务器启动脚本
├── start_full_server.py  # 完整服务器启动脚本
├── test_server.py        # 测试服务器脚本
└── README.md             # 项目说明文件
```

## 安装与运行

### 1.检查你的设备是否安装了以下内容：
- Python 3.8+
- 必要的Python库：
  - websockets
  - asyncio
  - json
  - sqlite3
  - logging
  - os
  - urllib3
  - requests
  - beautifulsoup4

### 2. 如果没有，请使用PIP安装程序进行安装：
**示例**
```bash
pip install websockets
pip install beautifulsoup4
pip install passlib
pip install requests
```

### 3. 运行服务器

**方法1：使用”启动服务器.bat“启动**（推荐）

**方法2：使用完整启动脚本**
```bash
python start_full_server.py
```

**注意**：WebSocket服务器默认运行在8766端口，而非8765端口

### 4. 你可以使用内网穿透技术将你的websocket端口和HTTP服务端口暴露在公网以使用户连接并使用，例如使用ngrok。
**用户连接使用的URL**
```
http://<你的公网IP>:8000/src/client/login.html
```
**⚠ 注意：你需要先确定你的公网IP地址并在src/server/Config.json中配置，才能正确连接到服务器。 ⚠**
**示例**
```json
{
    "servers": [
        {
            "name": "本地服务器(localhost:8766)",
            "url": "ws://localhost:8766"
        },
        {
            "name": "服务器1(192.168.1.100:8766)",
            "url": "ws://192.168.1.100:8766"
        },
        {
            "name": "服务器2(192.168.1.101:8766)",
            "url": "ws://192.168.1.101:8766"
        }
    ]
}
```

## 使用指南

### 注册
1. 点击页面下方的”注册“链接
2. 选择服务器，然后输入昵称、密码
3. 点击注册，如果成功页面会进行提示
4. 点击提示框的”继续“按钮返回登录界面

### 登录
1. 在登录页面输入你的昵称和密码
2. 从下拉列表中选择要连接的服务器地址
3. 点击「登录」按钮进入聊天室

### 发送消息
1. 在输入框中输入消息
2. 点击发送按钮或按Enter键发送

### 使用@命令
- **获取运势**：输入 `@运势` 并发送
- **播放电影**：输入 `@电影 电影URL` 并发送，例如：`@电影 https://example.com/movie.mp4`
- **AI对话**：输入 `@苹果派 你的问题` 并发送，例如：`@苹果派 今天天气怎么样？`
  - AI回复支持流式显示，打字效果更加自然
  - 支持多轮对话，上下文理解
  - 需要启用“大模型对话”功能，才能正常使用
- **获取天气**：输入 `@天气 城市` 并发送，例如：`@天气 北京市海淀区`
  - 支持查询当前天气和未来几天的天气
  - 页面背景跟随天气变化。
  - 需要在LittleAPIConfig.json中配置天气API密钥，密钥获得方法参考后文
- **播放音乐**：输入 `@音乐 音乐URL` 并发送，例如：`@音乐 https://music.163.com/#song?id=xxx`
  - 需要在OickAPIConfig.txt中配置音乐API密钥，密钥获得方法参考后文
- **每日早报**：输入 `@新闻` 并发送，每天60秒，看懂世界
- **每日热搜**：输入 `@热搜` 并发送，实时获取当下百度热搜

### 使用emoji表情
1. 点击输入框旁的表情图标打开表情选择器
2. 表情选择器采用网格布局，每行固定显示7个emoji
3. 点击选择想要的表情直接插入到输入框

### 退出聊天室
点击右上角的退出按钮，将返回到登录页面

## 配置多服务器

编辑 `src/server/config.json` 文件，添加或修改服务器地址：

```json
{
  "servers": [
    {
      "name": "本地服务器",
      "url": "ws://localhost:8766"
    },
    {
      "name": "局域网服务器1",
      "url": "ws://192.168.1.100:8766"
    },
    {
      "name": "局域网服务器2",
      "url": "ws://192.168.1.101:8766"
    }
  ]
}
```

## 配置API密钥

### 天气API密钥
1. 访问 https://xxapi.cn/注册账号
2. 获取API密钥
3. 在 `src/server/LittleAPIConfig.json` 文件中配置密钥：
```json
{"key":"Input your API key here"}
```

### 音乐API密钥
1. 访问 https://api.oick.cn/注册账号
2. 购买“网易云解析”（免费，年付即可）
3. 获取API密钥
4. 在 `src/server/OickAPIConfig.txt` 文件中配置密钥：
```
你的API密钥
```

## 大模型对话功能

### 启用大模型对话
1.访问你所需要使用的AI大模型的开发者平台，获取你的API密钥
2.在src/server/chatbot-config.json文件中配置密钥：
```json
{
    "api_key": "Input your API key here",
    "model_name": "Input your model name here",
    "enabled": true,
    "api_base": "Input your API URL here"
}
```
#### 注意事项
- 请确保配置文件中的密钥、模型名称和URL是正确的，否则可能导致API调用失败
- 大模型对话功能默认是禁用的，需要将enabled设置为true才能启用

### 使用大模型提示词
**如果需要使用大模型提示词功能，请将提示词写在src/server/chatbot-tips.txt文件中，如果不需要请将其留空**
**示例：**
```
角色：
姓名：
性别：
性格：
功能：
限定：
```

## 需要重置账户数据库？
**直接运行ResetDataBase.py即可重置数据库！**
```bash
python ResetDataBase.py
```

## 常见问题

### 无法连接服务器
- 检查服务器是否正在运行
- 确认网络连接正常
- 验证服务器地址是否正确

### 昵称已被使用
- 请选择一个不同的昵称再次尝试登录

### 电影无法播放
- 确保提供的URL是有效的视频文件链接
- 检查浏览器是否支持该视频格式

### 音乐无法播放
- 确保提供的音乐URL属于网易云音乐平台且不是付费歌曲

### 聊天界面弹出大量断开连接提示
- 这是由于浏览器对于未聚焦的网页进行静默处理导致的正常现象

## 如何下载？
- 直接下载源代码压缩包即可！

## 许可证

本项目仅供学习和参考使用。

## 贡献

欢迎提交问题报告和改进建议！
