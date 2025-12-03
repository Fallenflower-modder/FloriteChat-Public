// 聊天页面JavaScript

// 全局变量
let socket;
let username = '';
let isAuthenticated = false;
let serverUrl;
let connectionState = 'disconnected'; // 连接状态变量


const elements = {
    userAvatar: document.getElementById('user-avatar'),
    userNickname: document.getElementById('user-nickname'),
    connectionStatus: document.getElementById('connection-status'),
    logoutBtn: document.getElementById('logout-btn'),
    onlineCount: document.getElementById('online-count'),
    userList: document.getElementById('user-list'),
    chatMessages: document.getElementById('chat-messages'),
    messageInput: document.getElementById('message-input'),
    sendBtn: document.getElementById('send-btn'),
    emojiBtn: document.getElementById('emoji-btn'),
    emojiPicker: document.getElementById('emoji-picker'),
    movieModal: document.getElementById('movie-modal'),
    closeModal: document.querySelector('.close-modal'),
    moviePlayer: document.getElementById('movie-player'),
    movieTitle: document.getElementById('movie-title'),
    commandList: document.getElementById('command-list')
};

// 存储指令列表
let commandData = {};

// 常用emoji表情
const emojis = [
    '😊', '😂', '😍', '🥰', '😘', '😗', '🤗', '🤩',
    '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂',
    '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙',
    '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐',
    '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔'
];

// 初始化应用
function init() {
    // 获取用户信息
    username = localStorage.getItem('username');
    serverUrl = localStorage.getItem('serverUrl');
    isAuthenticated = localStorage.getItem('authenticated') === 'true';
    
    if (!username || !serverUrl || !isAuthenticated) {
        // 如果没有用户信息或未认证，跳转到登录页面
        window.location.href = 'login.html';
        return;
    }
    
    // 设置用户信息显示
    elements.userNickname.textContent = username;
    elements.userAvatar.textContent = username.charAt(0).toUpperCase();
    
    // 初始化emoji选择器
    initEmojiPicker();
    
    // 加载指令列表
    loadCommandList();
    
    // 设置事件监听
    setupEventListeners();
    
    // 连接WebSocket服务器
    connectToServer();
}

// 初始化emoji选择器
function initEmojiPicker() {
    elements.emojiPicker.innerHTML = '';
    emojis.forEach(emoji => {
        const emojiItem = document.createElement('div');
        emojiItem.className = 'emoji-item';
        emojiItem.textContent = emoji;
        emojiItem.addEventListener('click', () => {
            elements.messageInput.value += emoji;
            elements.messageInput.focus();
            elements.emojiPicker.classList.remove('show');
        });
        elements.emojiPicker.appendChild(emojiItem);
    });
}

// 加载指令列表
function loadCommandList() {
    // 从本地JSON文件加载指令列表，使用相对于chat.html的路径
    fetch('js/user_command.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应错误');
            }
            return response.json();
        })
        .then(data => {
            commandData = data;
            renderCommandList();
            console.log('指令列表加载成功:', data);
        })
        .catch(error => {
            console.error('加载指令列表失败:', error);
            // 添加错误提示
            showError('无法加载指令列表，请刷新页面重试');
        });
}

// 渲染指令列表
function renderCommandList() {
    const commandList = elements.commandList;
    commandList.innerHTML = '';
    
    Object.entries(commandData).forEach(([command, description]) => {
        const commandItem = document.createElement('div');
        commandItem.className = 'command-item';
        commandItem.innerHTML = `
            <span class="command-name">${escapeHtml(command)}</span>
            <span class="command-desc">${escapeHtml(description)}</span>
        `;
        
        // 点击指令时将指令插入输入框
        commandItem.addEventListener('click', function() {
            // 检查输入框中是否已经有@符号，如果有则替换它
            const inputElement = elements.messageInput;
            const currentValue = inputElement.value;
            const lastAtIndex = currentValue.lastIndexOf('@');
            
            if (lastAtIndex !== -1) {
                // 检查@之后是否有其他字符
                const afterAt = currentValue.substring(lastAtIndex).split(/\s/)[0];
                if (afterAt === '@' || afterAt.startsWith('@') && !afterAt.includes(' ')) {
                    inputElement.value = currentValue.substring(0, lastAtIndex) + command;
                } else {
                    inputElement.value = currentValue + (currentValue ? ' ' : '') + command;
                }
            } else {
                inputElement.value = command;
            }
            
            // 关闭指令列表
            hideCommandList();
            // 聚焦输入框
            inputElement.focus();
        });
        
        commandList.appendChild(commandItem);
    });
}

// 显示指令列表
function showCommandList() {
    elements.commandList.classList.add('show');
}

// 隐藏指令列表
function hideCommandList() {
    elements.commandList.classList.remove('show');
}

// 检查是否应该显示指令列表
function shouldShowCommandList(inputValue) {
    // 如果输入框为空或最后一个字符是@，则显示指令列表
    if (inputValue === '@' || (inputValue.length > 0 && inputValue.endsWith('@'))) {
        return true;
    }
    
    // 检查光标位置后面是否有@符号且其后没有空格
    const cursorPos = elements.messageInput.selectionStart;
    const textBeforeCursor = inputValue.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    
    if (lastAtIndex !== -1) {
        const textAfterAt = textBeforeCursor.substring(lastAtIndex);
        // 如果@后面没有字符或只有非空格字符，则显示指令列表
        return !textAfterAt.includes(' ');
    }
    
    return false;
}

// 在光标位置插入文本
function insertTextAtCursor(inputElement, text) {
    const startPos = inputElement.selectionStart;
    const endPos = inputElement.selectionEnd;
    const scrollTop = inputElement.scrollTop;
    
    inputElement.value = inputElement.value.substring(0, startPos) + text + inputElement.value.substring(endPos);
    
    // 设置新的光标位置
    inputElement.selectionStart = inputElement.selectionEnd = startPos + text.length;
    inputElement.scrollTop = scrollTop;
    
    // 聚焦输入框
    inputElement.focus();
}

// 设置事件监听
function setupEventListeners() {
    // 发送消息按钮
    elements.sendBtn.addEventListener('click', sendMessage);
    
    // 输入框回车发送
    elements.messageInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Emoji按钮
    elements.emojiBtn.addEventListener('click', () => {
        elements.emojiPicker.classList.toggle('show');
        // 如果显示emoji选择器，则隐藏指令列表
        if (elements.emojiPicker.classList.contains('show')) {
            hideCommandList();
        }
    });
    
    // 输入框事件监听，处理@符号显示指令列表
    elements.messageInput.addEventListener('input', function(e) {
        const inputValue = this.value;
        if (shouldShowCommandList(inputValue)) {
            showCommandList();
        } else {
            hideCommandList();
        }
    });
    
    // 输入框光标位置变化时检查是否应该显示指令列表
    elements.messageInput.addEventListener('click', function() {
        const inputValue = this.value;
        if (shouldShowCommandList(inputValue)) {
            showCommandList();
        } else {
            hideCommandList();
        }
    });
    
    // 点击其他区域关闭emoji选择器和指令列表
    document.addEventListener('click', (e) => {
        // 关闭emoji选择器
        if (!elements.emojiBtn.contains(e.target) && !elements.emojiPicker.contains(e.target)) {
            elements.emojiPicker.classList.remove('show');
        }
        
        // 关闭指令列表
        if (!elements.messageInput.contains(e.target) && !elements.commandList.contains(e.target)) {
            hideCommandList();
        }
    });
    
    // 退出按钮
    elements.logoutBtn.addEventListener('click', logout);
    
    // 关闭电影模态框
    elements.closeModal.addEventListener('click', () => {
        elements.movieModal.classList.remove('show');
        // 更彻底地清除iframe内容以停止所有播放
        const iframe = elements.moviePlayer;
        // 保存原始属性
        const width = iframe.width;
        const height = iframe.height;
        
        // 完全重置iframe（这会停止所有正在播放的内容）
        iframe.src = 'about:blank';
        
        // 可选：延迟一点时间后设置回空字符串，确保彻底释放
        setTimeout(() => {
            iframe.src = '';
            // 恢复尺寸设置
            iframe.width = width;
            iframe.height = height;
        }, 100);
    });
    
    // 点击模态框外部关闭
    elements.movieModal.addEventListener('click', (e) => {
        if (e.target === elements.movieModal) {
            elements.closeModal.click();
        }
    });
}

