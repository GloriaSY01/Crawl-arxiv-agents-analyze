#!/usr/bin/env python3
"""
ArXiv Paper Intelligent Analysis System - Streamlit Version
"""

import streamlit as st
import json
import os
import time
from datetime import datetime
from typing import List, Dict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from crawl import ArxivCrawler
    from analyzer import PaperAnalyzer
    from excel_exporter import ExcelExporter
    from paper_chat import PaperChatBot
    from pdf_processor import PDFProcessor
except ImportError as e:
    st.error(f"Module import failed: {e}")

# Page configuration
st.set_page_config(
    page_title="ArXiv Paper Intelligent Analysis System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styles
st.markdown("""
<style>
    /* Global font settings */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.8rem 0;
        margin-bottom: 0.3rem;
        line-height: 1.4;
    }
    
    /* Sub-header */
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    
    /* Sidebar titles */
    .sidebar .sidebar-content h1 {
        font-size: 1.25rem !important;
        font-weight: 600;
    }
    
    .sidebar .sidebar-content h2 {
        font-size: 1.15rem !important;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    .sidebar .sidebar-content h3 {
        font-size: 1.05rem !important;
        font-weight: 500;
    }
    
    /* Main content area title */
    .main h1 {
        font-size: 1.8rem !important;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    
    .main h2 {
        font-size: 1.5rem !important;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }
    
    .main h3 {
        font-size: 1.25rem !important;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Text */
    .main p, .main li {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #333;
    }
    
    /* Button */
    .stButton button {
        font-size: 1rem !important;
        font-weight: 500;
        padding: 0.45rem 1rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Input box style */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        font-size: 1rem !important;
        border-radius: 8px;
    }
    
    .stTextInput label, .stSelectbox label, .stTextArea label {
        font-size: 1rem !important;
        font-weight: 500;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Paper card */
    .paper-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.6rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .paper-card:hover {
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
        transform: translateY(-2px);
    }
    
    .paper-card h4 {
        font-size: 1.15rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.4rem;
        line-height: 1.4;
    }
    
    .paper-card p {
        font-size: 0.95rem;
        color: #666;
        line-height: 1.5;
        margin-bottom: 0.3rem;
    }
    
    /* Metric card */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card h3 {
        font-size: 2rem !important;
        font-weight: 700;
        margin: 0.3rem 0;
    }
    
    .metric-card p {
        font-size: 0.95rem;
        opacity: 0.9;
    }
    
    /* Tab styles */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.25rem;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    
    /* Expander (expand/collapse) area */
    .streamlit-expanderHeader {
        font-size: 1.05rem !important;
        font-weight: 500;
    }
    
    /* Success/Error/Warning/Info messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        font-size: 1rem;
        padding: 0.8rem 1rem;
        border-radius: 8px;
    }
    
    /* Dataframe styles */
    .dataframe {
        font-size: 0.95rem;
    }
    
    /* Remove excessive whitespace */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    
    /* Table styles */
    table {
        font-size: 0.95rem !important;
    }
    
    table th {
        font-weight: 600;
        background-color: #f8f9fa;
    }
    
    /* Code blocks */
    code {
        font-size: 0.95rem;
        background-color: #f5f5f5;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
    }
    
    /* Streamlit metric组件 */
    [data-testid="stMetric"] {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
    }
    
    [data-testid="stMetric"] label {
        font-size: 0.95rem !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
    }
    
    /* Sidebar styles */
    .sidebar .sidebar-content {
        padding: 1rem 1rem;
    }
    
    /* Chat message styles */
    .stChatMessage {
        font-size: 1rem;
    }
    
    /* Download button */
    .stDownloadButton button {
        font-size: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'classified_papers' not in st.session_state:
    st.session_state.classified_papers = {}
if 'crawler' not in st.session_state:
    st.session_state.crawler = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'llm_configured' not in st.session_state:
    st.session_state.llm_configured = False
if 'paper_chatbot' not in st.session_state:
    st.session_state.paper_chatbot = None
if 'current_paper_for_chat' not in st.session_state:
    st.session_state.current_paper_for_chat = None
if 'paper_chat_messages' not in st.session_state:
    st.session_state.paper_chat_messages = []

def main():
    """Main function"""
    
    # Title and top anchor
    st.markdown('<span id="top"></span><h1 class="main-header">🚀 ArXiv Paper Intelligent Analysis System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-driven paper crawling, analysis, and visualization platform</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration and Settings")
        
        # LLM Configuration
        st.subheader("🤖 LLM Configuration")
        model_name = st.text_input("Model Name", value="gpt-5", key="model_name")
        
        if st.button("🔗 Connect LLM", use_container_width=True):
            with st.spinner("Connecting..."):
                success, message = configure_llm(model_name)
                if success:
                    st.success(message)
                    st.session_state.llm_configured = True
                else:
                    st.error(message)
        
        st.divider()
        
        # Crawling Settings
        st.subheader("📅 Crawling Settings")
        
        st.info("🌐 Crawl **New submissions** and **Cross submissions** from the web")
        
        # Date selection mode
        date_mode = st.radio(
            "Date Selection",
            options=["single", "latest"],
            format_func=lambda x: {
                "single": "📅 Specific Date (as per requirements)",
                "latest": "🆕 Latest Papers"
            }[x],
            horizontal=True
        )
        
        # Category selection (supports formats like cs.CV as per requirements)
        category_type = st.radio(
            "Category Format",
            options=["detailed", "simple"],
            format_func=lambda x: {
                "detailed": "Detailed Categories (e.g., cs.CV, cs.AI)",
                "simple": "Simple Categories (e.g., cs, math)"
            }[x],
            horizontal=True
        )
        
        if category_type == "detailed":
            category = st.selectbox(
                "Select Detailed Category",
                options=["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.NE", "cs.RO", "math.OC", "math.ST"],
                help="Example: cs.CV (Computer Vision)"
            )
        else:
            category = st.selectbox(
                "Select Category",
                options=["cs", "math", "physics", "q-bio", "q-fin", "stat", "eess", "econ"],
                format_func=lambda x: {
                    "cs": "Computer Science",
                    "math": "Mathematics",
                    "physics": "Physics",
                    "q-bio": "Quantitative Biology",
                    "q-fin": "Quantitative Finance",
                    "stat": "Statistics",
                    "eess": "Electrical Engineering",
                    "econ": "Economics"
                }[x]
            )
        
        selected_date = None
        if date_mode == "single":
            # Single date selection (as per requirements)
            selected_date = st.date_input("Select Date", value=None)
            if selected_date:
                st.caption(f"💡 Papers from {selected_date} will be crawled (URL format: /catchup/{category}/{selected_date}?abs=True)")
            else:
                st.warning("⚠️ Please select a date")
        
        if st.button("🚀 Start Crawling", use_container_width=True, type="primary"):
            if date_mode == "single" and selected_date:
                crawl_papers_by_date(category, selected_date.strftime("%Y-%m-%d"))
            elif date_mode == "latest":
                crawl_papers(category)
            else:
                st.error("⚠️ Please select a date")
        
        st.divider()
        
        # Data Operations
        st.subheader("🔬 Data Operations")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤖 AI Analysis", use_container_width=True, disabled=not st.session_state.papers or not st.session_state.llm_configured):
                analyze_papers_with_cache()
        
        with col2:
            if st.button("📁 Export to Excel", use_container_width=True, disabled=not st.session_state.papers):
                export_to_excel()
        
        st.divider()
        
        # Statistics
        if st.session_state.papers:
            st.subheader("📊 Statistics")
            st.metric("Total Papers", len(st.session_state.papers))
            if st.session_state.classified_papers:
                st.metric("Classified Count", len(st.session_state.classified_papers))
    
    # Main Content Area - Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Visualization", "📋 Classification Details", "💬 Single Paper Q&A", "ℹ️ Instructions"])
    
    with tab1:
        show_visualization()
    
    with tab2:
        show_classification_details()
    
    with tab3:
        show_paper_detail_chat()
    
    with tab4:
        show_instructions()


def configure_llm(model_name: str) -> tuple:
    """Configure LLM"""
    try:
        # Check if OpenAI library is installed
        if OpenAI is None:
            return False, "❌ OpenAI library is not installed. Please run: pip install openai"
        
        # Get API configuration from environment variables
        base_url = os.getenv('YUNWU_API_BASE')
        api_key = os.getenv('YUNWU_API_KEY')
        
        if base_url is None:
            return False, "❌ Environment variable YUNWU_API_BASE is not set. Please set it using the command line argument --base_url"
        if api_key is None:
            return False, "❌ Environment variable YUNWU_API_KEY is not set. Please set it using the command line argument --api_key"
        
        # Create client
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Test connection
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                timeout=10
            )
        except Exception as conn_error:
            return False, f"❌ API connection failed: {str(conn_error)}\n\nPlease check:\n1. Network connection\n2. API key correctness\n3. Model name correctness"
        
        # Create analyzer
        st.session_state.analyzer = PaperAnalyzer(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key
        )
        st.session_state.llm_client = client
        st.session_state.llm_model = model_name
        st.session_state.llm_configured = True
        
        return True, f"✅ Successfully connected to {model_name}"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}"


def crawl_papers_by_date(category: str, date: str):
    """Crawl papers by specified date (catchup format as required)"""
    if not st.session_state.crawler:
        st.session_state.crawler = ArxivCrawler()
    
    # Create progress display area
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    time_placeholder = st.empty()
    
    # Progress callback function
    def progress_callback(current, total, arxiv_id, time_remaining):
        if total > 0:
            progress = int((current / total) * 100)
            progress_bar.progress(progress)
        status_placeholder.info(f"🔍 Crawling paper [{current}/{total}]: {arxiv_id}")
        
        # Show remaining time
        if time_remaining:
            if time_remaining < 60:
                time_str = f"{time_remaining:.0f}sec"
            elif time_remaining < 3600:
                minutes = time_remaining / 60
                time_str = f"{minutes:.1f}min"
            else:
                hours = time_remaining / 3600
                time_str = f"{hours:.1f}hour"
            time_placeholder.warning(f"⏱️ Estimated remaining time: {time_str}")
    
    try:
        status_placeholder.info(f"🔍 Crawling papers in category {category} on {date}...")
        info_placeholder.info(f"📅 URL format: /catchup/{category}/{date}?abs=True")
        progress_bar.progress(5)
        
        # Crawl using catchup format
        papers = st.session_state.crawler.crawl_by_date(category, date, progress_callback)
        
        progress_bar.progress(100)
        time_placeholder.empty()
        
        # Debug information
        print(f"\n[DEBUG] Crawl results: papers type={type(papers)}, length={len(papers) if papers else 0}")
        if papers and len(papers) > 0:
            print(f"[DEBUG] Keys of the first paper: {list(papers[0].keys()) if papers[0] else 'None'}")
        
        if papers and len(papers) > 0:
            st.session_state.papers = papers
            # Save crawl date for caching
            st.session_state.crawl_date = date
            
            # Statistics
            new_count = sum(1 for p in papers if p.get('submission_type') == 'New submission')
            cross_count = sum(1 for p in papers if p.get('submission_type') == 'Cross submission' or p.get('submission_type') == 'Cross-list')
            
            # Save to file
            try:
                # Include target date in filename for cache matching
                target_date_str = date.replace('-', '')  # Convert 2025-09-18 to 20250918
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"papers/crawled_{target_date_str}_{timestamp}.json"
                abs_filename = os.path.abspath(filename)
                
                print(f"\n[DEBUG] Preparing to save file: {abs_filename}")
                print(f"[DEBUG] Current working directory: {os.getcwd()}")
                print(f"[DEBUG] Target date: {date}, Category: {category}")
                
                # Ensure directory exists
                os.makedirs('papers', exist_ok=True)
                print(f"[DEBUG] papers directory created/existed")
                
                # Save file with metadata (new format)
                print(f"[DEBUG] Starting to write JSON file with {len(papers)} papers...")
                save_data = {
                    'metadata': {
                        'target_date': date,  # The date user requested to crawl
                        'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'category': category,
                        'total_papers': len(papers),
                        'new_submissions': new_count,
                        'cross_submissions': cross_count
                    },
                    'papers': papers
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] JSON file write completed")
                
                # Verify if file was created successfully
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"[DEBUG] File verification successful, size: {file_size} bytes ({file_size / 1024:.2f} KB)")
                    status_placeholder.success(f"✅ Successfully crawled {len(papers)} papers!")
                    info_placeholder.success(
                        f"📊 New submissions: {new_count} papers\n"
                        f"📊 Cross submissions: {cross_count} papers\n"
                        f"💾 Saved to: {filename}\n"
                        f"📦 File size: {file_size / 1024:.2f} KB\n"
                        f"📍 Full path: {abs_filename}"
                    )
                else:
                    status_placeholder.warning(f"⚠️ Successfully crawled but failed to save file")
                    info_placeholder.error(f"File path: {os.path.abspath(filename)}")
                    
            except Exception as save_error:
                status_placeholder.warning(f"⚠️ Successfully crawled but error occurred while saving file")
                info_placeholder.error(f"Save error: {str(save_error)}\n\nFile path: {os.path.abspath(filename) if 'filename' in locals() else 'N/A'}")
                import traceback
                st.error(f"Detailed error:\n```\n{traceback.format_exc()}\n```")
            
            time.sleep(3)
            status_placeholder.empty()
            info_placeholder.empty()
            st.rerun()
        else:
            status_placeholder.error("❌ No papers found or encountered reCAPTCHA")
            info_placeholder.warning("💡 Suggestions:\n1. Wait a few minutes and try again\n2. Check if the date and category are correct\n3. Check terminal output for more information")
            
    except Exception as e:
        status_placeholder.error(f"❌ Crawl failed: {str(e)}")
        import traceback
        info_placeholder.error(f"```\n{traceback.format_exc()}\n```")
    finally:
        progress_bar.empty()
        time_placeholder.empty()


def crawl_papers(category: str):
    """Crawl papers"""
    if not st.session_state.crawler:
        st.session_state.crawler = ArxivCrawler()
    
    # Create progress display area
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    time_placeholder = st.empty()
    
    # Progress callback function
    def progress_callback(current, total, arxiv_id, time_remaining):
        progress = int((current / total) * 100)
        progress_bar.progress(progress)
        status_placeholder.info(f"🔍 Crawling papers [{current}/{total}]: {arxiv_id}")
        
        # Show remaining time
        if time_remaining:
            if time_remaining < 60:
                time_str = f"{time_remaining:.0f}sec"
            elif time_remaining < 3600:
                minutes = time_remaining / 60
                time_str = f"{minutes:.1f}min"
            else:
                hours = time_remaining / 3600
                time_str = f"{hours:.1f}hour"
            time_placeholder.warning(f"⏱️ Estimated remaining time: {time_str}")
    
    try:
        status_placeholder.info(f"🔍 Crawling latest papers in category {category}...")
        progress_bar.progress(5)
        
        # Crawling papers (with progress callback)
        papers = st.session_state.crawler.crawl_new_submissions(category, progress_callback)
        
        progress_bar.progress(100)
        time_placeholder.empty()
        
        # Debug information
        print(f"\n[DEBUG] Crawl results: papers type={type(papers)}, length={len(papers) if papers else 0}")
        if papers and len(papers) > 0:
            print(f"[DEBUG] Keys of the first paper: {list(papers[0].keys()) if papers[0] else 'None'}")
        
        if papers and len(papers) > 0:
            st.session_state.papers = papers
            # Save current date for caching
            current_date = datetime.now().strftime("%Y-%m-%d")
            st.session_state.crawl_date = current_date
            
            # Save to file
            try:
                current_date_str = datetime.now().strftime("%Y%m%d")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"papers/crawled_{current_date_str}_{timestamp}.json"
                abs_filename = os.path.abspath(filename)
                
                print(f"\n[DEBUG] Preparing to save file: {abs_filename}")
                print(f"[DEBUG] Current working directory: {os.getcwd()}")
                
                # Ensure directory exists
                os.makedirs('papers', exist_ok=True)
                print(f"[DEBUG] 'papers' directory created/existed")
                
                # Save file with metadata (new format)
                print(f"[DEBUG] Starting to write JSON file with {len(papers)} papers...")
                save_data = {
                    'metadata': {
                        'target_date': current_date,  # For new submissions, target date is today
                        'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'category': category,
                        'total_papers': len(papers),
                        'crawl_type': 'new_submissions'
                    },
                    'papers': papers
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] JSON file write completed")
                
                # Verify if file was created successfully
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"[DEBUG] File verification successful, size: {file_size} bytes ({file_size / 1024:.2f} KB)")
                    status_placeholder.success(f"✅ Successfully crawled {len(papers)} papers!")
                    info_placeholder.success(
                        f"💾 Saved to: {filename}\n"
                        f"📦 File size: {file_size / 1024:.2f} KB\n"
                        f"📍 Full path: {abs_filename}"
                    )
                else:
                    status_placeholder.warning(f"⚠️ Successfully crawled but failed to save file")
                    info_placeholder.error(f"File path: {os.path.abspath(filename)}")
                    
            except Exception as save_error:
                status_placeholder.warning(f"⚠️ Successfully crawled but error occurred while saving file")
                info_placeholder.error(f"Save error: {str(save_error)}\n\nFile path: {os.path.abspath(filename) if 'filename' in locals() else 'N/A'}")
                import traceback
                st.error(f"Detailed error:\n```\n{traceback.format_exc()}\n```")
            
            time.sleep(3)
            status_placeholder.empty()
            info_placeholder.empty()
            st.rerun()
        else:
            status_placeholder.error("❌ No papers found")
            info_placeholder.warning("💡 Suggestions:\n1. Check if the category is correct\n2. Check terminal output for more information")
            
    except Exception as e:
        status_placeholder.error(f"❌ Crawling failed: {str(e)}")
    finally:
        progress_bar.empty()
        time_placeholder.empty()


def analyze_papers():
    """Analyze papers"""
    if not st.session_state.papers:
        st.warning("Please crawl papers first")
        return
    
    if not st.session_state.analyzer:
        st.warning("Please configure LLM first")
        return
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    
    # Progress callback function
    def progress_callback(current, total, paper_title):
        progress = int((current / total) * 50)  # First 50% for generating task descriptions
        progress_bar.progress(progress)
        status_placeholder.info(f"🤖 Generating task descriptions [{current}/{total}]")
        info_placeholder.info(f"📄 Currently processing: {paper_title}")
    
    try:
        total_papers = len(st.session_state.papers)
        status_placeholder.info(f"🤖 Starting to generate task descriptions for {total_papers} papers...")
        info_placeholder.info("⏳ Please wait, this may take a few minutes...")
        progress_bar.progress(5)
        
        print(f"\n[DEBUG] Starting analysis of {total_papers} papers")
        print(f"[DEBUG] Using model: {st.session_state.analyzer.model_name}")
        
        # Generate task descriptions (with progress callback)
        st.session_state.papers = st.session_state.analyzer.batch_generate_task_descriptions(
            st.session_state.papers, 
            show_progress=True,
            progress_callback=progress_callback
        )
        
        progress_bar.progress(60)
        status_placeholder.info("🎯 Performing intelligent classification...")
        info_placeholder.info("📊 Clustering based on task descriptions...")
        
        # Classification
        st.session_state.classified_papers = st.session_state.analyzer.classify_papers(
            st.session_state.papers
        )
        
        progress_bar.progress(100)
        status_placeholder.success(f"✅ Analysis completed! {len(st.session_state.classified_papers)} categories in total")
        info_placeholder.success(f"📊 Task descriptions generated and classification completed for {total_papers} papers")
        time.sleep(2)
        status_placeholder.empty()
        info_placeholder.empty()
        st.rerun()
        
    except Exception as e:
        status_placeholder.error(f"❌ Analysis failed: {str(e)}")
        info_placeholder.error(f"Please check terminal output for detailed error information")
        import traceback
        print(f"\n[ERROR] Analysis failed: {e}")
        traceback.print_exc()
    finally:
        progress_bar.empty()


def analyze_papers_with_cache():
    """AI analysis with caching"""
    if not st.session_state.papers:
        st.warning("Please crawl papers first")
        return
    
    if not st.session_state.analyzer:
        st.warning("Please configure LLM first")
        return
    
    # Create cache directory
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Generate cache filename (based on crawl date)
    crawl_date = st.session_state.get('crawl_date', datetime.now().strftime("%Y-%m-%d"))
    cache_file = os.path.join(cache_dir, f"analysis_{crawl_date}.json")
    
    status_placeholder = st.empty()
    
    # Check if the cache exists
    if os.path.exists(cache_file):
        try:
            status_placeholder.info(f"🔍 Found cache file: {crawl_date}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Validate cache data
            if 'papers' in cache_data and 'classified_papers' in cache_data:
                # Check if the number of papers matches
                cached_count = len(cache_data['papers'])
                current_count = len(st.session_state.papers)
                
                if cached_count == current_count:
                    # Load cache
                    st.session_state.papers = cache_data['papers']
                    st.session_state.classified_papers = cache_data['classified_papers']
                    status_placeholder.success(f"✅ Loaded cached analysis results! ({cached_count} papers, {len(cache_data['classified_papers'])} categories)")
                    time.sleep(1.5)
                    status_placeholder.empty()
                    st.rerun()
                    return
                else:
                    status_placeholder.warning(f"⚠️ Cached data mismatch (Cache: {cached_count} papers vs Current: {current_count} papers), reanalyzing...")
                    time.sleep(1)
            else:
                status_placeholder.warning("⚠️ Cache file format incorrect, reanalyzing...")
                time.sleep(1)
        except Exception as e:
            status_placeholder.warning(f"⚠️ Cache loading failed: {str(e)}, reanalyzing...")
            time.sleep(1)
    
    # No cache or invalid cache, perform analysis
    status_placeholder.info("🚀 Starting AI analysis...")
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    
    # Progress callback function
    def progress_callback(current, total, paper_title):
        progress = int((current / total) * 50)
        progress_bar.progress(progress)
        status_placeholder.info(f"🤖 Generating task descriptions [{current}/{total}]")
        info_placeholder.info(f"📄 Processing: {paper_title}")
    
    try:
        total_papers = len(st.session_state.papers)
        print(f"\n[DEBUG] Starting analysis of {total_papers} papers")
        
        # Generate task descriptions
        st.session_state.papers = st.session_state.analyzer.batch_generate_task_descriptions(
            st.session_state.papers, 
            show_progress=True,
            progress_callback=progress_callback
        )
        
        progress_bar.progress(60)
        status_placeholder.info("🎯 Performing intelligent classification...")
        info_placeholder.info("📊 Clustering based on task descriptions...")
        
        # Classification
        st.session_state.classified_papers = st.session_state.analyzer.classify_papers(
            st.session_state.papers
        )
        
        # Save to cache
        try:
            cache_data = {
                'papers': st.session_state.papers,
                'classified_papers': st.session_state.classified_papers,
                'crawl_date': crawl_date,
                'analysis_time': datetime.now().isoformat(),
                'model': st.session_state.analyzer.model_name
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Analysis results cached to: {cache_file}")
        except Exception as e:
            print(f"[WARNING] Failed to save cache: {e}")
        
        progress_bar.progress(100)
        status_placeholder.success(f"✅ Analysis complete! {len(st.session_state.classified_papers)} categories")
        info_placeholder.success(f"📊 Generated task descriptions and completed classification for {total_papers} papers")
        time.sleep(2)
        status_placeholder.empty()
        info_placeholder.empty()
        st.rerun()
        
    except Exception as e:
        status_placeholder.error(f"❌ Analysis failed: {str(e)}")
        info_placeholder.error(f"Please check the terminal output for detailed error information")
        import traceback
        print(f"\n[ERROR] Analysis failed: {e}")
        traceback.print_exc()
    finally:
        progress_bar.empty()



def export_to_excel():
    """Export to Excel"""
    try:
        exporter = ExcelExporter()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        os.makedirs('exports', exist_ok=True)
        
        if st.session_state.classified_papers:
            filename = f"exports/classified_{timestamp}.xlsx"
            exporter.export_classified_papers(st.session_state.classified_papers, filename)
        else:
            filename = f"exports/papers_{timestamp}.xlsx"
            exporter.export_papers(st.session_state.papers, filename)
        
        st.success(f"✅ Export successful!")
        st.info(f"💾 File saved at: {filename}")
        
        # Provide download button
        with open(filename, 'rb') as f:
            st.download_button(
                label="📥 Download Excel file",
                data=f,
                file_name=os.path.basename(filename),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")


def create_interactive_network_graph(classified_papers: Dict[str, List[Dict]]):
    """
    Create an interactive network graph to display paper classification/clustering results
    
    Args:
        classified_papers: Dictionary of classified papers {category: [list of papers]}
    
    Returns:
        Plotly figure object
    """
    if not HAS_NETWORKX:
        print("[ERROR] networkx library is not installed")
        return None
    
    if not classified_papers:
        print("[ERROR] classified_papers is empty")
        return None
    
    try:
        # Validate data
        total_papers = sum(len(papers) for papers in classified_papers.values())
        if total_papers == 0:
            print("[ERROR] No paper data")
            return None
        
        print(f"[DEBUG] Starting to create network graph: {len(classified_papers)} categories, {total_papers} papers")
        
        # Create network graph
        G = nx.Graph()
        
        # Clean and fresh color palette
        color_palette = [
            '#FF6B6B',  # Coral Red
            '#4ECDC4',  # Cyan
            '#45B7D1',  # Sky Blue
            '#FFA07A',  # Light Orange
            '#98D8C8',  # Mint Green
            '#F7DC6F',  # Lemon Yellow
            '#BB8FCE',  # Light Purple
            '#85C1E2',  # Light Blue
            '#F8B739',  # Golden Yellow
            '#52B788',  # Forest Green
            '#E63946',  # Deep Red
            '#457B9D',  # Steel Blue
        ]
        
        num_categories = len(classified_papers)
        # If the number of categories exceeds the preset colors, loop through
        colors = [color_palette[i % len(color_palette)] for i in range(num_categories)]
        category_colors = {cat: colors[i] for i, cat in enumerate(classified_papers.keys())}
        
        # Add nodes and edges
        node_info = {}  # Store node information for hover
        node_hover_texts = {}  # Store hover text for each node
        node_urls = {}  # Store node URLs (for clicks)
        
        node_list = []  # Store all node IDs in order
        category_paper_ids = {}  # Store paper IDs for each category, used for layout
        
        # Create central nodes for each category
        category_nodes = {}
        for category, papers in classified_papers.items():
            # Category central node
            cat_node_id = f"CAT_{category}"
            G.add_node(cat_node_id)
            node_list.append(cat_node_id)
            category_nodes[category] = cat_node_id
            node_info[cat_node_id] = {
                'type': 'category',
                'name': category,
                'count': len(papers)
            }
            node_hover_texts[cat_node_id] = f"<b>{category}</b><br>Number of papers: {len(papers)}"
            
            # Initialize the list of paper IDs for this category
            category_paper_ids[category] = []
            
            # Create nodes for each paper and connect to the category node
            for paper_idx, paper in enumerate(papers):
                # Ensure each paper has a unique ID
                paper_id = paper.get('arxiv_id', '')
                if not paper_id or paper_id in G.nodes():
                    # If arxiv_id is empty or already exists, use a fallback ID
                    paper_id = f"PAPER_{category}_{paper_idx}_{len(node_list)}"
                
                if paper_id not in G.nodes():
                    G.add_node(paper_id)
                    node_list.append(paper_id)
                    category_paper_ids[category].append(paper_id)  # Record that this paper belongs to this category
                    # Connect to the category node
                    G.add_edge(cat_node_id, paper_id)
                    
                    # Store paper information
                    title = paper.get('title', 'N/A')
                    title_short = title[:50] + ('...' if len(title) > 50 else '')
                    authors = ', '.join(paper.get('authors', [])[:3])
                    if len(paper.get('authors', [])) > 3:
                        authors += f" etc. {len(paper.get('authors', []))} authors"
                    
                    task_desc = paper.get('task_description', 'N/A')
                    
                    node_info[paper_id] = {
                        'type': 'paper',
                        'title': title,
                        'authors': authors,
                        'task_description': task_desc,
                        'category': category
                    }
                    
                    # Hover text
                    hover_text = f"<b>{title_short}</b><br>"
                    hover_text += f"Authors: {authors}<br>"
                    if task_desc and task_desc != 'N/A':
                        task_short = task_desc[:60] + ('...' if len(task_desc) > 60 else '')
                        hover_text += f"Task: {task_short}"
                    node_hover_texts[paper_id] = hover_text
                    
                    # Store URL
                    arxiv_url = paper.get('arxiv_url') or paper.get('page_url', '')
                    if arxiv_url:
                        node_urls[paper_id] = arxiv_url
        
        # Check number of nodes
        if len(G.nodes()) == 0:
            print("[ERROR] Network graph has no nodes")
            return None
        
        print(f"[DEBUG] Number of nodes in network graph: {len(G.nodes())}, number of edges: {len(G.edges())}")
        
        # Use improved force-directed layout - balance clustering and overlap prevention
        try:
            # Use spring_layout with adjusted parameters to avoid overlap
            pos = nx.spring_layout(
                G, 
                k=1.0 / (len(G.nodes()) ** 0.3),  # Adaptive k value based on number of nodes to avoid overlap
                iterations=150,  # More iterations for stability
                seed=42,
                scale=20  # Larger overall scale
            )
            print(f"[DEBUG] Force-directed layout completed, positioned {len(pos)} nodes")
            
            # Post-processing: detect and adjust overlapping nodes
            import math
            min_distance = 0.8  # Minimum distance between nodes
            
            node_positions = list(pos.items())
            for i in range(len(node_positions)):
                for j in range(i + 1, len(node_positions)):
                    node1, pos1 = node_positions[i]
                    node2, pos2 = node_positions[j]
                    
                    # Calculate distance between two nodes
                    dx = pos1[0] - pos2[0]
                    dy = pos1[1] - pos2[1]
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    # If too close, push them apart
                    if dist < min_distance and dist > 0:
                        # Calculate direction and distance to push
                        push_dist = (min_distance - dist) / 2
                        angle = math.atan2(dy, dx)
                        
                        # Update positions
                        pos[node1] = (
                            pos1[0] + push_dist * math.cos(angle),
                            pos1[1] + push_dist * math.sin(angle)
                        )
                        pos[node2] = (
                            pos2[0] - push_dist * math.cos(angle),
                            pos2[1] - push_dist * math.sin(angle)
                        )
            
            print(f"[DEBUG] Overlap prevention completed")
            
        except Exception as layout_error:
            print(f"[ERROR] Force-directed layout failed: {layout_error}, using custom layout")
            
            # Fallback: custom dispersed layout
            import math
            import random
            random.seed(42)
            pos = {}
            
            num_categories = len(classified_papers)
            used_positions = set()
            
            for cat_idx, category in enumerate(classified_papers.keys()):
                # Find a non-overlapping position for the category center
                max_attempts = 100
                for attempt in range(max_attempts):
                    # Randomly disperse category centers - increase distribution range
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(8, 20)  # Increased from 5-15 to 8-20
                    cat_x = radius * math.cos(angle)
                    cat_y = radius * math.sin(angle)
                    
                    # Check if the distance to other category centers is sufficient
                    too_close = False
                    for other_pos in used_positions:
                        dist = math.sqrt((cat_x - other_pos[0])**2 + (cat_y - other_pos[1])**2)
                        if dist < 12:  # Further increase the minimum distance to avoid overlapping of category clusters
                            too_close = True
                            break
                    
                    if not too_close or attempt == max_attempts - 1:
                        used_positions.add((cat_x, cat_y))
                        break
                
                cat_node_id = f"CAT_{category}"
                pos[cat_node_id] = (cat_x, cat_y)
                
                # Get all paper node IDs for this category
                paper_ids = category_paper_ids.get(category, [])
                num_papers = len(paper_ids)
                
                if num_papers == 0:
                    continue
                
                # Adjust distribution radius based on the number of papers - increase radius to avoid overlap
                if num_papers <= 5:
                    radius_papers = 1.5
                elif num_papers <= 10:
                    radius_papers = 2.0
                elif num_papers <= 20:
                    radius_papers = 2.8
                else:
                    radius_papers = 3.5
                
                # Distribute the thesis nodes around the category centers to ensure no overlap.
                for paper_idx, paper_id in enumerate(paper_ids):
                    if num_papers == 1:
                        paper_angle = math.pi / 4
                        paper_radius = 1.2  # Maintain a certain distance
                    elif num_papers <= 6:
                        # Few papers, single layer distribution
                        paper_angle = 2 * math.pi * paper_idx / num_papers
                        paper_radius = radius_papers
                    elif num_papers <= 12:
                        # Medium number of papers, single layer but increased radius
                        paper_angle = 2 * math.pi * paper_idx / num_papers
                        paper_radius = radius_papers * 1.2
                    else:
                        # Many papers, multi-layer spiral distribution
                        layer = paper_idx // 6  # Every 6 papers form a layer
                        angle_offset = (layer % 2) * (math.pi / 6)  # Offset angle
                        paper_angle = 2 * math.pi * (paper_idx % 6) / 6 + angle_offset
                        paper_radius = radius_papers + layer * 1.0  # Increase layer spacing
                    
                    paper_x = cat_x + paper_radius * math.cos(paper_angle)
                    paper_y = cat_y + paper_radius * math.sin(paper_angle)
                    pos[paper_id] = (paper_x, paper_y)
            
            print(f"[DEBUG] Custom dispersed layout completed, positioned {len(pos)} nodes")
        
        # After determining the layout, further increase the distance between paper nodes and category center nodes
        # This allows each category's "petals" to be more spread out, avoiding paper nodes crowding near category nodes
        try:
            distance_scale = 2.0  # Distance scaling factor, adjustable as needed (>1 means farther)
            for node_id, info in node_info.items():
                if info.get('type') != 'paper':
                    continue
                
                cat = info.get('category')
                if not cat:
                    continue
                
                cat_node_id = category_nodes.get(cat)
                if not cat_node_id:
                    continue
                
                if node_id not in pos or cat_node_id not in pos:
                    continue
                
                cx, cy = pos[cat_node_id]
                px, py = pos[node_id]
                
                dx = px - cx
                dy = py - cy
                
                # If they coincide exactly, give a small offset to avoid division by zero or zero direction
                if dx == 0 and dy == 0:
                    dx, dy = 0.1, 0.1
                
                pos[node_id] = (cx + dx * distance_scale, cy + dy * distance_scale)
            
            print(f"[DEBUG] Increased distance between paper nodes and category nodes, scale={distance_scale}")
        except Exception as adjust_error:
            print(f"[WARN] Failed to adjust paper node distances: {adjust_error}")
        
        # Extract edge coordinates - using gradient colors and finer styles
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create edge traces - finer lines suitable for dense layouts
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(
                width=0.5,  # Reduced line width for cleaner look
                color='rgba(180, 180, 180, 0.3)'  # Lighter color
            ),
            hoverinfo='none',
            mode='lines'
        )
        
        # Extract node coordinates and texts (in the order of node_list)
        node_x = []
        node_y = []
        node_labels = []
        hover_texts_ordered = []
        node_sizes_ordered = []
        node_colors_ordered = []
        
        for node in node_list:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node labels (only show category names, shortened to avoid overlap)
            if node_info.get(node, {}).get('type') == 'category':
                label = node_info[node].get('name', '')
                # Truncate overly long labels
                if len(label) > 15:
                    label = label[:13] + '..'
                node_labels.append(label)
            else:
                node_labels.append('')
            
            # Hover texts
            hover_texts_ordered.append(node_hover_texts.get(node, ''))
            
            # Node sizes and colors - reduced sizes to avoid overlap
            if node.startswith('CAT_'):
                # Category center nodes - moderate size
                cat_name = node.replace('CAT_', '')
                node_sizes_ordered.append(25)  # Reduced from 35 to 25
                node_colors_ordered.append(category_colors.get(cat_name, colors[0]))
            else:
                # Paper nodes - smaller dots to avoid overlap
                node_sizes_ordered.append(6)  # Reduced from 8 to 6
                paper_category = node_info.get(node, {}).get('category', '')
                node_colors_ordered.append(category_colors.get(paper_category, colors[0]))
        
        # Separate category nodes and paper nodes traces to avoid label overlap
        # Category nodes (with labels)
        cat_x, cat_y, cat_labels, cat_hover, cat_sizes, cat_colors = [], [], [], [], [], []
        # Paper nodes (without labels)
        paper_x, paper_y, paper_hover, paper_sizes, paper_colors = [], [], [], [], []
        
        for idx, node in enumerate(node_list):
            x, y = node_x[idx], node_y[idx]
            if node.startswith('CAT_'):
                cat_x.append(x)
                cat_y.append(y)
                cat_labels.append(node_labels[idx])
                cat_hover.append(hover_texts_ordered[idx])
                cat_sizes.append(node_sizes_ordered[idx])
                cat_colors.append(node_colors_ordered[idx])
            else:
                paper_x.append(x)
                paper_y.append(y)
                paper_hover.append(hover_texts_ordered[idx])
                paper_sizes.append(node_sizes_ordered[idx])
                paper_colors.append(node_colors_ordered[idx])
        
        # Category center nodes trace (with labels, labels positioned above to avoid overlap)
        cat_trace = go.Scatter(
            x=cat_x, y=cat_y,
            mode='markers+text',
            hoverinfo='text',
            text=cat_labels,
            textposition="top center",  # Labels positioned above nodes
            textfont=dict(
                size=10,  # Smaller font to avoid overlap
                color='#2c3e50',
                family='Arial, sans-serif',
                weight='bold'
            ),
            hovertext=cat_hover,
            marker=dict(
                size=cat_sizes,
                color=cat_colors,
                line=dict(width=2, color='white'),
                opacity=0.95
            ),
            cliponaxis=False,  # Allow labels to extend beyond the plot area
            name='Category Centers'
        )
        
        # Paper nodes trace (without labels)
        paper_trace = go.Scatter(
            x=paper_x, y=paper_y,
            mode='markers',
            hoverinfo='text',
            hovertext=paper_hover,
            marker=dict(
                size=paper_sizes,
                color=paper_colors,
                line=dict(width=1, color='white'),
                opacity=0.9
            ),
            name='Papers'
        )
        
        # Display legend on the right
        legend_annotations = []
        legend_y_start = 0.98
        legend_spacing = 0.04  # Adjust spacing dynamically based on number of categories
        
        # Reduce spacing if there are many categories
        if num_categories > 15:
            legend_spacing = 0.03
        elif num_categories > 20:
            legend_spacing = 0.025
        
        for idx, (category, color) in enumerate(category_colors.items()):
            paper_count = len(classified_papers[category])
            y_position = legend_y_start - idx * legend_spacing
            
            # Only show legend items within the visible range
            if y_position > 0:
                legend_annotations.append(
                    dict(
                        text=f"● {category} ({paper_count})",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=1.01, y=y_position,
                        xanchor="left", yanchor="top",
                        font=dict(size=9, color=color),
                        bgcolor='rgba(255, 255, 255, 0.85)',
                        borderpad=2
                    )
                )
        
        right_margin = 200
        
        # Create figure (edges at the bottom layer, paper nodes in the middle, category nodes and labels at the top layer)
        fig = go.Figure(
            data=[edge_trace, paper_trace, cat_trace],
            layout=go.Layout(
                title=dict(
                    text='Paper Classification Network',
                    font=dict(size=18, color='#2c3e50'),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=40, l=40, r=right_margin, t=80),  # Increase bottom, left, and right margins to prevent label clipping
                annotations=[
                    dict(
                        text="💡 Tip: Nodes of the same color belong to the same category | Papers of the same category automatically cluster | Hover to see details",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=-0.03,
                        xanchor="center", yanchor="top",
                        font=dict(size=10, color="#7f8c8d")
                    )
                ] + legend_annotations,
                xaxis=dict(
                    showgrid=False, 
                    zeroline=False, 
                    showticklabels=False
                ),
                yaxis=dict(
                    showgrid=False, 
                    zeroline=False, 
                    showticklabels=False
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=850,  # Increase height to accommodate labels and content
                autosize=True,  # Automatically adjust size
                uniformtext=dict(
                    mode='hide',  # Hide text that doesn't fit instead of scaling
                    minsize=8  # Minimum font size
                )
            )
        )
        
        # Add click event handling (via custom JavaScript)
        # Note: Plotly click events in Streamlit need to be handled differently
        # Here we use hover information to prompt users to click
        
        return fig
        
    except Exception as e:
        error_msg = f"Failed to create network graph: {e}"
        print(f"[ERROR] {error_msg}")
        import traceback
        print("[ERROR] Detailed error information:")
        traceback.print_exc()
        # Note: st.error cannot be used here as it may not be in Streamlit context
        return None


def show_visualization():
    """Display data visualization"""
    st.header("📊 Data Visualization")
    
    if not st.session_state.papers:
        st.info("No data available, please crawl papers first")
        return
    
    # Basic statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Total Papers", len(st.session_state.papers))
    
    with col2:
        new_count = sum(1 for p in st.session_state.papers if p.get('submission_type') == 'New submission')
        st.metric("🆕 New Submissions", new_count)
    
    with col3:
        cross_count = sum(1 for p in st.session_state.papers if p.get('submission_type') == 'Cross-list')
        st.metric("🔀 Cross-lists", cross_count)
    
    st.divider()
    
    # Classification visualization
    if st.session_state.classified_papers:
        # Visualization mode selection
        viz_mode = st.radio(
            "Select Visualization Mode",
            ["📊 Interactive Network Graph", "📈 Statistical Charts"],
            horizontal=True,
            key="viz_mode"
        )
        
        if viz_mode == "📊 Interactive Network Graph":
            st.subheader("📊 Paper Classification Interactive Network Graph")
            st.caption("💡 Tip: The force-directed algorithm automatically clusters similar papers together, with a legend displayed on the right.")
            
            if HAS_NETWORKX:
                # Check data
                if not st.session_state.classified_papers:
                    st.warning("No classification data available, please perform AI analysis first")
                else:
                    # Debug information
                    total_papers = sum(len(papers) for papers in st.session_state.classified_papers.values())
                    st.caption(f"📊 Total {len(st.session_state.classified_papers)} categories, {total_papers} papers")
                    
                    # Create interactive network graph
                    with st.spinner("Generating network graph..."):
                        network_fig = create_interactive_network_graph(st.session_state.classified_papers)
                    
                    if network_fig:
                        # Configure chart display options
                        config = {
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                            'scrollZoom': True
                        }
                        st.plotly_chart(network_fig, use_container_width=True, config=config)
                    else:
                        st.warning("⚠️ Unable to create network graph")
                        st.info("💡 Possible reasons:\n1. Incorrect data format\n2. Too many nodes in the network graph\n3. networkx library not properly installed\n4. Check detailed error information in the terminal output")
                        st.code("Please check the [ERROR] and [DEBUG] messages in the terminal output", language='text')
            else:
                st.warning("⚠️ The networkx library is required to display the network graph. Run: pip install networkx")
                st.info("Displaying statistical charts as an alternative...")
                viz_mode = "📈 Statistical Charts"
        
        if viz_mode == "📈 Statistical Charts":
            st.subheader("📊 Paper Classification Distribution")
            
            # Prepare data
            categories = list(st.session_state.classified_papers.keys())
            counts = [len(papers) for papers in st.session_state.classified_papers.values()]
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=counts,
                    marker_color='rgb(102, 126, 234)',
                    text=counts,
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Number of Papers by Category",
                xaxis_title="Category",
                yaxis_title="Number of Papers",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📌 Please perform AI analysis first to view classification results")
        
        # Display submission type distribution
        st.subheader("📊 Submission Type Distribution")
        
        submission_types = {}
        for paper in st.session_state.papers:
            stype = paper.get('submission_type', 'Unknown')
            submission_types[stype] = submission_types.get(stype, 0) + 1
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(submission_types.keys()),
                values=list(submission_types.values()),
                hole=0.3
            )
        ])
        
        fig.update_layout(
            title="Submission Type Distribution",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_classification_details():
    """Show classification details"""
    st.header("📋 Classification Details")
    
    if not st.session_state.papers:
        st.info("No data available, please crawl papers first")
        return
    
    if not st.session_state.classified_papers:
        st.info("📌 Please perform AI analysis first to view classification results")
        return
    
    # Statistics
    total_papers = sum(len(papers) for papers in st.session_state.classified_papers.values())
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Number of Categories", len(st.session_state.classified_papers))
    with col2:
        st.metric("📄 Total Papers", total_papers)
    
    # Add CSS to reduce spacing after statistics
    st.markdown("""
    <style>
    /* Reduce spacing after statistics */
    [data-testid="stMetric"] {
        margin-bottom: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        margin-bottom: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add global CSS for fixed navigation bar
    st.markdown("""
    <style>
    /* Fixed right navigation bar */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        position: relative;
    }
    
    /* Create fixed navigation area (right side) */
    .fixed-nav-container {
        position: fixed;
        top: 100px;
        right: 20px;
        width: 200px;
        max-height: calc(100vh - 140px);
        overflow-y: auto;
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 1000;
        border: 1px solid #e0e0e0;
    }
    
    /* Anchor offset upwards to compensate for top white bar */
    span[id] {
        scroll-margin-top: 100px;
    }
    
    .fixed-nav-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .fixed-nav-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .fixed-nav-container::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    .fixed-nav-container::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    .nav-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #333;
        border-bottom: 2px solid #667eea;
        padding-bottom: 8px;
    }
    
    .nav-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .nav-list li {
        margin: 2px 0;
    }
    
    .nav-link {
        color: #1f77b4;
        text-decoration: none !important;
        font-size: 0.98rem;
        display: block;
        padding: 5px 10px;
        border-radius: 5px;
        transition: all 0.2s;
        line-height: 1.4;
    }
    
    .nav-link:hover {
        background-color: #e3f2fd;
        color: #0d47a1;
        text-decoration: none !important;
        transform: translateX(3px);
    }
    
    .nav-link:focus, .nav-link:active, .nav-link:visited {
        text-decoration: none !important;
    }
    
    .top-link {
        color: #666;
        font-weight: 600;
        background-color: #f5f5f5;
        margin-bottom: 10px;
    }
    
    .top-link:hover {
        background-color: #eeeeee;
        color: #333;
    }
    
    /* Reserve space on the right side of the main content area */
    .main-content-area {
        margin-right: 280px;
        padding-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render fixed navigation bar
    nav_html = """
    <div class="fixed-nav-container">
        <div class="nav-title">📑 Category Navigation</div>
        <ul class="nav-list">
            <li><a href="#top" class="nav-link top-link">⬆️ Back to Top</a></li>
"""
    
    for idx, category in enumerate(st.session_state.classified_papers.keys()):
        nav_html += f'            <li><a href="#category_{idx}" class="nav-link">{category}</a></li>\n'
    
    nav_html += """        </ul>
    </div>
    """
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Main content area (with left margin)
    st.markdown('<div class="main-content-area">', unsafe_allow_html=True)
    
    # Regenerate the color mapping
    color_palette = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
        '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
        '#F8B739', '#52B788', '#E63946', '#457B9D',
    ]
    num_categories = len(st.session_state.classified_papers)
    colors = [color_palette[i % len(color_palette)] for i in range(num_categories)]
    
    # Add CSS to remove expander spacing
    st.markdown("""
    <style>
    /* Force remove spacing for all expanders */
    [data-testid="stExpander"] {
        margin-bottom: 1px !important;
        margin-top: 0 !important;
        padding: 0 !important;
    }
    
    /* Remove top margin of the first expander */
    div.main-content-area > [data-testid="stExpander"]:first-of-type {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove extra padding in expander content area */
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Remove divider lines between expanders */
    [data-testid="stExpander"] {
        border: none !important;
    }
    
    .streamlit-expanderHeader {
        font-size: 1.1rem !important;
        padding: 0.5rem 0.75rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Each category in a row, expandable to view papers
    for idx, (category, papers) in enumerate(st.session_state.classified_papers.items()):
        color = colors[idx]
        
        # Add anchor tag
        st.markdown(f'<div id="category_{idx}"></div>', unsafe_allow_html=True)
        
        # Use expander to create expandable category area
        with st.expander(f"📁 **{category}** ({len(papers)} papers)", expanded=False):
            # Display category statistics
            st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {color}20 0%, {color}08 100%);
    border-left: 5px solid {color};
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #333; margin-bottom: 0.3rem;">
                📚 {category}
            </div>
            <div style="font-size: 1rem; color: #666;">
                 <strong style="color: {color}; font-size: 1.35rem;">{len(papers)}</strong> papers in total
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
            
            # Display all papers in this category (same format as crawled papers)
            for paper_idx, paper in enumerate(papers, 1):
                with st.expander(f"📄 {paper_idx}. {paper.get('title', 'Untitled')}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**arXiv ID:** {paper.get('arxiv_id', 'N/A')}")
                        
                        # Display date information
                        if paper.get('published_date'):
                            st.markdown(f"**Published Date:** {paper.get('published_date')}")
                        elif paper.get('updated_date'):
                            st.markdown(f"**Updated Date:** {paper.get('updated_date')}")
                        
                        # Display authors
                        authors = paper.get('authors', [])
                        if authors:
                            author_list = ', '.join(authors[:5])
                            st.markdown(f"**Authors:** {author_list}")
                            if len(authors) > 5:
                                st.markdown(f"*...and {len(authors)} more authors*")
                        
                        # Display affiliations (if any)
                        affiliations = paper.get('affiliations', [])
                        # Filter out empty affiliation information
                        valid_affiliations = [a.strip() for a in affiliations if a and a.strip()]
                        if valid_affiliations:
                            # Remove duplicates while preserving order
                            seen = set()
                            unique_affiliations = []
                            for aff in valid_affiliations:
                                if aff not in seen:
                                    seen.add(aff)
                                    unique_affiliations.append(aff)
                            
                            # Display at most the first 3 institutions
                            if unique_affiliations:
                                display_affiliations = unique_affiliations[:3]
                                st.markdown(f"**Affiliations:** {', '.join(display_affiliations)}")
                                if len(unique_affiliations) > 3:
                                    st.markdown(f"*...and {len(unique_affiliations)} more affiliations*")
                        
                        # Task description
                        if 'task_description' in paper:
                            st.markdown(f"**Task Description:** 📌 {paper['task_description']}")
                        
                        # Categories and submission types
                        st.markdown(f"**Categories:** {', '.join(paper.get('categories', []))}")
                        st.markdown(f"**Submission Type:** {paper.get('submission_type', 'N/A')}")
                    
                    with col2:
                        # PDF link
                        if paper.get('pdf_url'):
                            st.link_button("📄 View PDF", paper['pdf_url'], use_container_width=True)
                        
                        # ArXiv page link (compatible with two field names)
                        arxiv_link = paper.get('page_url') or paper.get('arxiv_url')
                        if arxiv_link:
                            st.link_button("🔗 arXiv Page", arxiv_link, use_container_width=True)
                       
                        # Use a unique key to avoid conflicts  
                        chat_toggle_key = f"chat_toggle_{paper.get('arxiv_id')}_{idx}_{paper_idx}"
                        if chat_toggle_key not in st.session_state:
                            st.session_state[chat_toggle_key] = False
                        
                        # Quick Q&A button
                        if st.button("💬 Quick Q&A", key=f"chat_btn_{paper.get('arxiv_id')}_{idx}_{paper_idx}", use_container_width=True):
                            st.session_state[chat_toggle_key] = not st.session_state[chat_toggle_key]
                            st.rerun()
                        
                        # Deep Q&A button
                        if st.button("📖 Deep Q&A", key=f"deep_chat_btn_{paper.get('arxiv_id')}_{idx}_{paper_idx}", use_container_width=True):
                            p_title = paper.get('title', 'N/A')[:100]
                            p_id = paper.get('arxiv_id', 'N/A')
                            target_option = f"{p_id}: {p_title}"
                            st.session_state['paper_selector'] = target_option
                            st.toast("✅ Synchronized to Single Paper Q&A, please switch tabs", icon="📖")
                    
                    # Abstract
                    if paper.get('abstract'):
                        st.markdown("**Abstract:**")
                        st.text_area("", paper['abstract'], height=150, key=f"class_abstract_{idx}_{paper_idx}", disabled=True, label_visibility="collapsed")
                    
                    # If Q&A mode is enabled, display the Q&A area
                    if st.session_state.get(chat_toggle_key, False):
                        st.markdown("---")
                        st.markdown("### 💬 Quick Q&A (Based on Abstract)")
                        
                        # Initialize the Q&A history for this paper
                        chat_key = f"quick_chat_{paper.get('arxiv_id')}"
                        if chat_key not in st.session_state:
                            st.session_state[chat_key] = []
                        
                        # Display chat history
                        for msg in st.session_state[chat_key]:
                            with st.chat_message(msg["role"]):
                                st.write(msg["content"])
                        
                        # Q&A input
                        if prompt := st.chat_input("Enter your question...", key=f"quick_input_{paper.get('arxiv_id')}_{idx}_{paper_idx}"):
                                # Add user message
                                st.session_state[chat_key].append({"role": "user", "content": prompt})
                                
                                # Generate AI response
                                with st.chat_message("assistant"):
                                    with st.spinner("Thinking..."):
                                        try:
                                            # Build context
                                            context = f"""
Paper Title: {paper.get('title', 'N/A')}
Authors: {', '.join(paper.get('authors', [])[:5])}
Abstract: {paper.get('abstract', 'N/A')}
Task Description: {paper.get('task_description', 'N/A')}

User Question: {prompt}

Please answer the user's question based on the above paper information. If the full PDF is needed to answer, please prompt the user to click the "Load Full PDF" button below.
"""
                                            
                                            response = st.session_state.llm_client.chat.completions.create(
                                                model=st.session_state.llm_model,
                                                messages=[
                                                    {"role": "system", "content": "You are a professional academic paper analysis assistant."},
                                                    {"role": "user", "content": context}
                                                ],
                                                temperature=0.7,
                                                max_tokens=1000
                                            )
                                            
                                            answer = response.choices[0].message.content
                                            st.write(answer)
                                            st.session_state[chat_key].append({"role": "assistant", "content": answer})
                                            
                                        except Exception as e:
                                            error_msg = f"❌ Error in response: {str(e)}"
                                            st.error(error_msg)
                                            st.session_state[chat_key].append({"role": "assistant", "content": error_msg})
                                
                                st.rerun()
                        
                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("📖 Deep Q&A on Full Text", key=f"goto_full_{paper.get('arxiv_id')}_{idx}_{paper_idx}", use_container_width=True):
                                p_title = paper.get('title', 'N/A')[:100]
                                p_id = paper.get('arxiv_id', 'N/A')
                                target_option = f"{p_id}: {p_title}"
                                st.session_state['paper_selector'] = target_option
                                st.toast("✅ Synchronized to single paper Q&A, please switch tabs", icon="📖")
                        
                        with btn_col2:
                            if st.button("❌ Close Q&A", key=f"close_chat_{paper.get('arxiv_id')}_{idx}_{paper_idx}", use_container_width=True):
                                st.session_state[chat_toggle_key] = False
                                st.rerun()
    
    # Close main content area div
    st.markdown('</div>', unsafe_allow_html=True)


def show_paper_detail_chat():
    """Display deep Q&A for a single paper"""
    st.header("📖 Deep Q&A for a Single Paper")
    
    if not st.session_state.papers:
        st.info("No paper data available, please crawl papers first")
        return
    
    if not st.session_state.llm_configured:
        st.warning("⚠️ Please configure LLM in the sidebar first")
        return
    
    # Paper selection
    st.subheader("1️⃣ Select Paper")
    
    # Create paper options
    paper_options = {}
    for i, paper in enumerate(st.session_state.papers):
        title = paper.get('title', 'N/A')[:100]
        arxiv_id = paper.get('arxiv_id', 'N/A')
        option_text = f"{arxiv_id}: {title}"
        paper_options[option_text] = i
    
    # Add empty option as placeholder
    options_list = ["-- Please select a paper --"] + list(paper_options.keys())
    
    selected_option = st.selectbox(
        "Select a paper for deep Q&A",
        options=options_list,
        index=0,  # Default to first item (placeholder)
        key="paper_selector"
    )
    
    # If no valid paper is selected, return directly
    if not selected_option or selected_option == "-- Please select a paper --":
        st.info("👆 Please select a paper from the dropdown above")
        return
    
    selected_paper_idx = paper_options[selected_option]
    selected_paper = st.session_state.papers[selected_paper_idx]
    
    # Display basic paper information
    with st.expander("📋 Basic Paper Information", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Title:** {selected_paper.get('title', 'N/A')}")
            st.markdown(f"**ArXiv ID:** {selected_paper.get('arxiv_id', 'N/A')}")
            
            authors = selected_paper.get('authors', [])
            if authors:
                st.markdown(f"**Authors:** {', '.join(authors[:5])}")
                if len(authors) > 5:
                    st.markdown(f"*...and {len(authors)} more authors*")
            
            categories = selected_paper.get('categories', [])
            if categories:
                st.markdown(f"**Categories:** {', '.join(categories)}")
        
        with col2:
            if selected_paper.get('pdf_url'):
                st.link_button("📄 View PDF", selected_paper['pdf_url'], use_container_width=True)
            
            arxiv_url = selected_paper.get('page_url') or selected_paper.get('arxiv_url')
            if arxiv_url:
                st.link_button("🔗 arXiv Page", arxiv_url, use_container_width=True)
    
    st.divider()
    
    # Load paper button
    st.subheader("2️⃣ Load Full Paper")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        load_button = st.button("🔄 Load Full Paper", use_container_width=True, type="primary")
    
    with col2:
        force_reload = st.checkbox("Force Reload", value=False)
    
    with col3:
        if st.session_state.current_paper_for_chat:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.paper_chat_messages = []
                st.session_state.current_paper_for_chat = None
                st.session_state.paper_chatbot = None
                st.rerun()
    
    # Check if paper has changed
    paper_changed = (st.session_state.current_paper_for_chat and 
                     st.session_state.current_paper_for_chat.get('arxiv_id') != selected_paper.get('arxiv_id'))
    
    # If paper has changed, show warning
    if paper_changed:
        st.warning(f"⚠️ You have selected a new paper. Please click the 'Load Full Paper' button to reload.")
    
    # Load paper (only triggered when button is clicked)
    if load_button:
        with st.spinner("Downloading and processing PDF, this may take a few minutes..."):
            # Create or get chatbot
            if not st.session_state.paper_chatbot:
                try:
                    base_url = os.getenv('YUNWU_API_BASE')
                    api_key = os.getenv('YUNWU_API_KEY')
                    
                    st.session_state.paper_chatbot = PaperChatBot(
                        model_name=st.session_state.llm_model,
                        base_url=base_url,
                        api_key=api_key
                    )
                except Exception as e:
                    st.error(f"Failed to create Q&A bot: {e}")
                    return
            
            # Load paper
            try:
                success = st.session_state.paper_chatbot.load_paper(
                    selected_paper, 
                    force_download=force_reload
                )
                
                if success:
                    # If switching to a new paper, clear chat history
                    if (st.session_state.current_paper_for_chat and 
                        st.session_state.current_paper_for_chat.get('arxiv_id') != selected_paper.get('arxiv_id')):
                        st.session_state.paper_chat_messages = []
                    
                    st.session_state.current_paper_for_chat = selected_paper
                    st.session_state.paper_chat_messages = []
                    st.success("✅ Paper loaded successfully! You can now start asking questions.")
                    
                    # Show loading info
                    if st.session_state.paper_chatbot.current_full_text:
                        text_length = len(st.session_state.paper_chatbot.current_full_text)
                        st.info(f"📄 Full text loaded, {text_length:,} characters")
                    else:
                        st.warning("⚠️ Failed to load full text, will use abstract only")
                else:
                    st.error("❌ Failed to load paper")
            except Exception as e:
                st.error(f"Error loading paper: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    st.divider()
    
    # Q&A Interface
    st.subheader("3️⃣ Start Q&A")
    
    if not st.session_state.current_paper_for_chat:
        st.info("💡 Please click the 'Load Full Paper' button above first")
        return
    
    # Show current paper info
    st.caption(f"📚 Current Paper: {st.session_state.current_paper_for_chat.get('title', 'N/A')[:80]}...")
    
    # Example questions (only shown when chat is empty)
    if not st.session_state.paper_chat_messages:
        st.markdown("💡 **Example Questions:**")
        example_col1, example_col2 = st.columns(2)
        
        with example_col1:
            if st.button("📋 What are the core contributions of this paper?", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "What are the core contributions of this paper?"
                })
                st.rerun()
            
            if st.button("🔬 What research methods were used?", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "What research methods were used in this paper?"
                })
                st.rerun()
                
            if st.button("📚 List the main references cited", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "Please list the main references cited in this paper and briefly explain the most critical ones."
                })
                st.rerun()
        
        with example_col2:
            if st.button("📊 What are the experimental results?", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "What are the experimental results of this paper? Any highlights?"
                })
                st.rerun()
            
            if st.button("🎯 What are the limitations or future work?", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "What are the limitations of this paper? What future work directions did the authors propose?"
                })
                st.rerun()
                
            if st.button("🧠 Explain the full text in simple terms", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "Please explain the core ideas and main content of this paper in simple terms, as if teaching a beginner."
                })
                st.rerun()
        
        st.markdown("---")
    
    # Display chat history
    for message in st.session_state.paper_chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # If there is an unprocessed user message, generate AI response
    if (st.session_state.paper_chat_messages and 
        st.session_state.paper_chat_messages[-1]["role"] == "user"):
        
        user_question = st.session_state.paper_chat_messages[-1]["content"]
        
        # Generate AI response and display
        with st.chat_message("assistant"):
            with st.spinner("AI is analyzing the paper and thinking..."):
                try:
                    response = st.session_state.paper_chatbot.chat(user_question)
                    st.write(response)
                    st.session_state.paper_chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"❌ Chat error: {str(e)}"
                    st.write(error_msg)
                    st.session_state.paper_chat_messages.append({"role": "assistant", "content": error_msg})
    
    # Chat input box always at the bottom
    if prompt := st.chat_input("Enter your question about this paper..."):
        # Immediately add user message to history
        st.session_state.paper_chat_messages.append({"role": "user", "content": prompt})
        # Rerun to display user question and generate AI response
        st.rerun()


def show_instructions():
    """Display usage instructions"""
    st.header("ℹ️ Usage Instructions")
    
    st.markdown("""
    ## 🚀 Quick Start
    
    ### 1. Configure LLM (Required for AI Features)
    - In the left sidebar, enter the model name (e.g., `gpt-4`, `gpt-5`)
    - Click the **"🔗 Connect LLM"** button
    - Wait for the connection success message
    - **Note**: Required for AI Analysis and Single Paper Q&A features
    - The system uses environment variables `YUNWU_API_BASE` and `YUNWU_API_KEY` for API configuration
    
    ### 2. Crawl Papers from ArXiv
    
    The system uses **web scraping** to crawl papers from ArXiv website:
    
    - **Select Date Mode**:
      - **📅 Specific Date**: Crawl all papers from a specific date (URL format: `https://arxiv.org/catchup/{category}/{date}?abs=True`)
      - **🆕 Latest Papers**: Get the most recently submitted papers (URL format: `https://arxiv.org/list/{category}/new`)
    - **Choose Category Format**:
      - **Detailed Categories**: Select from specific subcategories (e.g., `cs.CV`, `cs.AI`, `cs.LG`, `cs.CL`, `cs.NE`, `cs.RO`, `math.OC`, `math.ST`)
      - **Simple Categories**: Select from main categories (e.g., `cs`, `math`, `physics`, `q-bio`, `q-fin`, `stat`, `eess`, `econ`)
    - **Select Date** (if using Specific Date mode): Choose a date from the date picker
    - Click **"🚀 Start Crawling"** button
    - The system automatically crawls **New submissions** and **Cross submissions** from the webpage
    - Progress will be displayed in real-time with paper IDs and estimated remaining time
    - **Note**: May encounter reCAPTCHA verification if crawling too frequently
    - Crawled data is automatically saved to the `papers/` directory as JSON files
    
    ### 3. AI Analysis (Optional)
    - After crawling is complete, click the **"🤖 AI Analysis"** button in the sidebar
    - The system will:
      - Generate task descriptions for each paper using LLM
      - Intelligently classify papers into thematic categories
      - Cache results to avoid redundant API calls
    - View the classification results in the **"📊 Data Visualization"** tab:
      - Category distribution charts
      - Network graph of paper relationships
      - Statistical summaries
    - View detailed classification in the **"📋 Classification Details"** tab
    
    ### 4. Export Data to Excel
    - Click the **"📁 Export to Excel"** button in the sidebar
    - The system generates an Excel file containing:
      - All paper information (title, abstract, authors, etc.)
      - Task descriptions (if AI Analysis was performed)
      - Classification categories
    - The file is saved to the `exports/` directory
    - Click the download button to save it locally
    
    ### 5. Single Paper Deep Q&A
    - Switch to the **"💬 Single Paper Q&A"** tab
    - Select a paper from the dropdown menu
    - Click **"📥 Load Full Paper"** to download and process the PDF
    - Wait for the paper to load (this may take a few minutes)
    - Once loaded, you can ask questions about the paper
    - The AI will answer based on the full text content of the paper
    - **Note**: Requires LLM to be configured and the paper PDF to be downloaded
    
    ## 📋 Supported Categories
    
    - 🖥️ **cs** - Computer Science
    - 📐 **math** - Mathematics
    - ⚛️ **physics** - Physics
    - 🧬 **q-bio** - Quantitative Biology
    - 💰 **q-fin** - Quantitative Finance
    - 📊 **stat** - Statistics
    - ⚡ **eess** - Electrical Engineering
    - 💹 **econ** - Economics
    
    ## ⚙️ Technical Details
    
    ### Crawling Method
    - **Web Scraping**: Uses web scraping to extract data from ArXiv web pages (not API)
    - **URL Formats**:
      - Specific date: `https://arxiv.org/catchup/{category}/{date}?abs=True`
      - Latest papers: `https://arxiv.org/list/{category}/new`
    - **Data Extraction**: Parses HTML pages using BeautifulSoup to extract:
      - Title, abstract, authors
      - ArXiv ID, submission date, update date
      - Primary category and all categories
      - PDF download links
      - Author affiliations (when available in meta tags)
    - **Anti-Bot Protection**: 
      - Uses browser-like headers to mimic real browser requests
      - Includes delays between requests to avoid triggering anti-scraping measures
      - May encounter reCAPTCHA if crawling too frequently
    - **Data Storage**: Automatically saves crawled data as JSON files in the `papers/` directory
    - **File Naming**: Files are named with pattern `crawled_{start_date}_{end_date}_{timestamp}.json`
    - **Caching**: Checks for existing cached data before crawling to avoid redundant requests
    
    ### AI Analysis Features
    - **Task Description Generation**: Uses LLM to generate concise task descriptions (≤25 words) for each paper
    - **Intelligent Classification**: Automatically groups papers into thematic categories based on task descriptions
    - **Caching**: Analysis results are cached in the `cache/` directory to avoid redundant API calls
    - **Fallback Classification**: If LLM classification fails, uses keyword-based simple classification
    
    ### Single Paper Q&A
    - **PDF Processing**: Downloads and processes PDF files from ArXiv
    - **Text Extraction**: Extracts full text from PDFs using PDFProcessor
    - **Context Management**: Handles long papers by chunking text and managing conversation history
    - **Deep Understanding**: AI can answer questions based on the complete paper content, not just abstract
    
    ### Data Export
    - **Excel Format**: Exports all paper data to Excel format with multiple sheets
    - **Classification Sheets**: Separate sheets for each classification category
    - **Export Location**: Files saved to `exports/` directory with timestamp
    
    ## 💡 Tips & Best Practices
    
    - **LLM Configuration**: Set up LLM connection before using AI features (Analysis and Q&A)
    - **Date Selection**: Use "Specific Date" mode to crawl papers from a particular date
    - **Category Selection**: 
      - Use "Detailed Categories" for specific subfields (e.g., `cs.CV` for Computer Vision)
      - Use "Simple Categories" for broader fields (e.g., `cs` for all Computer Science)
    - **AI Analysis**: Large paper sets may take time; results are cached for faster subsequent access
    - **Single Paper Q&A**: 
      - PDF download and processing may take a few minutes
      - Ensure you have sufficient disk space for PDFs
      - Questions work best when the paper has been fully loaded
    - **Performance**: 
      - Crawling many papers may take time (web scraping is slower than API)
      - The system includes delays between requests to be respectful to ArXiv servers
      - May encounter reCAPTCHA if crawling too frequently - wait a few minutes and retry
      - AI Analysis processes papers sequentially to avoid overwhelming the LLM API
    - **Data Management**: 
      - Old crawled files are preserved in `papers/` directory
      - Analysis cache helps speed up repeated analyses
    """)


if __name__ == "__main__":
    main()

