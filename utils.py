#!/usr/bin/env python3
"""
工具函数模块
"""

import os
import re
import json
import shutil
import configparser
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests


def load_config(config_file: str = "config.ini") -> Optional[configparser.ConfigParser]:
    """加载配置文件"""
    config = configparser.ConfigParser()
    
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        print("请创建 config.ini 文件并配置API密钥")
        return None
    
    try:
        config.read(config_file, encoding='utf-8')
        
        # 验证必要配置
        required_sections = ['API', 'CLASSIFICATION', 'PATHS', 'SETTINGS']
        for section in required_sections:
            if section not in config:
                print(f"错误: 配置文件中缺少 [{section}] 部分")
                return None
        
        # 验证API密钥
        api_key = config['API'].get('api_key', '').strip()
        if not api_key or api_key == 'your_deepseek_api_key_here':
            print("错误: 请先在 config.ini 中配置您的API密钥")
            return None
            
        return config
        
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return None


def get_files(source_folder: str, extensions: List[str] = None) -> List[str]:
    """获取指定文件夹中的所有文件（支持多种扩展名）"""
    if not os.path.exists(source_folder):
        print(f"警告: 源文件夹 {source_folder} 不存在，正在创建...")
        os.makedirs(source_folder, exist_ok=True)
        return []
    
    all_files = []
    
    for file in os.listdir(source_folder):
        if os.path.isfile(os.path.join(source_folder, file)):
            if extensions:
                # 检查文件扩展名
                file_ext = os.path.splitext(file)[1].lower()
                if any(file_ext == ext.lower() or file_ext == f".{ext.lower()}" for ext in extensions):
                    all_files.append(file)
            else:
                # 如果没有指定扩展名，返回所有文件
                all_files.append(file)
    
    return sorted(all_files)


def build_ai_prompt(filenames: List[str], 
                   categories: List[str], category_descriptions: str) -> str:
    """构建发送给AI的提示词（仅基于文件名）"""
    
    # 构建分类标签映射（索引从1开始）
    category_map = "\n".join([f"{i+1}: {cat}" for i, cat in enumerate(categories)])
    
    prompt = f"""请分析以下文件的文件名，并根据文件名推测其内容主题，将其分类到以下类别之一：

分类标签（请返回对应的数字序号）：
{category_map}

分类要求：
1. 仔细分析文件名，包括扩展名
2. 根据文件名推测内容的主要方向进行分类
3. 如果文件名涉及多个领域，选择最突出的主题
4. 确保分类准确合理

请按照以下格式输出分类结果：
序号:标签序号
例如：
1:3
2:1
3:7

只需要输出序号和对应的标签序号，每行一个，不要输出其他任何内容。

需要分类的文件列表：
"""
    
    # 添加每个文件的信息
    for i, filename in enumerate(filenames, 1):
        prompt += f"\n[{i}] 文件名: {filename}"
        prompt += "\n" + "-"*40
    
    return prompt