// 连接相关变量
let reconnectAttempts = 0;
let maxReconnectAttempts = 10;
let heartbeatInterval;
let reconnectTimeout;
let lastHeartbeatTime = Date.now();
// connectionState is already declared globally at the top of the file

// 连接到WebSocket服务器
function connectToServer() {
    // 更新连接状态
    connectionState = 'connecting';
    elements.connectionStatus.textContent = '连接中...';
    elements.connectionStatus.className = 'status connecting';
    
    try {
        // 如果已经有socket连接，先关闭
        if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
            socket.close();
        }
        
        console.log(`尝试连接到服务器: ${serverUrl}`);
        socket = new WebSocket(serverUrl);
        
        // 设置连接超时
        const connectionTimeout = setTimeout(() => {
            if (socket && socket.readyState === WebSocket.CONNECTING) {
                console.error('连接超时');
                socket.close();
                handleReconnect();
            }
        }, 10000); // 10秒超时
        
        socket.onopen = () => {
            clearTimeout(connectionTimeout);
            console.log('已连接到服务器');
            connectionState = 'connected';
            elements.connectionStatus.textContent = '在线';
            elements.connectionStatus.className = 'status online';
            reconnectAttempts = 0; // 重置重连计数
            lastHeartbeatTime = Date.now();
            
            // 直接使用本地存储的认证状态
            isAuthenticated = localStorage.getItem('authenticated') === 'true';
            
            // 如果用户已认证，发送登录信息给服务器
            if (isAuthenticated && username) {
                // 添加调试日志
                console.log('localStorage内容检查:', {
                    username: localStorage.getItem('username'),
                    isAuthenticated: localStorage.getItem('authenticated')
                });
                // 首先检查内存中的密码，然后检查sessionStorage中的密码
                const passwordForReconnect = window.sessionPassword || sessionStorage.getItem('sessionPassword');
                
                if (!passwordForReconnect) {
                    // 没有密码，需要用户重新登录
                    showSystemMessage('需要重新登录才能继续使用', 'error');
                    // 重置认证状态
                    localStorage.removeItem('authenticated');
                    isAuthenticated = false;
                    // 延迟跳转到登录页面，让用户看到消息
                    setTimeout(() => {
                        window.location.href = 'login.html';
                    }, 3000);
                } else {
                    // 创建认证消息对象（使用正确的认证格式）
                    const authMessage = {
                        type: 'login',
                        username: username,
                        password: passwordForReconnect // 使用内存中的密码进行验证
                    };
                    // 显示完整的认证消息内容
                    console.log('向服务器发送登录信息:', authMessage);
                    // 发送认证消息
                    socket.send(JSON.stringify(authMessage));
                }
            }
            
            // 启动心跳
            startHeartbeat();
        };
        
        socket.onmessage = (event) => {
            try {
                console.log('接收到原始消息:', event.data);
                const data = JSON.parse(event.data);
                console.log('解析后的消息数据:', data);
                
                // 更新心跳时间（任何消息都可以视为心跳响应）
                lastHeartbeatTime = Date.now();
                
                handleMessage(data);
            } catch (error) {
                console.error('解析消息失败:', error, '消息内容:', event.data);
                // 显示错误消息但不中断连接
                showSystemMessage(`消息解析错误: ${error.message}`, 'error');
            }
        };
        
        socket.onclose = (event) => {
            clearTimeout(connectionTimeout);
            clearInterval(heartbeatInterval);
            connectionState = 'disconnected';
            console.log(`与服务器断开连接: ${event.code} - ${event.reason}`);
            elements.connectionStatus.textContent = '离线';
            elements.connectionStatus.className = 'status offline';
            
            // 避免页面关闭时的不必要重连
            if (!event.wasClean) {
                // 根据断开原因显示不同消息
                let reconnectMessage = '与服务器的连接已断开，正在尝试重连...';
                if (event.code === 1006) { // 连接意外关闭
                    reconnectMessage = '连接意外中断，正在尝试重连...';
                } else if (event.code === 1001) { // 服务器关闭
                    reconnectMessage = '服务器已关闭，正在尝试重连...';
                }
                
                showSystemMessage(reconnectMessage);
                handleReconnect();
            }
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            // 显示更友好的错误信息
            const errorMessage = error.message ? error.message : '连接出现错误';
            showSystemMessage(`连接错误: ${errorMessage}`, 'error');
        };
    } catch (error) {
        console.error('连接服务器失败:', error);
        showSystemMessage('无法连接到服务器，正在尝试重连...');
        handleReconnect();
    }
}

// 处理重连逻辑
function handleReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) {
        showError('无法连接到服务器，请检查网络连接后刷新页面');
        // 添加手动重连按钮
        const reconnectBtn = document.createElement('button');
        reconnectBtn.textContent = '重试连接';
        reconnectBtn.className = 'reconnect-btn';
        reconnectBtn.onclick = () => {
            reconnectBtn.remove();
            reconnectAttempts = 0;
            handleReconnect();
        };
        elements.chatMessages.appendChild(reconnectBtn);
        scrollToBottom();
        return;
    }
    
    // 清除之前的重连定时器
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
    }
    
    // 检查网络状态
    if (!navigator.onLine) {
        console.log('检测到离线状态，等待网络恢复');
        // 监听网络状态变化
        const onNetworkChange = () => {
            if (navigator.onLine) {
                console.log('网络已恢复，开始重连');
                window.removeEventListener('online', onNetworkChange);
                connectToServer();
            }
        };
        window.addEventListener('online', onNetworkChange);
        
        // 设置一个后备的重连定时器
        reconnectTimeout = setTimeout(() => {
            window.removeEventListener('online', onNetworkChange);
            handleReconnect();
        }, 30000);
        return;
    }
    
    // 指数退避重连策略，增加一些随机性避免所有客户端同时重连
    const baseDelay = 5000 * Math.pow(1.5, reconnectAttempts);
    const jitter = Math.random() * 1000; // 添加最多1秒的随机延迟
    const delay = Math.min(baseDelay + jitter, 30000); // 最大30秒
    reconnectAttempts++;
    
    const delayInSeconds = Math.round(delay / 1000);
    console.log(`将在 ${delayInSeconds}秒 后进行第 ${reconnectAttempts} 次重连`);
    
    // 显示重连倒计时
    let remainingSeconds = delayInSeconds;
    elements.connectionStatus.textContent = `将在${remainingSeconds}秒后重连...`;
    
    const countdownInterval = setInterval(() => {
        remainingSeconds--;
        if (remainingSeconds <= 0) {
            clearInterval(countdownInterval);
        } else {
            elements.connectionStatus.textContent = `将在${remainingSeconds}秒后重连...`;
        }
    }, 1000);
    
    reconnectTimeout = setTimeout(() => {
        clearInterval(countdownInterval);
        connectToServer();
    }, delay);
}

