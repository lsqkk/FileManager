# app/utils.py
"""
Web应用专用工具函数
"""

import os
import json
import tempfile
from pathlib import Path

def save_temp_data(data, prefix='classification_'):
    """保存临时数据到文件"""
    temp_dir = tempfile.gettempdir()
    temp_file = Path(temp_dir) / f"{prefix}{os.getpid()}.json"
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return temp_file

def load_temp_data(temp_file):
    """从临时文件加载数据"""
    if temp_file.exists():
        with open(temp_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def validate_folder_path(path):
    """验证文件夹路径"""
    if not path:
        return False, "路径不能为空"
    
    # 检查相对路径或绝对路径
    if not os.path.isabs(path):
        # 如果是相对路径，确保在当前目录下存在
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                return False, f"无法创建目录: {e}"
    
    return True, "路径有效"

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"