def call_ai_api(filenames: List[str],
                categories: List[str], category_descriptions: str,
                api_config: Dict[str, str]) -> str:
    """调用AI API进行分类（仅基于文件名）"""
    
    # 构建提示词
    prompt = build_ai_prompt(filenames, categories, category_descriptions)
    
    # API配置
    api_key = api_config.get('api_key')
    base_url = api_config.get('base_url', 'https://api.deepseek.com')
    model = api_config.get('model', 'deepseek-chat')
    
    # 准备请求数据
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system", 
                "content": "你是一个专业的文件分类助手，需要根据文件名推测内容并进行准确分类。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,  # 低温度以获得更确定的输出
        "max_tokens": 500
    }
    
    # 确定API端点
    if "openai.com" in base_url:
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/chat/completions"
    
    try:
        print(f"调用AI API ({model})...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result['choices'][0]['message']['content'].strip()
        
        print("AI响应接收成功")
        return ai_response
        
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        raise
    except (KeyError, IndexError) as e:
        print(f"解析API响应失败: {e}")
        raise


def parse_ai_response(response: str, expected_count: int, category_count: int) -> List[int]:
    """解析AI返回的分类结果"""
    classifications = []
    
    # 按行分割
    lines = response.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 匹配格式: "序号:标签序号"
        match = re.match(r'^(\d+)[:\s]+(\d+)$', line)
        if match:
            file_index = int(match.group(1))
            category_index = int(match.group(2))
            
            # 验证索引范围
            if 1 <= file_index <= expected_count and 1 <= category_index <= category_count:
                classifications.append(category_index - 1)  # 转换为0-based索引
    
    # 如果解析出的结果数量不对，尝试其他格式
    if len(classifications) != expected_count:
        print(f"警告: 解析结果数量({len(classifications)})与预期({expected_count})不符")
        print(f"AI原始响应:\n{response}")
        
        # 尝试只提取数字
        all_numbers = re.findall(r'\b\d+\b', response)
        if len(all_numbers) >= expected_count:
            classifications = []
            for i in range(expected_count):
                if i < len(all_numbers):
                    num = int(all_numbers[i])
                    if 1 <= num <= category_count:
                        classifications.append(num - 1)
    
    return classifications


def parse_category_paths(config: configparser.ConfigParser) -> Dict[str, str]:
    """解析分类标签的目标路径配置"""
    category_paths = {}
    
    if 'CLASSIFICATION' in config and 'category_paths' in config['CLASSIFICATION']:
        paths_text = config['CLASSIFICATION']['category_paths']
        
        # 解析每行配置
        for line in paths_text.strip().split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
                
            parts = line.split(':', 1)
            if len(parts) == 2:
                category = parts[0].strip()
                path = parts[1].strip()
                category_paths[category] = path
    
    return category_paths


def classify_files(filenames: List[str], classifications: List[int], 
                  categories: List[str], source_folder: str, 
                  target_base_folder: str,
                  category_paths: Dict[str, str] = None) -> Dict[str, Any]:
    """根据分类结果整理文件"""
    
    # 如果没有提供自定义路径映射，使用默认目标文件夹
    if category_paths is None:
        category_paths = {}
    
    # 分类统计
    category_stats = {category: 0 for category in categories}
    success_count = 0
    failed_count = 0
    failed_files = []
    
    # 记录每个文件的目标路径，用于可能的撤回操作
    file_target_paths = {}
    
    # 复制文件到对应分类文件夹
    for i, (filename, category_idx) in enumerate(zip(filenames, classifications)):
        if i >= len(classifications):
            print(f"警告: 文件 {filename} 没有对应的分类，跳过")
            failed_count += 1
            failed_files.append(filename)
            continue
            
        if category_idx < 0 or category_idx >= len(categories):
            print(f"警告: 文件 {filename} 的分类索引 {category_idx} 无效，跳过")
            failed_count += 1
            failed_files.append(filename)
            continue
        
        category = categories[category_idx]
        source_path = os.path.join(source_folder, filename)
        
        # 确定目标路径：优先使用自定义路径，否则使用默认路径
        if category in category_paths:
            target_folder = category_paths[category]
            # 确保路径是相对于当前目录的绝对路径
            if not os.path.isabs(target_folder):
                target_folder = os.path.abspath(target_folder)
        else:
            target_folder = os.path.join(target_base_folder, category)
        
        # 确保目标文件夹存在
        os.makedirs(target_folder, exist_ok=True)
        
        target_path = os.path.join(target_folder, filename)
        
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                category_stats[category] += 1
                success_count += 1
                
                # 记录文件的目标路径，用于可能的撤回操作
                file_target_paths[filename] = target_path
                
                # 显示目标路径信息
                if category in category_paths:
                    print(f"  ✓ {filename} → {category} ({target_folder})")
                else:
                    print(f"  ✓ {filename} → {category}")
            else:
                print(f"  ✗ {filename}: 源文件不存在")
                failed_count += 1
                failed_files.append(filename)
                
        except Exception as e:
            print(f"  ✗ {filename}: 复制失败 - {e}")
            failed_count += 1
            failed_files.append(filename)
    
    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'failed_files': failed_files,
        'category_stats': category_stats,
        'file_target_paths': file_target_paths  # 新增：记录目标路径
    }


def rollback_classification(file_target_paths: Dict[str, str]) -> Dict[str, any]:
    """撤回分类操作：删除已复制到目标位置的文件"""
    
    deleted_count = 0
    failed_to_delete_count = 0
    failed_files = []
    
    print("\n[撤回操作] 正在删除已分类的文件...")
    
    for filename, target_path in file_target_paths.items():
        try:
            if os.path.exists(target_path):
                os.remove(target_path)
                deleted_count += 1
                print(f"  ✓ 已删除: {target_path}")
            else:
                print(f"  ⚠ {filename}: 目标文件不存在，无需删除")
                
        except Exception as e:
            print(f"  ✗ 删除失败 {target_path}: {e}")
            failed_to_delete_count += 1
            failed_files.append(filename)
    
    # 尝试删除空的分类文件夹
    for target_path in set(os.path.dirname(path) for path in file_target_paths.values()):
        try:
            if os.path.exists(target_path) and not os.listdir(target_path):
                os.rmdir(target_path)
                print(f"  ✓ 已删除空文件夹: {target_path}")
        except Exception as e:
            print(f"  ⚠ 无法删除文件夹 {target_path}: {e}")
    
    return {
        'deleted_count': deleted_count,
        'failed_to_delete_count': failed_to_delete_count,
        'failed_files': failed_files
    }


def create_default_config():
    """创建默认配置文件"""
    config_content = """[API]
# DeepSeek API配置
api_key = your_deepseek_api_key_here
base_url = https://api.deepseek.com
model = deepseek-chat

[CLASSIFICATION]
# 自定义分类标签（用逗号分隔）
categories = 干货,奇文,史政,数学,信息学,学科,资源教程

# 分类路径映射（格式：分类标签:目标路径，相对于当前目录）
category_paths = 
    干货:../干货
    数学:../学习/数学
    信息学:../学习/信息学

[PATHS]
# 文件路径配置（现在作为默认路径）
source_folder = ./source_files
target_base_folder = ./classified_files

[SETTINGS]
# API超时时间（秒）
api_timeout = 30
# 最大重试次数
max_retries = 3
"""
    
    with open('config.ini', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("已创建默认配置文件 config.ini")
    print("请编辑该文件并填入您的API密钥")


if __name__ == "__main__":
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists("config.ini"):
        create_default_config()
    else:
        print("配置文件已存在")