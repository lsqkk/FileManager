#!/bin/bash
# run.sh
# 启动脚本

echo "正在启动Quark File Manager..."
echo "端口: 5180"

# 激活虚拟环境（如果使用的话）
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务器
python server.py