// 启动心跳机制
function startHeartbeat() {
    // 清除之前的心跳定时器
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    
    // 每10秒发送一次心跳
    heartbeatInterval = setInterval(() => {
        // 检查是否长时间没有收到心跳响应
        const now = Date.now();
        if (now - lastHeartbeatTime > 30000) { // 30秒没有心跳响应
            console.error('长时间未收到心跳响应，重新连接');
            clearInterval(heartbeatInterval);
            if (socket) {
                socket.close();
            }
            handleReconnect();
            return;
        }
        
        if (socket && socket.readyState === WebSocket.OPEN) {
            try {
                // 发送一个ping消息
                socket.send(JSON.stringify({ type: 'ping' }));
            } catch (error) {
                console.error('发送心跳失败:', error);
                // 发送心跳失败，可能连接已问题，触发重连
                clearInterval(heartbeatInterval);
                handleReconnect();
            }
        }
    }, 10000);
}

// 存储流式响应消息的容器
let streamingMessages = {};
// 存储当前活跃的流式对话气泡
let activeStreamingBubbles = {};

// 处理接收到的消息
function handleMessage(data) {
    // 忽略undefined或null数据
    if (!data) return;
    
    console.log('进入handleMessage函数，处理消息类型:', data.type);
    
    // 特殊处理流式消息片段
    if (data.type === 'message' && data.stream_id && data.stream_type) {
        handleStreamingMessage(data);
        return;
    }
    
    switch (data.type) {
        case 'image_preload':
            // 处理图片预加载消息，不显示在聊天界面
            console.log('处理图片预加载消息:', data.image_id, data.image_path);
            // 如果有image_path，尝试预加载图片
            if (data.image_path) {
                const img = new Image();
                img.src = data.image_path;
                
                // 图片加载成功回调
                img.onload = () => {
                    console.log('图片预加载成功:', data.image_id, data.image_path);
                    // 发送加载完成信号给服务器
                    const loadCompleteMessage = {
                        type: 'image_preload_complete',
                        image_id: data.image_id,
                        status: 'success',
                        time: new Date().toLocaleTimeString()
                    };
                    console.log('发送图片加载完成信号:', loadCompleteMessage);
                    socket.send(JSON.stringify(loadCompleteMessage));
                };
                
                // 图片加载失败回调
                img.onerror = () => {
                    console.error('图片预加载失败:', data.image_path);
                    // 发送加载失败信号给服务器
                    const loadCompleteMessage = {
                        type: 'image_preload_complete',
                        image_id: data.image_id,
                        status: 'error',
                        error: 'Failed to load image',
                        time: new Date().toLocaleTimeString()
                    };
                    console.log('发送图片加载失败信号:', loadCompleteMessage);
                    socket.send(JSON.stringify(loadCompleteMessage));
                };
            }
            break;
        case 'sse_stream':
            // 处理带有event_type的SSE流式消息
            if (data.event_type) {
                handleSseStreamMessage(data);
            } else {
                // 兼容旧格式
                handleStreamMessage(data);
            }
            break;
        case 'system':
            showSystemMessage(data.message);
            // 确保online_users存在且为数组
            if (Array.isArray(data.online_users)) {
                updateUserList(data.online_users);
                console.log('用户列表已更新:', data.online_users);
            }
            break;
        case 'online_users_update':
            // 专门处理用户列表更新消息
            if (Array.isArray(data.online_users)) {
                updateUserList(data.online_users);
                console.log('用户列表已更新(专用类型):', data.online_users);
            }
            break;
        case 'message':
            // 确保必要字段存在，支持user或sender字段作为消息发送者
            const sender = data.sender || data.user;
            console.log('处理普通消息，发送者:', sender, '消息内容:', data.message || data.content);
            // 检查是否包含图片信息
            const hasImage = data.has_image || data.image_path || data.image_content;
            
            if (hasImage) {
                // 对于包含图片的消息，使用showNewsCard函数处理
                console.log('消息包含图片，调用showNewsCard处理');
                showNewsCard(data);
            } else {
                // 支持content字段作为消息内容（兼容新闻消息）
                const messageContent = data.message || data.content;
                if (sender && messageContent) {
                    // 即使没有time字段，也应该显示消息
                    showChatMessage(sender, messageContent, data.time || new Date().toLocaleTimeString());
                } else {
                    console.warn('接收到的消息缺少必要字段:', data);
                }
            }
            break;
        case 'command':
            showCommandMessage(data.message, data.time);
            break;
        case 'movie':
            if (data.url) {
                showMovieCard(data.sender || '系统', data.url);
            }
            break;
        case 'hot_search':
            // 处理热搜消息
            showHotSearchMessage(data.message, data.user || '热搜榜', data.avatar || '🔥', data.time);
            break;
        case 'error':
            showError(data.message || '未知错误');
            // 只有严重错误才退出登录
            if (data.message && (data.message.includes('昵称') || data.message.includes('权限'))) {
                logout();
            }
            break;
        case 'pong':
            // 服务器对心跳的响应
            console.log('收到服务器pong响应');
            connectionState = 'connected';
            break;
        case 'ping':
            // 响应服务器的ping
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'pong' }));
            }
            break;
        case 'weather_card':
            // 处理天气卡片消息
            showWeatherCard(data);
            break;
        case 'music':
            // 处理音乐分享消息
            showMusicCard(data);
            break;
        case 'login_response':
            // 处理登录响应消息
            if (data.success) {
                console.log('登录成功:', data.message);
                isAuthenticated = true;
                // 可以在这里更新UI状态或执行其他登录成功后的操作
            } else {
                console.log('登录失败:', data.message);
                showError(data.message || '登录失败');
            }
            break;
        case 'private_message':
        case 'private_message_sent':
            // 处理私聊消息
            showChatMessage(data.from || data.to, data.message, data.time || new Date().toLocaleTimeString());
            break;
        case 'news':
            // 处理新闻消息
            showNewsCard(data);
            break;
        default:
            console.log('未知消息类型:', data.type, data);
    }
}

// 处理流式消息片段
function handleStreamingMessage(data) {
    const streamId = data.stream_id;
    const streamType = data.stream_type;
    const sender = data.sender || data.user;
    const message = data.message;
    
    if (!streamId || !sender) return;
    
    switch (streamType) {
        case 'chunk':
            if (activeStreamingBubbles[streamId]) {
                // 追加到现有气泡
                appendToStreamMessage(streamId, message);
            } else {
                // 创建新的流式消息气泡
                createStreamMessageBubble(streamId, sender, message);
            }
            break;
        case 'end':
            // 完成流式消息
            finalizeStreamMessage(streamId);
            break;
        default:
            console.log('未知的流式消息类型:', streamType);
    }
}

