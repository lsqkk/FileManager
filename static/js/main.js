// static/js/main.js
/**
 * 主JavaScript文件
 * 处理通用交互和工具函数
 */

// 全局工具函数
class FileClassifier {
    constructor() {
        this.currentSelections = {};
    }

    // 选择文件夹（模拟）
    selectFolder() {
        // 在实际应用中，这里会调用系统对话框
        return new Promise((resolve) => {
            // 发送请求到后端获取路径
            fetch('/api/files/browse', {
                method: 'POST'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        resolve(data.path);
                    } else {
                        resolve('');
                    }
                })
                .catch(() => resolve(''));
        });
    }

    // 保存配置项
    saveConfig(configData) {
        return fetch('/api/config/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(configData)
        })
            .then(response => response.json());
    }

    // 显示通知
    showNotification(message, type = 'info') {
        // 移除现有通知
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }

        // 创建新通知
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        // 添加样式
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            border-left: 4px solid ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#2563eb'};
        `;

        // 添加动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);

        // 关闭按钮事件
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        });

        // 自动消失
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
}

// 创建全局实例
window.fileClassifier = new FileClassifier();

// 通用表单处理
document.addEventListener('DOMContentLoaded', function () {
    // 处理所有表单提交
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            const submitBtn = form.querySelector('[type="submit"]');
            const originalText = submitBtn.innerHTML;

            // 显示加载状态
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
            submitBtn.disabled = true;

            // 收集表单数据
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            // 发送请求
            fetch(form.action, {
                method: form.method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        fileClassifier.showNotification(result.message || '操作成功', 'success');

                        // 如果有重定向
                        if (result.redirect) {
                            setTimeout(() => {
                                window.location.href = result.redirect;
                            }, 1000);
                        }
                    } else {
                        fileClassifier.showNotification(result.message || '操作失败', 'error');
                    }
                })
                .catch(error => {
                    fileClassifier.showNotification('网络错误: ' + error.message, 'error');
                })
                .finally(() => {
                    // 恢复按钮状态
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    });

    // 处理选择框变化
    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            this.style.backgroundColor = 'white';
            this.style.color = 'var(--text-primary)';
        });
    });

    // 添加CSS样式
    const style = document.createElement('style');
    style.textContent = `
        .notification-content {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0;
            font-size: 1rem;
        }
        
        .notification-close:hover {
            color: var(--text-primary);
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        select:disabled {
            background-color: #f1f5f9;
            color: #94a3b8;
            cursor: not-allowed;
        }
        
        input:disabled {
            background-color: #f1f5f9;
            color: #94a3b8;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
});