# 🤖 ArXiv Intelligent Paper Analysis System

An AI-based intelligent analysis platform for academic papers, capable of automatically crawling ArXiv papers, generating task descriptions, intelligently classifying them, and providing visualization analysis and intelligent question-and-answer functions.

## ✨ Features

### Core Functions

- 🔍 **Crawling**:
  - **Web Mode**: Pure web crawling to obtain the latest papers (New submissions & Cross submissions)
- 📅 **Flexible Date Selection**:
  - **Single Date**: Crawl all papers for a specified date (Recommended)⭐
  - **Latest Papers**: Obtain recently submitted papers
- 👥 **Author Information**: Automatically obtain author and affiliation information
- 🤖 AI Task Description: Automatically generate paper task descriptions using LLM
- 🎯 **Intelligent Classification**: Automatically classify and cluster papers based on task descriptions
- 📊 **Data Visualization**: Interactive charts display classification results
- 💬 **Intelligent Question Answering**: An AI question answering system based on a paper database
- 📁 **Excel Export**: Export crawling and analysis results to Excel
- 🌐 **Web Interface**: A beautiful and modern web interface integrating all functions

## 🚀 Quick Start

### Environment Requirements

- Python 3.7+
- OpenAI-compatible API service (such as yunwu.ai)

- Stable network connection

### 安装依赖

```bash
# Cloning project
git clone https://github.com/GloriaSY01/Crawl-arxiv-agents-analyze.git

# Install all dependency packages
pip install -r requirements.txt

# Or install manually
pip install requests openai flask beautifulsoup4 openpyxl tqdm
```

### 🎯One-click start (recommended)

```bash
python main.py --base_url "https://xxxxx/v1" --api_key "your_api_key"
```

The system will automatically:

1. 🌐 Start the Streamlit web server (default port 8501)