// 创建流式消息气泡
function createStreamMessageBubble(streamId, sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.id = `stream-bubble-${streamId}`;
    messageDiv.className = 'message other streaming';
    messageDiv.dataset.completed = 'false';
    
    const messageHtml = `
        <div class="message-header">
            <div class="message-avatar">${sender.charAt(0).toUpperCase()}</div>
            <span class="message-sender">${escapeHtml(sender)}</span>
        </div>
        <div class="message-content">
            <div class="streaming-content">${escapeHtml(message).replace(/@([^\s]+)/g, '<span class="mention">@$1</span>')}</div>
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        <span class="message-time">${new Date().toLocaleTimeString()}</span>
    `;
    
    messageDiv.innerHTML = messageHtml;
    elements.chatMessages.appendChild(messageDiv);
    activeStreamingBubbles[streamId] = messageDiv;
    scrollToBottom();
}

// 追加内容到流式消息气泡
function appendToStreamMessage(streamId, message) {
    const messageDiv = activeStreamingBubbles[streamId];
    if (!messageDiv) return;
    
    const contentElement = messageDiv.querySelector('.streaming-content');
    const typingIndicator = messageDiv.querySelector('.typing-indicator');
    
    if (contentElement) {
        // 处理@提及并追加内容
        const processedContent = escapeHtml(message).replace(/@([^\s]+)/g, '<span class="mention">@$1</span>');
        contentElement.innerHTML += processedContent;
    }
    
    if (typingIndicator) {
        typingIndicator.style.display = 'flex';
    }
    
    scrollToBottom();
}

// 完成流式消息气泡
function finalizeStreamMessage(streamId) {
    const messageDiv = activeStreamingBubbles[streamId];
    if (!messageDiv) return;
    
    // 标记为已完成
    messageDiv.dataset.completed = 'true';
    messageDiv.classList.remove('streaming');
    
    // 移除打字指示器
    const typingIndicator = messageDiv.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    
    // 清理引用
    delete activeStreamingBubbles[streamId];
    scrollToBottom();
}

// 处理SSE流式响应消息
// 处理新格式的SSE流式消息（带有event_type字段）
function handleSseStreamMessage(data) {
    // 使用当前时间戳作为响应ID，确保唯一性
    const responseId = 'sse_' + Date.now();
    
    switch (data.event_type) {
        case 'start':
            // 开始新的流式响应
            // 由于服务端没有传递原始消息，我们可以使用占位符
            createStreamingMessage(responseId, '苹果派', '');
            break;
        case 'chunk':
            // 更新流式响应内容
            // 查找最近创建的流式消息
            const lastStreamId = Object.keys(streamingMessages).pop();
            if (lastStreamId && streamingMessages[lastStreamId]) {
                updateStreamingMessage(lastStreamId, data.message || '');
            } else {
                // 如果没有找到现有的流式消息，创建一个新的
                createStreamingMessage(responseId, '苹果派', '');
                updateStreamingMessage(responseId, data.message || '');
            }
            break;
        case 'end':
            // 结束流式响应
            const activeStreamId = Object.keys(streamingMessages).pop();
            if (activeStreamId && streamingMessages[activeStreamId]) {
                finalizeStreamingMessage(activeStreamId);
            }
            break;
        default:
            console.log('未知的SSE事件类型:', data.event_type);
    }
}

function handleStreamMessage(data) {
    if (!data.response_id || !data.action) return;
    
    const responseId = data.response_id;
    
    switch (data.action) {
        case 'start':
            // 开始新的流式响应
            createStreamingMessage(responseId, data.sender || '苹果派', data.original_message);
            break;
        case 'chunk':
            // 更新流式响应内容
            updateStreamingMessage(responseId, data.content || '');
            break;
        case 'end':
            // 结束流式响应
            finalizeStreamingMessage(responseId);
            break;
        default:
            console.log('未知的流式响应动作:', data.action);
    }
}

// 创建流式消息容器
function createStreamingMessage(responseId, sender, originalMessage) {
    const messageDiv = document.createElement('div');
    messageDiv.id = `streaming-${responseId}`;
    messageDiv.className = 'message other streaming';
    messageDiv.dataset.completed = 'false';
    
    const messageHtml = `
        <div class="message-header">
            <div class="message-avatar">${sender.charAt(0).toUpperCase()}</div>
            <span class="message-sender">${escapeHtml(sender)}</span>
        </div>
        <div class="message-content">
            <div class="streaming-content">正在思考...</div>
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        <span class="message-time">${new Date().toLocaleTimeString()}</span>
    `;
    
    messageDiv.innerHTML = messageHtml;
    elements.chatMessages.appendChild(messageDiv);
    streamingMessages[responseId] = messageDiv;
    scrollToBottom();
}

// 更新流式消息内容
function updateStreamingMessage(responseId, content) {
    const messageDiv = streamingMessages[responseId];
    if (!messageDiv) return;
    
    const contentElement = messageDiv.querySelector('.streaming-content');
    const typingIndicator = messageDiv.querySelector('.typing-indicator');
    
    if (contentElement) {
        // 如果是第一次有内容，移除"正在思考..."文本
        if (contentElement.textContent === '正在思考...') {
            contentElement.textContent = '';
        }
        
        // 处理@提及
        const processedContent = content.replace(/@([^\s]+)/g, '<span class="mention">@$1</span>');
        contentElement.innerHTML += processedContent;
    }
    
    if (typingIndicator) {
        // 只要有内容更新就显示打字指示器
        typingIndicator.style.display = 'flex';
    }
    
    scrollToBottom();
}

// 完成流式消息
function finalizeStreamingMessage(responseId) {
    const messageDiv = streamingMessages[responseId];
    if (!messageDiv) return;
    
    // 标记为已完成
    messageDiv.dataset.completed = 'true';
    messageDiv.classList.remove('streaming');
    
    // 移除打字指示器
    const typingIndicator = messageDiv.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    
    // 清理引用
    delete streamingMessages[responseId];
    scrollToBottom();
}

