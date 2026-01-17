# Quark File Manager - 小白友好的 AI 文件管家

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-lightgrey)](https://flask.palletsprojects.com/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-API-green)](https://platform.deepseek.com/)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Quark File Manager** 是一个基于AI的智能文件分类与管理工具，通过分析文件名自动将文件分类到预设的目录结构。系统采用Web可视化界面，支持批量处理、手动调整和实时配置更新，让文件整理变得简单高效。

![演示图片](/static/img/demo_page.png)

## ✨ 核心亮点

### 智能 AI 分类
- 基于LLM API的文件智能识别
- 支持自定义分类标签和路径映射
- 自动分批处理，避免API调用限制
- 分类结果可手动调整和验证

### 现代化 Web 界面
- 响应式布局，适配各种设备
- 实时进度显示和状态监控
- 无需命令行操作，**全程可视化**

### 灵活配置管理
- 在线配置编辑，实时保存
- 支持相对路径和绝对路径模式
- 可自定义分类规则和描述
- API密钥和模型配置可视化管理

### 批量处理能力
- 自动按 30 文件分批处理
- 支持大文件集合的智能分割
- 分类结果统一预览和调整
- 一键执行和撤回操作

## 🛠️ 技术栈

- **后端框架**: Flask (Python)
- **前端技术**: HTML5, CSS3, JavaScript
- **AI引擎**: DeepSeek API / OpenAI API
- **配置文件**: INI格式 + ConfigParser
- **文件操作**: Python标准库 (os, shutil, pathlib)

## 📦 快速开始

### 环境要求
- Python 3.8 或更高版本
- DeepSeek API密钥（或OpenAI API密钥）

### 安装步骤

1. **克隆仓库**

```bash
git clone https://lsqkk.github.io/lsqkk/FileManager.git
cd FileManager
```
您也可以选择下载项目`zip`并解压。

2. **安装依赖**
```bash
pip install -r requirements.txt
```
您也可以选择直接运行`run.bat`或`run.sh`。

3. **配置API密钥**
编辑 `config.ini` 文件，填入您的API密钥。
您也可以在下一步启动服务器后在可视化页面编辑。
```ini
[API]
api_key = sk-your-deepseek-api-key-here
base_url = https://api.deepseek.com
model = deepseek-chat
```

4. **启动服务器**
```bash
python server.py
```

5. **访问应用**
打开浏览器访问：`http://localhost:5180`

## 📁 项目结构

```
FileManager/
├── server.py              # Flask服务器主入口
├── config.ini            # 配置文件
├── utils.py              # 核心工具函数
├── classify_main.py      # 命令行分类工具
├── requirements.txt      # Python依赖
├── README.md            # 项目说明
├── LICENSE              # MIT许可证
│
├── app/                 # Flask应用模块
│   ├── __init__.py
│   └── routes.py       # Web路由
│
├── templates/           # HTML模板
│   ├── base.html
│   ├── index.html      # 主页
│   ├── config.html     # 配置页面
│   └── results.html    # 结果页面
│
└── static/             # 静态资源
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## 🔧 配置说明

### 配置文件示例
```ini
[API]
api_key = your_api_key_here
base_url = https://api.deepseek.com
model = deepseek-chat

[CLASSIFICATION]
categories = 高数1,线代,资料讲义

category_paths = 
    高数1:../大一/学科/高数1
    线代:../大一/学科/线代
    ...

[PATHS]
source_folder = ./未整理
target_base_folder = ./

[SETTINGS]
api_timeout = 30
max_retries = 3
```

### 路径模式
- **相对路径模式**: 路径相对于项目根目录
- **绝对路径模式**: 完整系统路径

## 🚀 使用方法

### 1. 准备文件
将需要分类的文件放入 `source_folder` 指定的目录（默认为 `./未整理`，您也可以选择其他地址）

### 2. 配置分类规则
在Web界面的配置页面：
- 设置API密钥和端点
- 定义分类标签和描述
- 配置目标路径映射

### 3. 执行分类
1. 点击"扫描文件"查看待处理文件
2. 点击"AI分类"开始智能分类
3. 监控实时处理进度

### 4. 调整与确认
1. 在结果页面查看AI分类结果
2. 可手动调整单个文件的分类
3. 预览分类统计和文件分布

### 5. 执行与清理
1. 确认无误后执行分类操作
2. 可选择清理源文件夹已分类的文件
3. 如有需要可撤回操作

## ⚙️ 高级功能

### 批量处理优化
- 自动检测文件数量，超过30个自动分批
- 每批独立处理，避免API超时
- 处理进度实时可视化

### 错误处理与恢复
- API调用失败自动重试（可配置次数）
- 分类错误时使用默认分类
- 完整的撤回机制
- 详细的错误日志和用户反馈

### 可扩展架构
- 支持多种AI API（DeepSeek, OpenAI等）
- 模块化设计，易于添加新分类器
- 配置文件驱动，无需修改代码

## 🔌 API集成

### 支持的AI服务
1. **DeepSeek API** (默认)
   - 模型: deepseek-chat, deepseek-coder
   - 端点: https://api.deepseek.com

2. **OpenAI API**
   - 模型: gpt-4, gpt-3.5-turbo
   - 端点: https://api.openai.com/v1

### 自定义集成
通过修改 `config.ini` 的 `[API]` 部分，可切换不同的AI服务提供商。

## 📊 性能特点

- **响应速度**: 本地服务器，毫秒级响应
- **处理能力**: 支持数百个文件的批量处理
- **内存占用**: 轻量级设计，资源消耗低
- **稳定性**: 完善的错误处理和恢复机制

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目！

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 常见问题

### Q: API调用失败怎么办？
A: 检查API密钥是否正确，网络连接是否正常，或尝试增加超时时间。

### Q: 分类不准确如何调整？
A: 可在结果页面手动调整单个文件的分类，或修改分类描述帮助AI理解。

### Q: 如何处理大量文件？
A: 系统自动分批处理，每批30个文件，确保稳定性和性能。

### Q: 支持哪些文件类型？
A: 支持所有文件类型，分类基于文件名分析，不依赖文件内容。

### Q: 如何备份配置？
A: 所有配置保存在 `config.ini` 文件中，可手动备份此文件。

## 📞 支持与反馈

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 查看项目文档

---

**Quark File Manager** - 让文件整理变得智能而简单