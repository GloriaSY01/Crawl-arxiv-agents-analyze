# 🤖 ArXiv Intelligent Paper Analysis System

An AI-based intelligent analysis platform for academic papers, capable of automatically crawling ArXiv papers, generating task descriptions, intelligently classifying them, and providing visualization analysis and intelligent question-and-answer functions.


## ✨ Features

### Core Functions

- 🔍 **Web Scraping**: 
  - Pure web scraping from ArXiv website (not API)
  - Automatically crawls **New submissions** and **Cross submissions** from web pages
  - Supports both specific date and latest papers modes
- 📅 **Flexible Date Selection**:
  - **Single Date**: Crawl all papers for a specified date (URL: `/catchup/{category}/{date}?abs=True`) ⭐
  - **Latest Papers**: Obtain recently submitted papers (URL: `/list/{category}/new`)
- 📚 **Category Support**: 
  - Detailed categories: `cs.CV`, `cs.AI`, `cs.LG`, `cs.CL`, `cs.NE`, `cs.RO`, `math.OC`, `math.ST`
  - Simple categories: `cs`, `math`, `physics`, `q-bio`, `q-fin`, `stat`, `eess`, `econ`
- 👥 **Author Information**: Automatically extract author and affiliation information from paper detail pages
- 🤖 **AI Task Description**: Automatically generate concise task descriptions (≤25 words) using LLM
- 🎯 **Intelligent Classification**: Automatically classify papers into thematic categories based on task descriptions
- 📊 **Data Visualization**: Interactive charts (Plotly) display classification results with network graphs
- 💬 **Single Paper Deep Q&A**: AI question answering system based on full paper PDF content
- 📁 **Excel Export**: Export crawling and analysis results to Excel with multiple sheets
- 🌐 **Web Interface**: Beautiful and modern Streamlit web interface integrating all functions

## 🚀 Quick Start

### Environment Requirements

- Python 3.7+
- OpenAI-compatible API service (such as yunwu.ai)
- Stable network connection

### Install Dependencies

```bash
# Cloning project
git clone https://github.com/GloriaSY01/Crawl-arxiv-agents-analyze.git

# Install all dependency packages
pip install -r requirements.txt

# Or install manually
pip install requests openai beautifulsoup4 openpyxl tqdm streamlit plotly pandas PyPDF2 pdfplumber networkx
```

### 🎯 Quick Start

```bash
# Start with API configuration
python main.py --base_url "https://yunwu.ai/v1" --api_key "your_api_key"

# Or use run.bat on Windows (pre-configured)
run.bat
```

The system will automatically start Streamlit web server (port 8501) and open your browser.

**Usage Steps:**

1. Configure LLM in sidebar: Enter model name (e.g., `gpt-4`) and click "🔗 Connect LLM"
2. Select crawling settings: Choose date mode, category format, and click "🚀 Start Crawling"
3. Use "🤖 AI Analysis" for intelligent classification (requires LLM configured)
4. Switch tabs to view results: Data Visualization, Classification Details, Single Paper Q&A

**API Configuration:**
- **Startup Parameters**: `--base_url` and `--api_key` (Recommended)
- **Environment Variables**: `YUNWU_API_BASE` and `YUNWU_API_KEY`
- **Windows Batch File**: Pre-configured in `run.bat`

## 🎮 Usage Guide

### Web Interface

1. **Crawl Papers**: Select date mode, category format, and click "🚀 Start Crawling"
2. **AI Analysis**: Click "🤖 AI Analysis" to generate task descriptions and classify papers
3. **View Results**: Switch tabs to view Data Visualization, Classification Details, or Single Paper Q&A
4. **Export**: Click "📁 Export to Excel" to save results

### Command Line Mode

```bash
# Full pipeline
python main.py --console --base_url "https://yunwu.ai/v1" --api_key "your_key" \
    --abstract-keywords "machine learning" --start-date 20250101 --end-date 20250112 \
    --max-results 50 --output papers/ml_papers.json --translate_llm "gpt-4" --port 9000
```

## 📊 Advanced Features

### Programmatic Usage