// 显示热搜消息
function showHotSearchMessage(message, user, avatar, time) {
    const timestamp = time || new Date().toLocaleTimeString();
    
    // 创建热搜卡片容器
    const hotSearchCard = document.createElement('div');
    hotSearchCard.className = 'hot-search-card';
    
    // 创建消息头部，包含头像和用户名
    const header = document.createElement('div');
    header.className = 'hot-search-header';
    header.innerHTML = `
        <div class="hot-search-avatar">${avatar}</div>
        <span class="hot-search-user">${escapeHtml(user)}</span>
        <span class="message-time">${timestamp}</span>
    `;
    
    // 创建消息内容区域
    const content = document.createElement('div');
    content.className = 'hot-search-content';
    
    // 确保message是数组格式（从服务器接收的热搜数据）
    const hotSearches = Array.isArray(message) ? message : [message];
    
    // 处理每条热搜数据
    hotSearches.forEach((searchText, index) => {
        // 创建热搜项元素
        const searchItem = document.createElement('div');
        searchItem.className = 'hot-search-item';
        
        // 根据要求设置序号：第一条使用↑箭头，第二条开始从1依次编号
        let serialNumber;
        if (index === 0) {
            serialNumber = '↑';  // 第一条使用向上的箭头
        } else {
            serialNumber = (index).toString();  // 从第二条开始从1依次编号
        }
        
        // 创建序号和内容的结构
        const serialSpan = document.createElement('span');
        serialSpan.className = 'hot-search-serial';
        serialSpan.textContent = serialNumber;
        serialSpan.style.marginRight = '8px';
        serialSpan.style.fontWeight = 'bold';
        
        const contentSpan = document.createElement('span');
        contentSpan.className = 'hot-search-text';
        contentSpan.textContent = escapeHtml(searchText);
        
        // 组装热搜项
        searchItem.appendChild(serialSpan);
        searchItem.appendChild(contentSpan);
        
        // 添加点击事件，在新标签页打开百度搜索
        searchItem.addEventListener('click', function() {
            // 直接使用热搜文本作为关键词
            const keyword = searchText.trim();
            // 构建百度搜索URL
            const searchUrl = `https://www.baidu.com/s?wd=${encodeURIComponent(keyword)}`;
            // 在新标签页打开搜索结果
            window.open(searchUrl, '_blank');
        });
        
        // 添加鼠标悬停效果的样式
        searchItem.style.cursor = 'pointer';
        searchItem.style.transition = 'color 0.2s';
        searchItem.addEventListener('mouseenter', function() {
            this.style.color = '#1e88e5';
        });
        searchItem.addEventListener('mouseleave', function() {
            this.style.color = '';
        });
        
        content.appendChild(searchItem);
    });
    
    // 组装卡片
    hotSearchCard.appendChild(header);
    hotSearchCard.appendChild(content);
    
    // 添加到聊天区域
    elements.chatMessages.appendChild(hotSearchCard);
    scrollToBottom();
}

// 显示系统消息
function showSystemMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    // 根据类型添加不同的CSS类
    messageDiv.className = `system-message system-${type}`;
    messageDiv.innerHTML = `<p>${escapeHtml(message)}</p>`;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示聊天消息
function showChatMessage(sender, message, time) {
    const isSelf = sender === username;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isSelf ? 'self' : 'other'}`;
    
    let messageHtml = '';
    
    if (!isSelf) {
        messageHtml += `
            <div class="message-header">
                <div class="message-avatar">${sender.charAt(0).toUpperCase()}</div>
                <span class="message-sender">${escapeHtml(sender)}</span>
            </div>
        `;
    }
    
    // 处理@提及
    const processedMessage = message.replace(/@([^\s]+)/g, '<span class="mention">@$1</span>');
    
    // 创建消息容器
    messageHtml += `
        <div class="message-content-wrapper">
            <div class="message-content">${processedMessage}</div>
        </div>
    `;
    
    // 在消息气泡外部添加时间戳
    messageHtml += `<span class="message-time">${time}</span>`;
    
    messageDiv.innerHTML = messageHtml;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示命令消息
function showCommandMessage(message, time) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'command-message';
    const timestamp = time || new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
        <p>${escapeHtml(message)}</p>
        <span class="message-time">${timestamp}</span>
    `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示电影卡片
function showMovieCard(sender, url) {
    const movieCard = document.createElement('div');
    movieCard.className = 'movie-card';
    movieCard.innerHTML = `
        <div class="movie-card-header">
            <span class="movie-card-sender">${escapeHtml(sender)} 分享了一部电影</span>
        </div>
        <div class="movie-thumbnail">▶</div>
    `;
    
    movieCard.addEventListener('click', () => playMovie(url));
    elements.chatMessages.appendChild(movieCard);
    scrollToBottom();
}

// 显示天气卡片
function showWeatherCard(weatherData) {
    console.log('接收到天气数据:', weatherData);
    
    // 适配新的数据结构 - 检查是否有weather_data字段（兼容旧格式）
    const actualData = weatherData.weather_data || weatherData;
    
    // 基于新设计的数据规范化
    const normalizedData = {
        city: extractCityName(actualData),
        weather: extractWeatherDescription(actualData),
        temperature: extractTemperature(actualData),
        air_quality: extractAirQuality(actualData),
        wind: extractWindInfo(actualData),
        // 移除alert字段
        // 特别处理forecast数据
        forecast: actualData.forecast || actualData.data || extractForecastData(actualData),
        timestamp: weatherData.timestamp || new Date().toLocaleTimeString(),
        request_user: weatherData.request_user
    };
    
    // 创建消息容器
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message command-message';
    
    // 创建天气容器 - 使用参考实现的样式结构
    const weatherContainer = document.createElement('div');
    weatherContainer.className = 'weather-container';
    
    // 创建天气卡片 - 添加动画相关类名
    const weatherCard = document.createElement('div');
    weatherCard.className = 'weather-card'; // show类将通过JS动态添加以触发动画
    
    // 头部：城市名称和天气状态
    const weatherHeader = document.createElement('div');
    weatherHeader.className = 'weather-header';
    
    const cityTitle = document.createElement('h2');
    cityTitle.textContent = normalizedData.city;
    
    const weatherStatus = document.createElement('div');
    weatherStatus.className = 'weather-status';
    weatherStatus.textContent = normalizedData.weather;
    
    weatherHeader.appendChild(cityTitle);
    weatherHeader.appendChild(weatherStatus);
    
    // 当前天气：温度和详细信息
    const currentWeather = document.createElement('div');
    currentWeather.className = 'current-weather';
    
    const currentTemp = document.createElement('div');
    currentTemp.className = 'current-temp';
    
    // 格式化温度显示 - 更健壮的数值提取
    const formatTemperature = (temp) => {
        if (typeof temp === 'number') {
            return Math.round(temp) + '°';
        } else if (typeof temp === 'string') {
            // 从字符串中提取数字（支持℃、°C等格式）
            const match = temp.match(/-?\d+\.?\d*/);
            return match ? Math.round(parseFloat(match[0])) + '°' : '0°';
        }
        return '0°';
    };
    
    currentTemp.textContent = formatTemperature(normalizedData.temperature);
    
    const currentInfo = document.createElement('div');
    currentInfo.className = 'current-info';
    
    // 空气质量
    const airQuality = document.createElement('div');
    airQuality.className = 'air-quality';
    airQuality.textContent = `空气质量: ${normalizedData.air_quality}`;
    
    // 风速
    const windInfo = document.createElement('div');
    windInfo.className = 'wind';
    windInfo.textContent = normalizedData.wind;
    
    currentInfo.appendChild(airQuality);
    currentInfo.appendChild(windInfo);
    
    currentWeather.appendChild(currentTemp);
    currentWeather.appendChild(currentInfo);
    
    // 添加预报部分 - 6天预报
    const forecastContainer = document.createElement('div');
    forecastContainer.className = 'forecast-container';
    
    // 确保forecast是数组
    if (Array.isArray(normalizedData.forecast) && normalizedData.forecast.length > 0) {
        // 最多显示6天预报
        const forecastDays = normalizedData.forecast.slice(0, 6);
        
        // 获取星期几的函数
        const getWeekday = (index) => {
            const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
            const today = new Date().getDay();
            return weekdays[(today + index) % 7];
        };
        
        forecastDays.forEach((day, index) => {
            const forecastItem = document.createElement('div');
            forecastItem.className = 'forecast-item';
            
            // 日期显示
            const forecastDate = document.createElement('div');
            forecastDate.className = 'forecast-date';
            
            // 处理日期格式 - 使用星期几
            if (day.date) {
                // 尝试解析日期获取星期
                const dateObj = new Date(day.date);
                if (!isNaN(dateObj.getTime())) {
                    forecastDate.textContent = getWeekday(index);
                } else {
                    forecastDate.textContent = getWeekday(index);
                }
            } else {
                forecastDate.textContent = getWeekday(index);
            }
            
            // 天气状况 - 使用emoji
            const forecastWeather = document.createElement('div');
            forecastWeather.className = 'forecast-weather';
            
            // 根据天气描述返回对应的emoji
            const getWeatherEmoji = (weather) => {
                const weatherLower = (weather || '').toLowerCase();
                if (weatherLower.includes('晴') || weatherLower.includes('sunny')) {
                    return '☀️';
                } else if (weatherLower.includes('云') || weatherLower.includes('cloud')) {
                    return '☁️';
                } else if (weatherLower.includes('雨') || weatherLower.includes('rain')) {
                    return '🌧️';
                } else if (weatherLower.includes('雪') || weatherLower.includes('snow')) {
                    return '❄️';
                } else if (weatherLower.includes('雾') || weatherLower.includes('fog')) {
                    return '🌫️';
                } else if (weatherLower.includes('雷') || weatherLower.includes('thunder')) {
                    return '⛈️';
                }
                return '🌤️';
            };
            
            forecastWeather.textContent = getWeatherEmoji(day.weather);
            
            // 温度范围
            const forecastTemp = document.createElement('div');
            forecastTemp.className = 'forecast-temp';
            
            // 如果有温度范围使用范围，否则使用单一温度
            if (day.tempRange) {
                forecastTemp.textContent = day.tempRange;
            } else if (day.lowTemp && day.highTemp) {
                forecastTemp.textContent = `${Math.round(day.lowTemp)}°-${Math.round(day.highTemp)}°`;
            } else {
                forecastTemp.textContent = formatTemperature(day.temperature);
            }
            
            forecastItem.appendChild(forecastDate);
            forecastItem.appendChild(forecastWeather);
            forecastItem.appendChild(forecastTemp);
            
            forecastContainer.appendChild(forecastItem);
        });
    }
    
    // 添加时间戳
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = normalizedData.timestamp;
    
    // 组装卡片内容
    weatherCard.appendChild(weatherHeader);
    weatherCard.appendChild(currentWeather);
    weatherCard.appendChild(forecastContainer);
    
    weatherContainer.appendChild(weatherCard);
    messageContainer.appendChild(weatherContainer);
    messageContainer.appendChild(timeElement);
    
    // 添加到聊天消息区域
    elements.chatMessages.appendChild(messageContainer);
    scrollToBottom();
    
    // 触发入场动画 - 基于参考实现的动画序列
    setTimeout(() => {
        weatherCard.classList.add('show');
        
        // 为预报项添加交错动画
        const forecastItems = weatherCard.querySelectorAll('.forecast-item');
        forecastItems.forEach((item, index) => {
            setTimeout(() => {
                item.classList.add('show');
            }, 200 + index * 100); // 200ms延迟后开始逐个显示
        });
    }, 10);
    
    // 如果是当前用户请求的天气，切换背景
    const currentUser = localStorage.getItem('username');
    if (normalizedData.request_user === currentUser) {
        changeBackgroundByWeather(normalizedData.weather);
    }
    
    return messageContainer;
}

