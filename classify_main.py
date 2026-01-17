#!/usr/bin/env python3
"""
整合的文件分类工具
功能：扫描文件 → AI分析分类 → 自动整理（基于文件名）→ 询问确认 → 清理原文件
"""

import os
import sys
import time
import configparser
from pathlib import Path
from typing import List, Dict, Tuple

# 导入工具函数
try:
    from utils import (
        load_config,
        get_files,
        call_ai_api,
        parse_ai_response,
        classify_files,
        parse_category_paths,
        rollback_classification
    )
except ImportError:
    print("错误: 请确保 utils.py 文件存在")
    sys.exit(1)


def cleanup_source_files(files: List[str], classifications: List[int], 
                        categories: List[str], source_folder: str, 
                        target_base_folder: str, 
                        category_stats: Dict[str, int],
                        category_paths: Dict[str, str] = None) -> Dict[str, any]:
    """清理源文件夹中已成功分类的文件"""
    
    deleted_count = 0
    failed_to_delete_count = 0
    failed_files = []
    
    print("\n[清理阶段] 正在清理源文件夹中的已分类文件...")
    
    for i, (filename, category_idx) in enumerate(zip(files, classifications)):
        if i >= len(classifications):
            continue
            
        if category_idx < 0 or category_idx >= len(categories):
            continue
        
        category = categories[category_idx]
        source_path = os.path.join(source_folder, filename)
        
        # 确定目标路径：优先使用自定义路径，否则使用默认路径
        if category_paths and category in category_paths:
            target_folder = category_paths[category]
            # 确保路径是相对于当前目录的绝对路径
            if not os.path.isabs(target_folder):
                target_folder = os.path.abspath(target_folder)
            target_path = os.path.join(target_folder, filename)
        else:
            target_path = os.path.join(target_base_folder, category, filename)
        
        # 检查目标文件是否已成功创建
        if os.path.exists(target_path):
            try:
                # 删除源文件
                os.remove(source_path)
                deleted_count += 1
                print(f"  ✓ 已删除: {filename}")
                
            except Exception as e:
                print(f"  ✗ 删除失败 {filename}: {e}")
                failed_to_delete_count += 1
                failed_files.append(filename)
        else:
            print(f"  ⚠ 跳过 {filename}: 目标文件不存在，可能分类失败")
    
    return {
        'deleted_count': deleted_count,
        'failed_to_delete_count': failed_to_delete_count,
        'failed_files': failed_files
    }