```python
from crawl import ArxivCrawler
from analyzer import PaperAnalyzer
from excel_exporter import ExcelExporter

# Web scraping (not API)
crawler = ArxivCrawler()
papers = crawler.crawl_by_date(category="cs.CV", date="2025-09-30")
papers = crawler.crawl_new_submissions("cs")

# AI analysis
analyzer = PaperAnalyzer(model_name="gpt-4", base_url="https://yunwu.ai/v1", api_key="your_key")
papers = analyzer.batch_generate_task_descriptions(papers)
classified_papers = analyzer.classify_papers(papers)

# Export
exporter = ExcelExporter()
exporter.export_classified_papers(classified_papers, "output.xlsx")
```

## 🛠️ Configuration

**Required Parameters:**
- `--base_url`: API service base URL (e.g., `https://yunwu.ai/v1`)
- `--api_key`: API key

**Environment Variables:**
```bash
# Windows
set YUNWU_API_BASE=https://yunwu.ai/v1
set YUNWU_API_KEY=your_api_key

# Linux/macOS
export YUNWU_API_BASE=https://yunwu.ai/v1
export YUNWU_API_KEY=your_api_key
```

## 💻 Linux Server Usage

**Headless Environment:**
```bash
# On server
python main.py --base_url "https://yunwu.ai/v1" --api_key "your_api_key"

# Local port forwarding
ssh -L 8501:localhost:8501 username@your_server_ip
# Then visit http://localhost:8501
```

## �🔧 Troubleshooting

**Common Issues:**
- **Port occupied**: `streamlit run streamlit_app.py --server.port 9000`
- **API connection failed**: Check API service and verify `--base_url` and `--api_key`
- **reCAPTCHA**: Wait a few minutes, change network, or visit arxiv.org in browser
- **Browser not opening**: Manually visit `http://localhost:8501`

## 📁 Project Structure

```
Crawl-arxiv-agents-analyze--English/
├── main.py              # Main program entry (launch Streamlit or command line mode)
├── streamlit_app.py     # Streamlit Web interface (recommended)
├── chat.py              # Command line chat module (based on paper database)
├── crawl.py             # Paper crawling module (web scraping, not API)
├── analyzer.py          # AI analysis module (task description generation, classification, clustering)
├── excel_exporter.py    # Excel export module
├── paper_chat.py        # Single paper deep Q&A module (based on PDF)
├── pdf_processor.py     # PDF processing and text extraction module
├── translate.py         # Translation functionality
├── requirements.txt     # Dependency package list
├── run.bat              # Windows quick start script (pre-configured API)
├── papers/              # Crawled paper data storage directory (JSON format)
├── exports/             # Exported Excel files directory
├── cache/               # AI analysis results cache directory
├── pdfs/                # Downloaded PDF files storage directory
└── README.md            # Project documentation
```

## 🆕 Changelog
**v1.0.0 (2025-11-25)**
- ✨ Web scraping support (specific date and latest papers modes)
- ✨ AI task description generation and intelligent classification


**v2.0.0 (2025-12-02)**
- ✨ Web scraping support (specific date and latest papers modes)
- ✨ AI task description generation and intelligent classification
- ✨ Interactive data visualization (Plotly charts and NetworkX graphs)
- ✨ Single paper deep Q&A based on complete PDF content
- ✨ Enhanced Streamlit Web interface with real-time progress

## 🤝 Contributing

Welcome to submit Issues and Pull Requests! Fork the project, create a feature branch, commit changes, and create a Pull Request.

## ⚠️ Important Notes

- **Crawling Method**: Uses **web scraping**, **not ArXiv API**
- **Crawling Frequency**: Comply with ArXiv's usage policy. System has built-in request delays
- **reCAPTCHA**: May encounter verification. Wait and retry, or visit arxiv.org in browser
- **API Quota**: System caches analysis results to reduce API calls
- **PDF Storage**: Single paper Q&A downloads PDFs to `pdfs/` directory - ensure sufficient disk space

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

## 📞 Contact

- Project Repository: [GloriaSY01/Crawl-arxiv-agents-analyze](https://github.com/GloriaSY01/Crawl-arxiv-agents-analyze)