// 辅助函数：提取城市名称 - 增强对WeatherSpider格式的支持
function extractCityName(data) {
    const cityKeys = ['city', 'location', 'name', '城市', '地区'];
    for (const key of cityKeys) {
        if (data[key]) return data[key];
    }
    return '未知城市';
}

// 辅助函数：提取天气描述 - 增强对WeatherSpider格式的支持
function extractWeatherDescription(data) {
    // 优先直接从顶层获取（WeatherSpider格式）
    const weatherKeys = ['weather', 'condition', 'description', '天气', '状态'];
    for (const key of weatherKeys) {
        if (data[key]) return data[key];
    }
    
    // 其次从data数组获取（兼容其他格式）
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        return data.data[0].weather || '未知';
    }
    
    return '未知';
}

// 辅助函数：提取温度信息 - 增强对WeatherSpider格式的支持
function extractTemperature(data) {
    // 优先直接从顶层获取（WeatherSpider格式）
    const tempKeys = ['temperature', 'temp', 'tempture', '气温', '当前温度'];
    for (const key of tempKeys) {
        if (data[key]) return data[key];
    }
    
    // 其次从data数组获取（兼容其他格式）
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        return data.data[0].temperature || '0';
    }
    
    return '0';
}

// 辅助函数：提取空气质量 - 增强对WeatherSpider格式的支持
function extractAirQuality(data) {
    // 优先直接从顶层获取（WeatherSpider格式）
    const aqKeys = ['air_quality', 'airQuality', 'aqi', '空气质量'];
    for (const key of aqKeys) {
        if (data[key]) return data[key];
    }
    
    // 其次从data数组获取（兼容其他格式）
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        return data.data[0].air_quality || '未知';
    }
    
    return '未知';
}

// 辅助函数：提取风力信息 - 增强对WeatherSpider格式的支持
function extractWindInfo(data) {
    // 优先直接从顶层获取（WeatherSpider格式）
    const windKeys = ['wind', 'wind_speed', '风力', '风速'];
    for (const key of windKeys) {
        if (data[key]) return data[key];
    }
    
    // 其次从data数组获取（兼容其他格式）
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        return data.data[0].wind || '无风';
    }
    
    return '无风';
}

// 辅助函数：提取预警信息
function extractWeatherAlert(data) {
    if (data.alert) return data.alert;
    if (data.alerts && Array.isArray(data.alerts) && data.alerts.length > 0) {
        return data.alerts[0].description || data.alerts[0].title || '天气预警';
    }
    if (data.weatherAlert) return data.weatherAlert;
    return null;
}

// 辅助函数：提取预报数据 - 增强对WeatherSpider格式的支持
function extractForecastData(data) {
    // 优先使用WeatherSpider的数据格式（从forecast字段获取）
    if (data.forecast && Array.isArray(data.forecast)) return data.forecast;
    // 其次从data字段获取（兼容其他格式）
    if (data.data && Array.isArray(data.data)) return data.data;
    // 兼容其他可能的格式
    if (data.daily && Array.isArray(data.daily)) return data.daily;
    return [];
}

// 辅助函数：生成预报数据（确保有6天数据）- 适配WeatherSpider格式
function generateForecastData(forecastData) {
    const result = [];
    const today = new Date();
    
    // 处理实际预报数据
    if (forecastData && forecastData.length > 0) {
        for (let i = 0; i < Math.min(6, forecastData.length); i++) {
            const day = forecastData[i];
            result.push({
                date: day.date || formatForecastDate(today, i + 1),
                icon: getWeatherIcon(day.weather || day.condition || day.description || ''),
                temp: day.temperature || formatForecastTemperature(day)
            });
        }
    }
    
    // 补充不足的天数
    const remainingDays = 6 - result.length;
    for (let i = result.length; i < 6; i++) {
        result.push({
            date: formatForecastDate(today, i + 1),
            icon: '☀️',
            temp: '--'
        });
    }
    
    return result;
}

