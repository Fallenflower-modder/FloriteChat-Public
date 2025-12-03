// 登录页面JavaScript

// 当DOM加载完成后执行
window.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const serverSelect = document.getElementById('server');
    const errorMessage = document.getElementById('error-message');
    const registerLink = document.getElementById('register-link');
    
    // 注册链接点击事件
    if (registerLink) {
        registerLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = 'register.html';
        });
    }
    
    // 加载服务器配置
    async function loadServerConfig() {
        try {
            // 注意：在实际部署时，需要将config.json放在客户端可访问的位置
            // 这里为了开发方便，我们先硬编码一些服务器地址
            const servers = [
                { name: '本地服务器', url: 'ws://localhost:8766' },
                { name: '服务器1', url: 'ws://192.168.1.100:8766' },
                { name: '服务器2', url: 'ws://192.168.1.101:8766' }
            ];
            
            // 填充服务器选择下拉框
            serverSelect.innerHTML = '';
            servers.forEach(server => {
                const option = document.createElement('option');
                option.value = server.url;
                option.textContent = server.name;
                serverSelect.appendChild(option);
            });
        } catch (error) {
            console.error('加载服务器配置失败:', error);
            showError('加载服务器配置失败，请稍后重试');
        }
    }
    
    // 显示错误消息
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 3000);
    }
    
    // 验证用户名格式
    function validateUsername(username) {
        if (!username || username.trim().length === 0) {
            return '用户名不能为空';
        }
        if (username.length < 3) {
            return '用户名长度不能少于3个字符';
        }
        if (username.length > 20) {
            return '用户名长度不能超过20个字符';
        }
        // 检查是否包含特殊字符
        if (/[<>'"&]/g.test(username)) {
            return '用户名不能包含特殊字符';
        }
        return null;
    }
    
    // 验证密码格式
    function validatePassword(password) {
        if (!password || password.trim().length === 0) {
            return '密码不能为空';
        }
        if (password.length < 6) {
            return '密码长度不能少于6个字符';
        }
        return null;
    }
    
    // 处理登录表单提交
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const serverUrl = serverSelect.value;
        
        // 验证用户名和密码
        const usernameError = validateUsername(username);
        if (usernameError) {
            showError(usernameError);
            return;
        }
        
        const passwordError = validatePassword(password);
        if (passwordError) {
            showError(passwordError);
            return;
        }
        
        // 尝试连接服务器并验证用户
        try {
            // 创建WebSocket连接
            const ws = new WebSocket(serverUrl);
            
            // 设置超时
            const loginTimeout = setTimeout(() => {
                showError('登录超时，请检查服务器连接');
                ws.close();
            }, 10000);
            
            // 处理连接打开事件
            ws.onopen = () => {
                // 发送登录请求
                ws.send(JSON.stringify({
                    type: 'login',
                    username: username,
                    password: password
                }));
            };
            
            // 处理接收消息事件
            ws.onmessage = (event) => {
                clearTimeout(loginTimeout);
                
                try {
                    const response = JSON.parse(event.data);
                    
                    if (response.type === 'login_response') {
                            if (response.success) {
                                // 登录成功
                                localStorage.setItem('username', username);
                                localStorage.setItem('serverUrl', serverUrl);
                                localStorage.setItem('authenticated', 'true');
                                
                                // 将密码临时存储在内存和sessionStorage中（仅会话期间有效，不会保存到localStorage）
                                window.sessionPassword = password;
                                sessionStorage.setItem('sessionPassword', password);
                                
                                // 关闭当前连接
                                ws.close();
                                
                                // 跳转到聊天页面
                                window.location.href = 'chat.html';
                            } else {
                                // 登录失败
                                showError(response.message || '登录失败，请重试');
                                ws.close();
                            }
                    }
                } catch (error) {
                    showError('处理服务器响应时出错');
                    console.error('处理服务器响应错误:', error);
                    ws.close();
                }
            };
            
            // 处理连接错误事件
            ws.onerror = (error) => {
                clearTimeout(loginTimeout);
                showError('无法连接到服务器，请检查网络连接和服务器地址');
                console.error('WebSocket连接错误:', error);
                ws.close();
            };
            
            // 处理连接关闭事件
            ws.onclose = () => {
                clearTimeout(loginTimeout);
                // 连接关闭的处理逻辑已在其他事件处理器中完成
            };
        } catch (error) {
            showError('登录过程中出现错误');
            console.error('登录错误:', error);
        }
    });
    
    // 加载服务器配置
    loadServerConfig();
    
    // 添加一些额外的用户体验改进
    usernameInput.addEventListener('input', () => {
        errorMessage.style.display = 'none';
    });
    
    passwordInput.addEventListener('input', () => {
        errorMessage.style.display = 'none';
    });
    
    // 添加回车键提交表单
    passwordInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            loginForm.dispatchEvent(new Event('submit'));
        }
    });
});

// 预加载一些资源，提升用户体验
function preloadResources() {
    const resources = [
        'css/style.css',
        'css/chat.css'
    ];
    
    resources.forEach(resource => {
        if (resource.endsWith('.css')) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = resource;
            document.head.appendChild(link);
        }
    });
}

// 预加载资源
preloadResources();