2. 🚀 Automatically open your browser (if it doesn't open automatically, click the link below the terminal command line)

3. ✨ Display a modern, interactive interface

**Initial Usage Steps:**

1. Run `python main.py --base_url "https://xxx/xx" --api_key "your_api_key"`
2. Your browser will automatically open http://localhost:8501
3. Configure LLM in the sidebar:
   - Enter the model name (e.g., `gpt-4`, `gpt-5`)
   - Click the "🔗 Connect LLM" button
4. Select the crawling method:
   - **Web Scraping:** Get the latest papers
5. Select the category and click "🚀 Start Crawling"
6. Use "🤖 AI Analysis" for intelligent classification
7. Switch tabs to view results and use intelligent question answering



### 🔑 API配置

本系统使用yunwu.ai的API服务，API密钥已在代码中配置。如需使用其他服务，请修改以下文件中的配置：
- `chat.py`
- `translate.py`
- `analyzer.py`
- `streamlit_app.py`

### 📋 详细启动选项

```bash
# 使用Web界面（默认模式）
python main.py

# 自定义Web端口
python main.py --web_port 9090

# 使用已有论文文件
python main.py --chat_file your_papers.json

# 使用命令行模式（需要完整参数）
python main.py --console --translate_llm gpt-3.5-turbo --port 9000 --output papers.json

# 查看所有选项
python main.py --help
```

## 🎮 使用指南

### Web界面使用

1. **启动系统**
   ```bash
   python main.py
   ```
   浏览器会自动打开 `http://localhost:8501`

2. **爬取论文**
   - 📅 选择日期（默认为今天）
   - 📚 选择类别（cs, math, physics, stat等）
   - 🚀 点击"开始爬取"
   - ⏳ 实时进度条显示爬取进度
   - ✅ 自动获取标题、摘要、作者、单位信息

3. **AI分析与分类**
   - 🤖 点击"AI分析与分类"按钮
   - 📝 系统自动为每篇论文生成任务描述
   - 🎯 基于任务描述智能分类论文
   - ⏱️ 分析完成后自动更新界面

4. **数据可视化**
   - 📊 切换到"数据可视化"标签页
   - 📈 查看交互式柱状图展示分类结果
   - 🎨 彩色卡片显示每个类别的论文数量
   - 🖱️ 点击卡片查看该类别的详细论文列表

5. **智能问答**
   - 💬 切换到"智能问答"标签页
   - 📝 输入问题（支持中英文）
   - 🤖 AI基于已爬取的论文回答问题
   - 💡 支持多轮对话

6. **导出功能**
   - 📁 点击"导出到Excel"按钮
   - 📊 自动生成包含所有数据的Excel文件
   - 📋 分类结果以多个工作表展示
   - 💾 文件保存在`exports/`目录

### 命令行模式

对于需要批量处理的场景，可以使用命令行模式：

```bash
# 完整流程（爬取 + 翻译 + 分析 + 问答）
python main.py --console \
    --abstract-keywords "machine learning" \
    --start-date 20250101 \
    --end-date 20250112 \
    --max-results 50 \
    --output papers/ml_papers.json \
    --translate_llm "gpt-4" \
    --port 9000

# 仅分析已有数据
python analyzer.py --input papers/ml_papers.json --output results/analyzed.json

# 导出到Excel
python excel_exporter.py --input papers/ml_papers.json --output exports/papers.xlsx
```

## 📊 高级功能

### 1. 网页爬取功能

系统支持从ArXiv网页直接爬取论文：

```python
from crawl import ArxivCrawler

crawler = ArxivCrawler()

# 爬取指定类别的最新论文
# 会自动爬取 New submissions 和 Cross submissions（不爬取 Replacements）
papers = crawler.crawl_new_submissions("cs")  # Computer Science

# 支持的类别：
# cs - Computer Science
# math - Mathematics  
# physics - Physics
# q-bio - Quantitative Biology
# q-fin - Quantitative Finance
# stat - Statistics
# eess - Electrical Engineering and Systems Science
# econ - Economics

# 会自动进入每篇论文的详情页获取完整信息（标题、摘要、作者、单位）

# papers包含完整信息
for paper in papers:
    print(f"标题: {paper['title']}")
    print(f"作者: {', '.join(paper.get('authors', []))}")
    print(f"摘要: {paper.get('abstract', '')}")
    if 'author_affiliations' in paper:
        for author_info in paper['author_affiliations']:
            print(f"  {author_info['name']} - {author_info['affiliation']}")
```

### 2. AI任务描述生成

使用LLM自动生成论文任务描述：

```python
from analyzer import PaperAnalyzer

analyzer = PaperAnalyzer(model_name="gpt-4")

# 生成单篇论文的任务描述
task_desc = analyzer.generate_task_description(paper)

# 批量生成
papers = analyzer.batch_generate_task_descriptions(papers)
```

### 3. 智能分类与聚类

基于任务描述自动分类论文：

```python
# 分类论文
classified_papers = analyzer.classify_papers(papers)

# 聚类分析
clustered_papers = analyzer.cluster_papers_by_similarity(papers, num_clusters=5)

# 生成总结报告
report = analyzer.generate_summary_report(classified_papers)
```

### 4. 数据导出

支持导出为Excel格式：

```python
from excel_exporter import ExcelExporter

exporter = ExcelExporter()

# 导出基本论文数据
exporter.export_papers(papers, "output.xlsx")

# 导出分类结果（多工作表）
exporter.export_classified_papers(classified_papers, "classified.xlsx")
```

### 5. 智能问答示例

```
🔍 研究主题查询:
"这些论文主要研究什么领域？"

💡 技术对比分析:
"比较不同论文使用的深度学习方法"

📊 数据集分析:
"这些论文使用了哪些数据集？"

🎯 实验结果总结:
"总结各论文的主要实验结果"

🔬 方法创新点:
"有哪些值得关注的技术创新？"

🎓 作者机构分析:
"这些论文的作者来自哪些机构？"
```

## 🛠️ 配置选项

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--web` | `True` | 启用Web界面模式 |
| `--console` | `False` | 启用命令行模式 |
| `--web_port` | `8080` | Web服务器端口 |
| `--max_load_files` | `10` | 最大加载论文数量 |
| `--api_base` | `http://localhost:9000/v1` | API服务地址 |
| `--api_key` | `your-key-here` | API密钥 |

### 配置文件

在 `main.py` 中可以修改默认配置：

```python
# API配置
API_BASE = "http://localhost:9000/v1"
API_KEY = "your-key-here"

# 处理配置
MAX_LOAD_FILES = 10
WEB_PORT = 8080
```

## 🌐 Streamlit 界面功能

### 主要特性

- 🎨 **现代化设计**: 简洁优雅、响应式布局
- 💬 **实时交互**: 流畅的交互体验，即时反馈
- 📱 **移动端适配**: 完美支持手机和平板设备
- 📊 **交互式图表**: Plotly 驱动的数据可视化

### 界面组件

1. **侧边栏**
   - 🤖 LLM 配置
   - 📅 爬取设置
   - 🔬 数据操作（AI分析、导出Excel）
   - 📊 实时统计信息

2. **主内容区标签页**
   - 📚 **论文列表**: 搜索、浏览、查看详情
   - 📊 **数据可视化**: 交互式图表和统计
   - 💬 **智能问答**: 聊天式界面
   - ℹ️ **使用说明**: 完整帮助文档

3. **交互功能**
   - 🔍 实时搜索过滤
   - 📥 在线下载导出
   - 💬 多轮对话支持
   - 📈 动态数据更新

## 💻 Linux 服务器使用

### 无显示环境（推荐）

1. **在服务器上启动**：
   ```bash
   python main.py
   # 或直接运行
   streamlit run streamlit_app.py --server.port 8501
   ```

2. **本地端口转发**：
   ```bash
   # 在本地机器执行
   ssh -L 8501:localhost:8501 username@your_server_ip
   ```

3. **本地访问**：
   打开浏览器访问 `http://localhost:8501`

### 有显示环境

直接运行即可：
```bash
python main.py
```
Streamlit 会自动打开浏览器。

## �🔧 故障排除

### 常见问题

1. **无法访问Web界面**
   ```bash
   # 检查端口是否被占用
   netstat -an | grep 8501
   
   # 尝试其他端口
   streamlit run streamlit_app.py --server.port 9000
   ```

2. **API连接失败**
   ```bash
   # 检查API服务是否运行
   curl http://localhost:9000/v1/models
   
   # 修改API地址
   python main.py --api_base http://your-api-server:port/v1
   ```

3. **论文加载缓慢**
   ```bash
   # 减少加载论文数量
   python main.py --max_load_files 5
   ```

4. **浏览器未自动打开**
   - **Windows/macOS**: 手动访问：`http://localhost:8501`
   - **Linux服务器**: 如果是无显示环境，请在本地转发端口：
     ```bash
     # 本地机器执行端口转发
     ssh -L 8501:localhost:8501 username@server_ip
     # 然后访问 http://localhost:8501
     ```
   - **Linux桌面**: Streamlit 会自动打开默认浏览器

### 调试模式

```bash
# 启用详细日志
python main.py --console
# 然后查看控制台输出

# 测试爬虫功能
python test_crawl.py
```

## 📁 项目结构

```
Arxiv-crawler/
├── main.py              # 主程序入口
├── streamlit_app.py     # Streamlit Web界面（推荐使用）
├── chat.py              # 命令行聊天模块
├── crawl.py             # 论文爬取模块（支持API和网页爬取）
├── analyzer.py          # AI分析模块（任务描述生成、分类、聚类）
├── excel_exporter.py    # Excel导出模块
├── translate.py         # 翻译功能
├── requirements.txt     # 依赖包列表
├── run_streamlit.bat    # Windows启动脚本
├── run_streamlit.sh     # Linux/macOS启动脚本
├── papers/              # 爬取的论文数据存储目录
├── exports/             # 导出的Excel文件目录
├── README.md            # 项目说明
├── STREAMLIT_GUIDE.md   # Streamlit使用指南
└── CRAWL_CORRECTION.md  # 爬虫修正说明
```

## 📸 功能演示

### Web界面截图

1. **主界面** - 集成爬取、分析、可视化功能
2. **论文列表** - 显示爬取的论文，带任务描述标签
3. **数据可视化** - 交互式图表展示分类结果
4. **智能问答** - 基于论文库的AI对话

### 工作流程

```
1. 配置LLM → 2. 选择日期爬取论文 → 3. AI分析生成任务描述 → 
4. 智能分类论文 → 5. 查看可视化结果 → 6. 导出Excel报告 / 智能问答
```

## 🆕 更新日志

### v2.0.0 (2025-01-12)

**新增功能：**
- ✨ 支持从ArXiv网页按日期爬取论文
- ✨ 自动获取作者单位信息
- ✨ AI任务描述自动生成
- ✨ 智能分类和聚类功能
- ✨ 交互式数据可视化（Chart.js）
- ✨ Excel多工作表导出
- ✨ 增强版Web界面整合所有功能
- ✨ 实时进度条显示

**改进：**
- 🔧 优化爬虫性能和稳定性
- 🔧 改进LLM连接配置流程
- 🎨 全新现代化UI设计
- 📝 完善文档和使用说明

## 🤝 贡献指南

欢迎提交Issues和Pull Requests！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## ⚠️ 注意事项

1. **爬取频率**：请遵守ArXiv的使用政策，避免过于频繁的请求
2. **API配额**：使用LLM服务时注意API调用配额
3. **数据隐私**：爬取的论文数据仅供研究使用
4. **依赖安装**：确保安装所有必要的依赖包

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目地址: [[GloriaSY01/Crawl-arxiv-agents-analyze: 7008 homework](https://github.com/GloriaSY01/Crawl-arxiv-agents-analyze)]

---

🎉 **开始您的论文研究之旅吧！**