// 辅助函数：格式化预报日期
function formatForecastDate(baseDate, daysLater) {
    const date = new Date(baseDate);
    date.setDate(date.getDate() + daysLater);
    return '周' + ['日', '一', '二', '三', '四', '五', '六'][date.getDay()];
}

// 辅助函数：格式化预报温度
function formatForecastTemperature(day) {
    // 尝试多种温度字段
    const tempFields = ['temperature', 'temp', 'high_temp', 'low_temp', 'max', 'min'];
    for (const field of tempFields) {
        if (day[field]) {
            const temp = day[field];
            if (typeof temp === 'number') {
                return Math.round(temp) + '°';
            } else if (typeof temp === 'string') {
                const match = temp.match(/\d+/);
                return match ? match[0] + '°' : '--';
            }
        }
    }
    return '--';
}

// 根据天气描述返回对应的图标 - 完全匹配WeatherSpider的图标映射
function getWeatherIcon(weatherDescription) {
    if (!weatherDescription) return '☀️';
    
    // 直接使用关键词匹配，不转为小写，保持与WeatherSpider一致
    const weatherIcons = {
        '晴': '☀️',
        '少云': '⛅',
        '多云': '⛅',
        '阴': '☁️',
        '小雨': '🌧️',
        '中雨': '🌧️',
        '大雨': '🌧️',
        '雪': '❄️',
        '雾': '🌫️',
        '霾': '🌫️',
        '雷阵雨': '⛈️'
    };
    
    // 精确匹配
    if (weatherIcons[weatherDescription]) {
        return weatherIcons[weatherDescription];
    }
    
    // 关键词匹配
    const description = weatherDescription.toLowerCase();
    const iconMap = [
        { keywords: ['晴', 'clear', 'sunny', 'sun'], icon: '☀️' },
        { keywords: ['多云', 'cloudy', 'partly', '少云'], icon: '⛅' },
        { keywords: ['阴', 'overcast', '阴天'], icon: '☁️' },
        { keywords: ['雨', 'rain'], icon: '🌧️' },
        { keywords: ['雷', 'thunder', 'storm'], icon: '⛈️' },
        { keywords: ['雪', 'snow'], icon: '❄️' },
        { keywords: ['雾', 'fog', 'mist'], icon: '🌫️' },
        { keywords: ['霾', 'haze', 'dust', '沙尘'], icon: '🌫️' }
    ];
    
    // 查找匹配的图标
    for (const item of iconMap) {
        if (item.keywords.some(keyword => description.includes(keyword))) {
            return item.icon;
        }
    }
    
    // 默认图标
    return '☀️';
}

// 天气类型与背景图片的映射关系
const weatherBackgroundMap = {
    '晴': 'Sunny.png',
    '晴天': 'Sunny.png',
    '少云': 'Cloudy.png',
    '多云': 'Cloudy.png',
    '阴天': 'DarkCloudy.png',
    '阴': 'DarkCloudy.png',
    '雾': 'Cloudy.png',
    '雾天': 'Cloudy.png',
    '霾': 'Cloudy.png',
    '雨': 'Rainy.png',
    '雨天': 'Rainy.png',
    '小雨': 'Rainy.png',
    '中雨': 'Rainy.png',
    '大雨': 'Rainy.png',
    '暴雨': 'Rainy.png',
    '雷阵雨': 'Rainy.png',
    '雪': 'Snowy.png',
    '雪天': 'Snowy.png',
    '小雪': 'Snowy.png',
    '中雪': 'Snowy.png',
    '大雪': 'Snowy.png',
    '暴雪': 'Snowy.png',
    '风': 'Cloudy.png',
    '大风': 'Cloudy.png',
    '台风': 'Cloudy.png'
};

// 根据天气类型切换背景图片
function changeBackgroundByWeather(weather) {
    // 获取body元素
    const body = document.body;
    
    // 根据天气类型获取对应的背景图片
    let backgroundImage = 'Sunny.png'; // 默认背景
    
    // 查找匹配的天气类型
    for (const [key, value] of Object.entries(weatherBackgroundMap)) {
        if (weather.includes(key)) {
            backgroundImage = value;
            break;
        }
    }
    
    // 构建背景图片URL
    const imageUrl = `Images/${backgroundImage}`;
    
    // 添加过渡效果类（如果不存在）
    if (!body.classList.contains('bg-transition')) {
        body.classList.add('bg-transition');
    }
    
    // 切换背景图片
    body.style.backgroundImage = `url('${imageUrl}')`;
    
    console.log(`背景已切换为: ${backgroundImage} (天气: ${weather})`);
}

// 播放电影
function playMovie(url) {
    elements.movieTitle.textContent = '电影播放';
    
    // 在解码电影前，添加指定的URL前缀
    const movieDecodePrefix = 'https://jx.m3u8.tv/jiexi/?url=';
    // 检查URL是否已经包含前缀，避免重复添加
    let finalUrl = url;
    if (!url.startsWith(movieDecodePrefix)) {
        finalUrl = movieDecodePrefix + encodeURIComponent(url);
        console.log('添加电影解码前缀:', finalUrl);
    }
    
    // 设置iframe属性
    elements.moviePlayer.src = finalUrl;
    elements.moviePlayer.width = '100%';
    elements.moviePlayer.height = '500'; // 设置合适的高度
    
    elements.movieModal.classList.add('show');
    // iframe不需要play()调用，移除它
}

// 更新用户列表
function updateUserList(users) {
    elements.userList.innerHTML = '';
    elements.onlineCount.textContent = users.length;
    
    users.forEach(user => {
        const isSelf = user === username;
        const listItem = document.createElement('li');
        listItem.className = isSelf ? 'self' : '';
        listItem.innerHTML = `
            <div class="user-avatar">${user.charAt(0).toUpperCase()}</div>
            <span class="user-name">${escapeHtml(user)}${isSelf ? ' (我)' : ''}</span>
        `;
        elements.userList.appendChild(listItem);
    });
}