def main():
    """主程序"""
    print("=" * 60)
    print("文件智能分类工具（基于文件名）")
    print("=" * 60)
    
    # 1. 加载配置
    print("\n[1/4] 加载配置文件...")
    config = load_config()
    if not config:
        print("错误: 无法加载配置文件")
        sys.exit(1)
    
    # 解析分类路径映射
    category_paths = parse_category_paths(config)
    if category_paths:
        print("检测到自定义分类路径:")
        for category, path in category_paths.items():
            print(f"  {category}: {path}")
    
    # 2. 获取文件列表
    print("\n[2/4] 扫描文件...")
    source_folder = config['PATHS']['source_folder']
    files = get_files(source_folder)
    
    if not files:
        print(f"警告: 在 {source_folder} 中没有找到文件")
        sys.exit(0)
    
    print(f"找到 {len(files)} 个文件:")
    for i, file in enumerate(files, 1):
        print(f"  {i:2d}. {file}")
    
    # 3. 调用AI进行分类
    print("\n[3/4] AI智能分类中...")
    try:
        # 构建分类标签
        categories = [cat.strip() for cat in config['CLASSIFICATION']['categories'].split(',')]
        
        # 调用AI API（仅基于文件名）
        response = call_ai_api(
            files,
            categories,
            config['CLASSIFICATION'].get('category_descriptions', ''),
            config['API']
        )
        
        # 解析AI响应
        classifications = parse_ai_response(response, len(files), len(categories))
        
        if not classifications:
            print("错误: AI返回的分类结果为空")
            sys.exit(1)
        
        print(f"AI分类完成，收到 {len(classifications)} 个分类结果")
        
        # 4. 执行分类操作
        print("\n[4/4] 正在分类文件...")
        result = classify_files(
            files,
            classifications,
            categories,
            config['PATHS']['source_folder'],
            config['PATHS']['target_base_folder'],
            category_paths
        )
        
        # 显示结果统计
        print(f"\n{'='*60}")
        print("分类完成！统计信息:")
        print(f"{'='*60}")
        print(f"总文件数: {len(files)}")
        print(f"成功分类: {result['success_count']}")
        print(f"失败/跳过: {result['failed_count']}")
        
        if result['failed_files']:
            print("\n以下文件处理失败:")
            for file in result['failed_files']:
                print(f"  - {file}")
        
        # 显示分类统计和目标路径
        print(f"\n分类统计:")
        for category, count in result['category_stats'].items():
            if category_paths and category in category_paths:
                print(f"  {category}: {count} 个文件 → {category_paths[category]}")
            else:
                default_path = os.path.join(config['PATHS']['target_base_folder'], category)
                print(f"  {category}: {count} 个文件 → {default_path}")
        
        print("=" * 60)
        
        # 5. 询问用户是否满意分类结果
        print(f"\n{'='*60}")
        print("分类确认:")
        print("=" * 60)
        
        if result['success_count'] > 0:
            print(f"检测到 {result['success_count']} 个文件已成功分类")
            
            # 获取用户确认是否接受分类结果
            while True:
                print("\n请确认分类结果:")
                print("  y - 接受分类结果，继续处理")
                print("  n - 不满意分类结果，撤回分类操作")
                print("  v - 查看详细分类结果")
                
                response = input("\n您的选择 (y/n/v): ").strip().lower()
                
                if response in ['y', 'yes', '是']:
                    print("已确认分类结果，继续处理...")
                    break
                    
                elif response in ['n', 'no', '否']:
                    # 执行撤回操作
                    print("\n执行撤回操作...")
                    rollback_result = rollback_classification(result['file_target_paths'])
                    
                    print(f"\n撤回完成:")
                    print(f"  已删除文件: {rollback_result['deleted_count']}")
                    print(f"  删除失败: {rollback_result['failed_to_delete_count']}")
                    
                    if rollback_result['failed_files']:
                        print("\n以下文件删除失败:")
                        for file in rollback_result['failed_files']:
                            print(f"  - {file}")
                    
                    print("\n撤回操作完成，源文件保持不变")
                    sys.exit(0)
                    
                elif response in ['v', 'view']:
                    print("\n详细分类结果:")
                    print("-" * 40)
                    for i, (filename, category_idx) in enumerate(zip(files, classifications)):
                        if i < len(classifications):
                            category = categories[category_idx]
                            target_path = result['file_target_paths'].get(filename, "未知路径")
                            print(f"  {filename} → {category} ({os.path.dirname(target_path)})")
                    print("-" * 40)
                    continue
                    
                else:
                    print("请输入 y/n/v")
        
        # 6. 询问是否清理源文件
        print(f"\n{'='*60}")
        print("文件清理选项:")
        print("=" * 60)
        
        if result['success_count'] > 0:
            print(f"检测到 {result['success_count']} 个文件已成功分类")
            
            # 获取用户确认
            while True:
                response = input("\n是否要删除源文件夹中已分类的文件？(y/n): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    # 清理源文件
                    cleanup_result = cleanup_source_files(
                        files,
                        classifications,
                        categories,
                        config['PATHS']['source_folder'],
                        config['PATHS']['target_base_folder'],
                        result['category_stats'],
                        category_paths
                    )
                    
                    print(f"\n清理完成:")
                    print(f"  已删除文件: {cleanup_result['deleted_count']}")
                    print(f"  删除失败: {cleanup_result['failed_to_delete_count']}")
                    
                    if cleanup_result['failed_files']:
                        print("\n以下文件删除失败:")
                        for file in cleanup_result['failed_files']:
                            print(f"  - {file}")
                    break
                    
                elif response in ['n', 'no', '否']:
                    print("跳过清理，保留源文件")
                    break
                else:
                    print("请输入 y/n 或 是/否")
        else:
            print("没有成功分类的文件，跳过清理")
        
        # 最终统计
        print(f"\n{'='*60}")
        print("最终统计:")
        print("=" * 60)
        remaining_files = get_files(source_folder)
        print(f"源文件夹剩余文件数: {len(remaining_files)}")
        
        if len(remaining_files) > 0:
            print("\n剩余文件:")
            for file in remaining_files:
                print(f"  - {file}")
        
        print(f"\n所有文件已分类到相应的目标文件夹")
        if category_paths:
            print("（使用自定义分类路径映射）")
        print("=" * 60)
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(0)