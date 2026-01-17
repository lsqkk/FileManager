# server.py
#!/usr/bin/env python3
"""
文件分类Web服务器 - 主入口
"""

import os
import sys
import webbrowser
from threading import Timer
from app import create_app

def open_browser():
    """自动打开浏览器"""
    webbrowser.open('http://localhost:5180')

def main():
    """主函数"""
    print("=" * 60)
    print("Quark File Manager")
    print("=" * 60)
    
    # 检查必要的目录
    for folder in ['templates', 'static/css', 'static/js']:
        os.makedirs(folder, exist_ok=True)
    
    # 创建应用
    app = create_app()
    
    # 1秒后自动打开浏览器
    Timer(1, open_browser).start()
    
    # 启动服务器
    print(f"服务器启动中...")
    print(f"访问地址: http://localhost:5180")
    print("按 Ctrl+C 停止服务器")
    print("-" * 60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5180,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)

if __name__ == '__main__':
    main()