// 发送消息
function sendMessage() {
    console.log('sendMessage函数被调用');
    const message = elements.messageInput.value.trim();
    
    console.log('检查消息内容:', message);
    if (!message) {
        console.log('消息为空，不发送');
        return;
    }
    
    console.log('检查认证状态:', isAuthenticated);
    if (!isAuthenticated) {
        showError('请先登录后再发送消息');
        return;
    }
    
    console.log('检查WebSocket连接状态:', socket ? `状态码: ${socket.readyState}, 连接状态: ${connectionState}` : '未连接');
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        showError('连接已断开，无法发送消息');
        return;
    }
    
    // 记录调试信息
    console.log('准备发送消息:', message, '用户名:', username);
    
    // 检查是否是以@开头的命令
    const isCommand = message.trim().startsWith('@');
    console.log('检测到@指令:', isCommand, '原始消息:', message);
    
    // 解析命令内容，提取@后面的命令部分
    let commandContent = message;
    let commandType = '';
    if (isCommand) {
        console.log('开始解析命令:', message);
        // 使用更宽松的正则表达式，确保能匹配中文字符
        const commandMatch = message.trim().match(/^@([^\s]+)/);
        console.log('正则匹配结果:', commandMatch);
        
        if (commandMatch && commandMatch.length > 1) {
            commandType = commandMatch[1];
            commandContent = message.trim().substring(commandMatch[0].length).trim();
            console.log('命令解析成功 - commandType:', commandType, 'commandContent:', commandContent);
        } else {
            console.log('正则匹配失败，使用默认处理');
            commandType = message.trim().substring(1).split(' ')[0]; // 直接提取@后面的内容直到第一个空格
            commandContent = message.trim().substring(commandType.length + 1).trim();
        }
    }
    
    // 使用结构化消息格式发送，兼容服务器期望的格式
    // 注意：服务器只在type为'message'时才检查@命令
    const msgData = {
        type: 'message', // 保持type为'message'，这样服务器才能处理@命令
        message: message,
        command: commandType, // 添加command字段提供额外信息
        content: commandContent,
        user: username, // 保留user字段用于标识用户
        timestamp: new Date().toISOString() // 添加时间戳便于调试
    };
    
    // 对于@指令消息，删除username字段（如果存在）
    // 注意：我们保留了user字段，因为服务端可能需要它来识别用户
    
    console.log(isCommand ? `检测到@指令: @${commandType}，将作为command类型发送` : '普通消息，作为message类型发送');
    console.log('命令内容解析:', { commandType, commandContent });
    
    console.log('准备发送的消息数据:', msgData);
    
    try {
        const jsonString = JSON.stringify(msgData);
        console.log('消息JSON字符串:', jsonString);
        socket.send(jsonString);
        elements.messageInput.value = '';
        console.log('消息已发送到服务器');
        
        // 取消本地消息显示，等待服务器广播回来
    } catch (error) {
        console.error('发送消息失败:', error);
        showError('发送消息失败，请重试');
    }
}

// 显示错误消息
function showError(message) {
    // 使用更友好的错误提示方式
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<p>${escapeHtml(message)}</p>`;
    elements.chatMessages.appendChild(errorDiv);
    scrollToBottom();
    
    // 同时在控制台显示错误
    console.error('错误:', message);
}

function showNewsCard(data) {
    console.log('接收到新闻数据:', data);
    
    // 适配新的数据结构
    const sender = data.sender || data.user || '新闻资讯';
    const content = data.content || data.message || '';
    const time = data.time || new Date().toLocaleTimeString();
    
    // 创建消息容器，使用与普通用户消息相同的样式
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message other';
    
    let messageHtml = `
        <div class="message-header">
            <div class="message-avatar">${sender.charAt(0).toUpperCase() || '📰'}</div>
            <span class="message-sender">${escapeHtml(sender)}</span>
        </div>
        <div class="message-content-wrapper">
            <div class="message-content">`;
    
    // 处理新闻文本内容
    if (content) {
        // 如果内容是对象格式
        if (typeof content === 'object' && content.text) {
            messageHtml += `<p>${escapeHtml(content.text)}</p>`;
        } else {
            // 如果是纯文本格式
            messageHtml += `<p>${escapeHtml(content)}</p>`;
        }
    }
    
    // 处理图片显示 - 适配新的image_content字段
    if (data.image_content && data.image_content.path) {
        let imageSrc = data.image_content.path;
        
        // 确保图片路径正确
        if (!imageSrc.startsWith('/')) {
            imageSrc = '/' + imageSrc;
        }
        
        // 直接在消息内容中显示图片，类似用户发送图片的格式
        messageHtml += `
            <div class="message-image-container" style="margin-top: 8px;">
                <img src="${escapeHtml(imageSrc)}" alt="新闻图片" class="message-image" 
                     style="width: 80%; max-width: 100%; height: auto; border-radius: 4px;" 
                     onload="console.log('新闻图片加载成功:', this.src)" 
                     onerror="console.error('新闻图片加载失败:', this.src); this.style.display='none';">
            </div>`;
    }
    // 兼容旧的image_path字段
    else if (data.image_path) {
        let imageSrc = data.image_path;
        if (!imageSrc.startsWith('/')) {
            imageSrc = '/' + imageSrc;
        }
        
        messageHtml += `
            <div class="message-image-container" style="margin-top: 8px;">
                <img src="${escapeHtml(imageSrc)}" alt="新闻图片" class="message-image" 
                     style="width: 80%; max-width: 100%; height: auto; border-radius: 4px;" 
                     onload="console.log('新闻图片加载成功:', this.src)" 
                     onerror="console.error('新闻图片加载失败:', this.src); this.style.display='none';">
            </div>`;
    }
    
    messageHtml += `
            </div>
        </div>
        <span class="message-time">${time}</span>
    `;
    
    messageDiv.innerHTML = messageHtml;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示音乐分享卡片
function showMusicCard(data) {
    console.log('接收到音乐分享数据:', data);
    
    // 获取必要信息
    const sender = data.sender || data.user || '系统';
    const apiUrl = data.api_url;
    const songId = data.song_id;
    const time = data.time || new Date().toLocaleTimeString();
    
    // 创建消息容器，使用与普通用户消息相同的样式
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message other';
    
    let messageHtml = `
        <div class="message-header">
            <div class="message-avatar">${sender.charAt(0).toUpperCase() || '🎵'}</div>
            <span class="message-sender">${escapeHtml(sender)}</span>
        </div>
        <div class="message-content-wrapper">
            <div class="message-content">
                <p>分享了一首音乐</p>`;
    
    // 添加音乐播放器iframe
    if (apiUrl) {
        messageHtml += `
                <div class="music-player-container" style="margin-top: 8px; border-radius: 4px; overflow: hidden;">
                    <iframe src="${escapeHtml(apiUrl)}" 
                            width="100%" 
                            height="50" 
                            frameborder="0" 
                            allow="autoplay; encrypted-media" 
                            allowfullscreen></iframe>
                </div>`;
    }
    
    messageHtml += `
            </div>
        </div>
        <span class="message-time">${time}</span>
    `;
    
    messageDiv.innerHTML = messageHtml;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 退出登录
function logout() {
    // 清除本地存储
    localStorage.removeItem('username');
    localStorage.removeItem('authToken'); // 清除可能存在的token
    localStorage.removeItem('serverUrl');
    localStorage.removeItem('authenticated');
    
    // 清除会话存储的密码信息
    sessionStorage.removeItem('sessionPassword');
    window.sessionPassword = null;
    
    // 关闭socket连接
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        socket.close();
    }
    
    // 清除定时器
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
    }
    
    // 跳转到登录页面
    window.location.href = 'login.html';
}

// 滚动到底部
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 监听页面关闭，断开连接
window.addEventListener('beforeunload', () => {
    // 页面关闭时清理资源
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
    }
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        socket.close(1000, '用户关闭页面');
    }
});

// 当DOM加载完成后初始化应用
window.addEventListener('DOMContentLoaded', init);

// 防止页面刷新时丢失消息提醒
window.addEventListener('keydown', (e) => {
    // 阻止F5刷新
    if (e.key === 'F5') {
        e.preventDefault();
        if (confirm('确定要离开聊天室吗？')) {
            window.location.reload();
        }
    }
    // 阻止Ctrl+R刷新
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        if (confirm('确定要离开聊天室吗？')) {
            window.location.reload();
        }
    }
});