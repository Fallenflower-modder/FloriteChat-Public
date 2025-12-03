document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('error-message');
    const serverSelect = document.getElementById('serverSelect');
    
    // 创建状态提示元素
    const statusContainer = document.createElement('div');
    statusContainer.className = 'status-message-container';
    statusContainer.style.display = 'none';
    statusContainer.style.position = 'fixed';
    statusContainer.style.top = '20px';
    statusContainer.style.left = '50%';
    statusContainer.style.transform = 'translateX(-50%)';
    statusContainer.style.padding = '12px 24px';
    statusContainer.style.borderRadius = '8px';
    statusContainer.style.color = 'white';
    statusContainer.style.fontWeight = 'bold';
    statusContainer.style.zIndex = '1000';
    statusContainer.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    statusContainer.style.transition = 'all 0.3s ease';
    document.body.appendChild(statusContainer);
    
    // 加载服务器配置
    loadServerConfig();

    function loadServerConfig() {
        // 服务器列表
        const servers = [
            { name: '本地服务器', url: 'ws://localhost:8766' },
            { name: '局域网服务器1', url: 'ws://192.168.1.100:8766' },
            { name: '局域网服务器2', url: 'ws://192.168.1.101:8766' }
        ];
        
        // 清空并填充服务器选择下拉框
        serverSelect.innerHTML = '<option value="">请选择服务器</option>';
        servers.forEach(server => {
            const option = document.createElement('option');
            option.value = server.url;
            option.textContent = server.name;
            serverSelect.appendChild(option);
        });
        
        // 设置默认选中本地服务器
        const localServerOption = serverSelect.querySelector('option[value="ws://localhost:8766"]');
        if (localServerOption) {
            localServerOption.selected = true;
        }
    }

    registerForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // 表单验证
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // 清空之前的错误信息
        errorMessage.textContent = '';
        errorMessage.style.display = 'none';
        
        // 验证用户名
        if (!username || username.length < 3 || username.length > 20) {
            showError('用户名长度必须在3-20个字符之间');
            showStatusMessage('用户名长度必须在3-20个字符之间', false);
            return;
        }
        
        // 验证密码
        if (!password || password.length < 6) {
            showError('密码长度至少为6个字符');
            showStatusMessage('密码长度至少为6个字符', false);
            return;
        }
        
        // 验证两次输入的密码是否一致
        if (password !== confirmPassword) {
            showError('两次输入的密码不一致');
            showStatusMessage('两次输入的密码不一致', false);
            return;
        }
        
        // 发送注册请求
        registerUser(username, password);
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
    
    // 显示状态消息（成功或错误）
    function showStatusMessage(message, isSuccess = false) {
        statusContainer.textContent = message;
        statusContainer.style.display = 'block';
        
        // 设置样式
        if (isSuccess) {
            statusContainer.style.backgroundColor = '#4CAF50'; // 成功绿色
            statusContainer.innerHTML = `<i class="success-icon">✓</i> ${message}`;
        } else {
            statusContainer.style.backgroundColor = '#f44336'; // 错误红色
            statusContainer.innerHTML = `<i class="error-icon">✗</i> ${message}`;
        }
        
        // 添加图标样式
        const iconStyle = document.createElement('style');
        iconStyle.textContent = `
            .success-icon, .error-icon {
                margin-right: 8px;
                font-style: normal;
            }
        `;
        document.head.appendChild(iconStyle);
        
        // 3秒后自动隐藏
        setTimeout(() => {
            statusContainer.style.opacity = '0';
            setTimeout(() => {
                statusContainer.style.display = 'none';
                statusContainer.style.opacity = '1';
            }, 300);
        }, 3000);
    }

    function registerUser(username, password) {
        // 显示加载状态
        const submitButton = registerForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = '注册中...';
        
        // 获取选择的服务器地址
        const wsUrl = serverSelect.value;
        
        if (!wsUrl) {
            showError('请选择服务器');
            showStatusMessage('请选择服务器', false);
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            return;
        }
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            // 发送注册请求
            const registerMessage = {
                type: 'register',
                username: username,
                password: password
            };
            ws.send(JSON.stringify(registerMessage));
        };
        
        ws.onmessage = function(event) {
            try {
                const response = JSON.parse(event.data);
                
                if (response.type === 'register_response') {
                    if (response.success) {
                        // 注册成功，使用浏览器弹窗提示并跳转到登录页面
                        alert('注册成功！正在跳转到登录页面...');
                        setTimeout(() => {
                            window.location.href = 'login.html';
                        }, 500);
                    } else {
                        // 注册失败，使用浏览器弹窗提示
                        const errorText = response.message || '注册失败，请稍后重试';
                        alert(errorText);
                        showError(errorText);
                    }
                }
            } catch (e) {
                const errorText = '服务器响应格式错误';
                alert(errorText);
                showError(errorText);
            } finally {
                // 恢复按钮状态
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket错误:', error);
            const errorText = '连接服务器失败，请检查网络或服务器状态';
            showError(errorText);
            showStatusMessage(errorText, false);
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            ws.close();
        };
        
        ws.onclose = function() {
            // WebSocket连接关闭，确保按钮状态恢复
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        };
    }
});