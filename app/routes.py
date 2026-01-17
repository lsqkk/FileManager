# app/routes.py
from flask import (
    Blueprint, render_template, request, jsonify, 
    send_from_directory, current_app
)
import os
import json
import configparser
from pathlib import Path
import threading
import time

# 导入原有工具函数
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import (
    load_config, get_files, call_ai_api, 
    parse_ai_response, classify_files, parse_category_paths,
    rollback_classification
)

# 全局变量存储分类状态
classification_status = {
    'current_batch': 0,
    'total_batches': 0,
    'status': 'idle',
    'progress': 0,
    'current_file': '',
    'results': {},
    'files': [],
    'categories': [],
    'classifications': []
}

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页"""
    return render_template('index.html')

@main_bp.route('/config')
def config_page():
    """配置页面"""
    config = load_config()
    if not config:
        # 创建默认配置
        from utils import create_default_config
        create_default_config()
        config = load_config()
    
    # 解析配置
    categories = []
    if 'CLASSIFICATION' in config and 'categories' in config['CLASSIFICATION']:
        categories = [c.strip() for c in config['CLASSIFICATION']['categories'].split(',')]
    
    return render_template('config.html', 
                         config=config,
                         categories=categories)

# 添加分类结果页面路由
@main_bp.route('/classify/results')
def classification_results():
    """分类结果页面"""
    return render_template('results.html')

@main_bp.route('/api/config/save', methods=['POST'])
def save_config():
    """保存配置"""
    try:
        data = request.json
        
        # 读取现有配置
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        # 更新API配置
        if 'api' in data:
            for key, value in data['api'].items():
                config.set('API', key, value)
        
        # 更新分类配置
        if 'classification' in data:
            cats = data['classification'].get('categories', '')
            if cats:
                config.set('CLASSIFICATION', 'categories', cats)
            
            paths = data['classification'].get('category_paths', '')
            if paths:
                config.set('CLASSIFICATION', 'category_paths', paths)
            
            descs = data['classification'].get('category_descriptions', '')
            if descs:
                config.set('CLASSIFICATION', 'category_descriptions', descs)
        
        # 更新路径配置
        if 'paths' in data:
            for key, value in data['paths'].items():
                config.set('PATHS', key, value)
        
        # 保存配置
        with open('config.ini', 'w', encoding='utf-8') as f:
            config.write(f)
        
        return jsonify({'success': True, 'message': '配置已保存'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/config/get')
def get_config():
    """获取当前配置"""
    try:
        config = load_config()
        if not config:
            return jsonify({'success': False, 'message': '配置加载失败'})
        
        config_dict = {
            'api': dict(config['API']),
            'classification': dict(config['CLASSIFICATION']),
            'paths': dict(config['PATHS']),
            'settings': dict(config['SETTINGS'])
        }
        
        return jsonify({'success': True, 'config': config_dict})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/files/scan')
def scan_files():
    """扫描文件"""
    config = load_config()
    if not config:
        return jsonify({'success': False, 'message': '配置加载失败'})
    
    source_folder = config['PATHS']['source_folder']
    files = get_files(source_folder)
    
    # 获取分类标签
    categories = []
    if 'CLASSIFICATION' in config and 'categories' in config['CLASSIFICATION']:
        categories = [c.strip() for c in config['CLASSIFICATION']['categories'].split(',')]
    
    # 重置状态
    classification_status.update({
        'current_batch': 0,
        'total_batches': (len(files) + 29) // 30,  # 每批30个文件
        'status': 'idle',
        'progress': 0,
        'current_file': '',
        'results': {},
        'files': files,
        'categories': categories,  # 这里设置categories
        'classifications': []
    })
    
    return jsonify({
        'success': True,
        'files': files,
        'count': len(files),
        'batches': classification_status['total_batches'],
        'categories': len(categories)  # 返回分类数量
    })

@main_bp.route('/api/classify/start', methods=['POST'])
def start_classification():
    """开始分类"""
    if classification_status['status'] == 'processing':
        return jsonify({'success': False, 'message': '分类正在进行中'})
    
    # 启动分类线程
    thread = threading.Thread(target=classification_worker)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': '分类已开始'})

def classification_worker():
    """分类工作线程"""
    try:
        classification_status['status'] = 'processing'
        classification_status['progress'] = 0
        
        # 加载配置
        config = load_config()
        if not config:
            classification_status['status'] = 'error'
            classification_status['message'] = '配置加载失败'
            return
        
        # 获取分类标签
        categories = [c.strip() for c in config['CLASSIFICATION']['categories'].split(',')]
        classification_status['categories'] = categories  # 确保这里设置了categories
        
        files = classification_status['files']
        total_files = len(files)
        batches = classification_status['total_batches']
        
        all_classifications = []
        
        # 分批处理
        for batch_num in range(batches):
            classification_status['current_batch'] = batch_num + 1
            
            # 获取当前批次文件
            start_idx = batch_num * 30
            end_idx = min((batch_num + 1) * 30, total_files)
            batch_files = files[start_idx:end_idx]
            
            # 调用AI分类
            try:
                response = call_ai_api(
                    batch_files,
                    categories,
                    config['CLASSIFICATION'].get('category_descriptions', ''),
                    config['API']
                )
                
                # 解析响应
                batch_classifications = parse_ai_response(
                    response, 
                    len(batch_files), 
                    len(categories)
                )
                
                all_classifications.extend(batch_classifications)
                
                # 更新进度
                classification_status['progress'] = int((end_idx / total_files) * 100)
                
            except Exception as e:
                print(f"批次 {batch_num + 1} 处理失败: {e}")
                # 如果失败，为这批文件添加默认分类（最后一个分类：其他）
                all_classifications.extend([len(categories) - 1] * len(batch_files))
        
        # 保存分类结果
        classification_status['classifications'] = all_classifications
        classification_status['status'] = 'completed'
        classification_status['progress'] = 100
        
        # 确保结果对象被正确初始化
        classification_status['results'] = {
            'files': [],
            'categories': categories
        }
        
    except Exception as e:
        classification_status['status'] = 'error'
        classification_status['message'] = str(e)
        print(f"分类工作线程错误: {e}")

@main_bp.route('/api/classify/status')
def get_classification_status():
    """获取分类状态"""
    return jsonify({
        'status': classification_status['status'],
        'progress': classification_status['progress'],
        'current_batch': classification_status['current_batch'],
        'total_batches': classification_status['total_batches'],
        'current_file': classification_status['current_file']
    })

@main_bp.route('/api/classify/results')
def get_classification_results():
    """获取分类结果"""
    # 如果分类未完成，尝试从状态中获取已有的结果
    if classification_status['status'] != 'completed':
        # 检查是否已经有部分结果
        if classification_status['results'] and classification_status['results'].get('files'):
            files = classification_status['files']
            categories = classification_status.get('categories', [])
            results = classification_status['results']['files']
            
            return jsonify({
                'success': True,
                'results': results,
                'categories': categories,
                'total_files': len(files)
            })
        return jsonify({'success': False, 'message': '分类未完成或没有结果'})
    
    files = classification_status['files']
    categories = classification_status.get('categories', [])
    
    # 如果categories为空，尝试从配置中加载
    if not categories:
        config = load_config()
        if config and 'CLASSIFICATION' in config and 'categories' in config['CLASSIFICATION']:
            categories = [c.strip() for c in config['CLASSIFICATION']['categories'].split(',')]
    
    classifications = classification_status.get('classifications', [])
    
    # 构建结果列表
    results = []
    for i, (filename, cat_idx) in enumerate(zip(files, classifications)):
        if i < len(classifications):
            category_name = '其他'
            if cat_idx < len(categories):
                category_name = categories[cat_idx]
            elif categories and len(categories) > 0:
                # 如果索引超出范围，使用最后一个分类
                category_name = categories[-1]
            
            results.append({
                'id': i + 1,
                'filename': filename,
                'category_index': cat_idx,
                'category': category_name
            })
    
    # 保存结果到状态
    classification_status['results'] = {
        'files': results,
        'categories': categories
    }
    
    return jsonify({
        'success': True,
        'results': results,
        'categories': categories,
        'total_files': len(files)
    })

@main_bp.route('/api/classify/adjust', methods=['POST'])
def adjust_classification():
    """调整分类结果"""
    try:
        data = request.json
        file_id = data.get('file_id')
        category_index = data.get('category_index')
        
        # 找到对应的分类结果并更新
        results = classification_status.get('results', {}).get('files', [])
        for file_data in results:
            if file_data['id'] == file_id:
                file_data['category_index'] = category_index
                file_data['category'] = classification_status['categories'][category_index]
                
                # 更新主分类列表
                classification_status['classifications'][file_id - 1] = category_index
                break
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/classify/execute', methods=['POST'])
def execute_classification():
    """执行分类操作"""
    try:
        config = load_config()
        if not config:
            return jsonify({'success': False, 'message': '配置加载失败'})
        
        # 获取分类结果
        files = classification_status['files']
        classifications = classification_status['classifications']
        categories = classification_status['categories']
        
        # 解析分类路径
        category_paths = parse_category_paths(config)
        
        # 执行分类
        result = classify_files(
            files,
            classifications,
            categories,
            config['PATHS']['source_folder'],
            config['PATHS']['target_base_folder'],
            category_paths
        )
        
        # 保存文件目标路径，用于可能的撤回
        classification_status['file_target_paths'] = result.get('file_target_paths', {})
        
        return jsonify({
            'success': True,
            'message': '分类执行完成',
            'stats': {
                'success': result['success_count'],
                'failed': result['failed_count'],
                'category_stats': result['category_stats']
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/classify/cleanup', methods=['POST'])
def cleanup_files():
    """清理源文件"""
    try:
        config = load_config()
        if not config:
            return jsonify({'success': False, 'message': '配置加载失败'})
        
        # 获取分类结果
        files = classification_status['files']
        classifications = classification_status['classifications']
        categories = classification_status['categories']
        
        # 解析分类路径
        category_paths = parse_category_paths(config)
        
        # 统计删除的文件
        deleted_count = 0
        failed_to_delete_count = 0
        failed_files = []
        
        for i, (filename, category_idx) in enumerate(zip(files, classifications)):
            if i >= len(classifications):
                continue
                
            if category_idx < 0 or category_idx >= len(categories):
                continue
            
            category = categories[category_idx]
            source_path = os.path.join(config['PATHS']['source_folder'], filename)
            
            # 确定目标路径
            if category_paths and category in category_paths:
                target_folder = category_paths[category]
                if not os.path.isabs(target_folder):
                    target_folder = os.path.abspath(target_folder)
                target_path = os.path.join(target_folder, filename)
            else:
                target_path = os.path.join(config['PATHS']['target_base_folder'], category, filename)
            
            # 检查目标文件是否存在，然后删除源文件
            if os.path.exists(target_path) and os.path.exists(source_path):
                try:
                    os.remove(source_path)
                    deleted_count += 1
                except Exception as e:
                    failed_to_delete_count += 1
                    failed_files.append({'file': filename, 'error': str(e)})
        
        return jsonify({
            'success': True,
            'message': '清理完成',
            'deleted_count': deleted_count,
            'failed_count': failed_to_delete_count,
            'failed_files': failed_files
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/classify/rollback', methods=['POST'])
def rollback_files():
    """撤回分类"""
    try:
        file_target_paths = classification_status.get('file_target_paths', {})
        
        if file_target_paths:
            result = rollback_classification(file_target_paths)
            return jsonify({
                'success': True,
                'message': '撤回完成',
                'stats': result
            })
        else:
            return jsonify({'success': False, 'message': '没有可撤回的文件'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/check')
def check_api():
    """检查API连接"""
    try:
        config = load_config()
        if not config:
            return jsonify({'success': False, 'message': '配置加载失败'})
        
        # 简单的API测试
        import requests
        
        api_key = config['API'].get('api_key', '')
        base_url = config['API'].get('base_url', 'https://api.deepseek.com')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 发送一个简单的请求测试
        test_data = {
            "model": config['API'].get('model', 'deepseek-chat'),
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=test_data,
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'API连接正常'})
        else:
            return jsonify({'success': False, 'message': f'API连接失败: {response.status_code}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 静态文件路由
@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('../static', filename)