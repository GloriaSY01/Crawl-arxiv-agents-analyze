#!/usr/bin/env python3
"""
ArXiv论文智能分析系统 - Streamlit版本
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
    st.error(f"模块导入失败: {e}")

# 页面配置
st.set_page_config(
    page_title="ArXiv论文智能分析系统",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 全局字体设置 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* 主标题 */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.8rem 0;
        margin-bottom: 0.3rem;
        line-height: 1.4;
    }
    
    /* 副标题 */
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    
    /* 侧边栏标题 */
    .sidebar .sidebar-content h1 {
        font-size: 1.1rem !important;
        font-weight: 600;
    }
    
    .sidebar .sidebar-content h2 {
        font-size: 1rem !important;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    .sidebar .sidebar-content h3 {
        font-size: 0.95rem !important;
        font-weight: 500;
    }
    
    /* 主内容区标题 */
    .main h1 {
        font-size: 1.6rem !important;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    
    .main h2 {
        font-size: 1.3rem !important;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }
    
    .main h3 {
        font-size: 1.1rem !important;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* 普通文本 */
    .main p, .main li {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #333;
    }
    
    /* 按钮样式 */
    .stButton button {
        font-size: 0.9rem !important;
        font-weight: 500;
        padding: 0.45rem 1rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* 输入框样式 */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        font-size: 0.9rem !important;
        border-radius: 8px;
    }
    
    .stTextInput label, .stSelectbox label, .stTextArea label {
        font-size: 0.9rem !important;
        font-weight: 500;
    }
    
    /* 进度条 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 论文卡片 */
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
        font-size: 1rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.4rem;
        line-height: 1.4;
    }
    
    .paper-card p {
        font-size: 0.85rem;
        color: #666;
        line-height: 1.5;
        margin-bottom: 0.3rem;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card h3 {
        font-size: 1.8rem !important;
        font-weight: 700;
        margin: 0.3rem 0;
    }
    
    .metric-card p {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    /* 标签样式 */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 0.95rem;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    
    /* 展开/折叠区域 */
    .streamlit-expanderHeader {
        font-size: 0.95rem !important;
        font-weight: 500;
    }
    
    /* 成功/错误/警告消息 */
    .stSuccess, .stError, .stWarning, .stInfo {
        font-size: 0.9rem;
        padding: 0.8rem 1rem;
        border-radius: 8px;
    }
    
    /* 数据框样式 */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* 移除过多的空白 */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    
    /* 表格样式 */
    table {
        font-size: 0.85rem !important;
    }
    
    table th {
        font-weight: 600;
        background-color: #f8f9fa;
    }
    
    /* 代码块 */
    code {
        font-size: 0.85rem;
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
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* 侧边栏样式优化 */
    .sidebar .sidebar-content {
        padding: 1rem 1rem;
    }
    
    /* 聊天消息样式 */
    .stChatMessage {
        font-size: 0.9rem;
    }
    
    /* 下载按钮 */
    .stDownloadButton button {
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
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
    """主函数"""
    
    # 标题
    st.markdown('<h1 class="main-header">🚀 ArXiv论文智能分析系统</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI驱动的论文爬取、分析与可视化平台</p>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 配置与设置")
        
        # LLM配置
        st.subheader("🤖 LLM配置")
        model_name = st.text_input("模型名称", value="gpt-5", key="model_name")
        
        if st.button("🔗 连接LLM", use_container_width=True):
            with st.spinner("正在连接..."):
                success, message = configure_llm(model_name)
                if success:
                    st.success(message)
                    st.session_state.llm_configured = True
                else:
                    st.error(message)
        
        st.divider()
        
        # 爬取设置
        st.subheader("📅 爬取设置")
        
        st.info("🌐 从网页爬取 **New submissions** 和 **Cross submissions**")
        
        # 日期选择模式
        date_mode = st.radio(
            "日期选择",
            options=["single", "latest"],
            format_func=lambda x: {
                "single": "📅 指定日期（符合题目要求）",
                "latest": "🆕 最新论文"
            }[x],
            horizontal=True
        )
        
        # 类别选择（支持题目要求的格式，如cs.CV）
        category_type = st.radio(
            "类别格式",
            options=["detailed", "simple"],
            format_func=lambda x: {
                "detailed": "详细分类（如 cs.CV, cs.AI）",
                "simple": "简单分类（如 cs, math）"
            }[x],
            horizontal=True
        )
        
        if category_type == "detailed":
            category = st.selectbox(
                "选择详细类别",
                options=["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.NE", "cs.RO", "math.OC", "math.ST"],
                help="题目示例使用 cs.CV (Computer Vision)"
            )
        else:
            category = st.selectbox(
                "选择类别",
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
            # 单日期选择（符合题目要求）
            selected_date = st.date_input("选择日期", value=None)
            if selected_date:
                st.caption(f"💡 将爬取 {selected_date} 当天的论文（URL格式: /catchup/{category}/{selected_date}?abs=True）")
            else:
                st.warning("⚠️ 请选择日期")
        
        if st.button("🚀 开始爬取", use_container_width=True, type="primary"):
            if date_mode == "single" and selected_date:
                crawl_papers_by_date(category, selected_date.strftime("%Y-%m-%d"))
            elif date_mode == "latest":
                crawl_papers(category)
            else:
                st.error("⚠️ 请选择日期")
        
        st.divider()
        
        # 数据操作
        st.subheader("🔬 数据操作")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤖 AI分析", use_container_width=True, disabled=not st.session_state.papers or not st.session_state.llm_configured):
                analyze_papers()
        
        with col2:
            if st.button("📁 导出Excel", use_container_width=True, disabled=not st.session_state.papers):
                export_to_excel()
        
        st.divider()
        
        # 统计信息
        if st.session_state.papers:
            st.subheader("📊 统计信息")
            st.metric("论文总数", len(st.session_state.papers))
            if st.session_state.classified_papers:
                st.metric("分类数量", len(st.session_state.classified_papers))
    
    # 主内容区 - 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 数据可视化", "📋 分类详情", "💬 单篇论文问答", "ℹ️ 使用说明"])
    
    with tab1:
        show_visualization()
    
    with tab2:
        show_classification_details()
    
    with tab3:
        show_paper_detail_chat()
    
    with tab4:
        show_instructions()


def configure_llm(model_name: str) -> tuple:
    """配置LLM"""
    try:
        # 检查OpenAI库是否已安装
        if OpenAI is None:
            return False, "❌ OpenAI库未安装。请运行: pip install openai"
        
        # 从环境变量获取API配置
        base_url = os.getenv('YUNWU_API_BASE')
        api_key = os.getenv('YUNWU_API_KEY')
        
        if base_url is None:
            return False, "❌ 环境变量 YUNWU_API_BASE 未设置，请通过命令行参数 --base_url 设置"
        if api_key is None:
            return False, "❌ 环境变量 YUNWU_API_KEY 未设置，请通过命令行参数 --api_key 设置"
        
        # 创建客户端
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # 测试连接
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                timeout=10
            )
        except Exception as conn_error:
            return False, f"❌ API连接失败: {str(conn_error)}\n\n请检查:\n1. 网络连接\n2. API密钥是否正确\n3. 模型名称是否正确"
        
        # 创建分析器
        st.session_state.analyzer = PaperAnalyzer(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key
        )
        st.session_state.llm_client = client
        st.session_state.llm_model = model_name
        st.session_state.llm_configured = True
        
        return True, f"✅ 成功连接到 {model_name}"
    except Exception as e:
        return False, f"❌ 连接失败: {str(e)}"


def crawl_papers_by_date(category: str, date: str):
    """按指定日期爬取论文（符合题目要求的catchup格式）"""
    if not st.session_state.crawler:
        st.session_state.crawler = ArxivCrawler()
    
    # 创建进度显示区域
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    time_placeholder = st.empty()
    
    # 进度回调函数
    def progress_callback(current, total, arxiv_id, time_remaining):
        if total > 0:
            progress = int((current / total) * 100)
            progress_bar.progress(progress)
        status_placeholder.info(f"🔍 正在爬取论文 [{current}/{total}]: {arxiv_id}")
        
        # 显示剩余时间
        if time_remaining:
            if time_remaining < 60:
                time_str = f"{time_remaining:.0f}秒"
            elif time_remaining < 3600:
                minutes = time_remaining / 60
                time_str = f"{minutes:.1f}分钟"
            else:
                hours = time_remaining / 3600
                time_str = f"{hours:.1f}小时"
            time_placeholder.warning(f"⏱️ 预估剩余时间: {time_str}")
    
    try:
        status_placeholder.info(f"🔍 正在爬取 {category} 类别在 {date} 的论文...")
        info_placeholder.info(f"📅 URL格式: /catchup/{category}/{date}?abs=True")
        progress_bar.progress(5)
        
        # 使用catchup格式爬取
        papers = st.session_state.crawler.crawl_by_date(category, date, progress_callback)
        
        progress_bar.progress(100)
        time_placeholder.empty()
        
        # 调试信息
        print(f"\n[DEBUG] 爬取结果: papers类型={type(papers)}, 长度={len(papers) if papers else 0}")
        if papers and len(papers) > 0:
            print(f"[DEBUG] 第一篇论文的键: {list(papers[0].keys()) if papers[0] else 'None'}")
        
        if papers and len(papers) > 0:
            st.session_state.papers = papers
            
            # 统计
            new_count = sum(1 for p in papers if p.get('submission_type') == 'New submission')
            cross_count = sum(1 for p in papers if p.get('submission_type') == 'Cross submission' or p.get('submission_type') == 'Cross-list')
            
            # 保存到文件
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"papers/crawled_{timestamp}.json"
                abs_filename = os.path.abspath(filename)
                
                print(f"\n[DEBUG] 准备保存文件: {abs_filename}")
                print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
                
                # 确保目录存在
                os.makedirs('papers', exist_ok=True)
                print(f"[DEBUG] papers目录已创建/存在")
                
                # 保存文件
                print(f"[DEBUG] 开始写入JSON文件，包含 {len(papers)} 篇论文...")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] JSON文件写入完成")
                
                # 验证文件是否创建成功
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"[DEBUG] 文件验证成功，大小: {file_size} 字节 ({file_size / 1024:.2f} KB)")
                    status_placeholder.success(f"✅ 成功爬取 {len(papers)} 篇论文！")
                    info_placeholder.success(
                        f"📊 New submissions: {new_count} 篇\n"
                        f"📊 Cross submissions: {cross_count} 篇\n"
                        f"💾 已保存到: {filename}\n"
                        f"📦 文件大小: {file_size / 1024:.2f} KB\n"
                        f"📍 完整路径: {abs_filename}"
                    )
                else:
                    status_placeholder.warning(f"⚠️ 爬取成功但文件保存失败")
                    info_placeholder.error(f"文件路径: {os.path.abspath(filename)}")
                    
            except Exception as save_error:
                status_placeholder.warning(f"⚠️ 爬取成功但保存文件时出错")
                info_placeholder.error(f"保存错误: {str(save_error)}\n\n文件路径: {os.path.abspath(filename) if 'filename' in locals() else 'N/A'}")
                import traceback
                st.error(f"详细错误:\n```\n{traceback.format_exc()}\n```")
            
            time.sleep(3)
            status_placeholder.empty()
            info_placeholder.empty()
            st.rerun()
        else:
            status_placeholder.error("❌ 未找到论文或遇到reCAPTCHA")
            info_placeholder.warning("💡 建议：\n1. 等待几分钟后重试\n2. 检查日期和类别是否正确\n3. 查看终端输出获取更多信息")
            
    except Exception as e:
        status_placeholder.error(f"❌ 爬取失败: {str(e)}")
        import traceback
        info_placeholder.error(f"```\n{traceback.format_exc()}\n```")
    finally:
        progress_bar.empty()
        time_placeholder.empty()


def crawl_papers(category: str):
    """爬取论文"""
    if not st.session_state.crawler:
        st.session_state.crawler = ArxivCrawler()
    
    # 创建进度显示区域
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    time_placeholder = st.empty()
    
    # 进度回调函数
    def progress_callback(current, total, arxiv_id, time_remaining):
        progress = int((current / total) * 100)
        progress_bar.progress(progress)
        status_placeholder.info(f"🔍 正在爬取论文 [{current}/{total}]: {arxiv_id}")
        
        # 显示剩余时间
        if time_remaining:
            if time_remaining < 60:
                time_str = f"{time_remaining:.0f}秒"
            elif time_remaining < 3600:
                minutes = time_remaining / 60
                time_str = f"{minutes:.1f}分钟"
            else:
                hours = time_remaining / 3600
                time_str = f"{hours:.1f}小时"
            time_placeholder.warning(f"⏱️ 预估剩余时间: {time_str}")
    
    try:
        status_placeholder.info(f"🔍 正在爬取 {category} 类别的最新论文...")
        progress_bar.progress(5)
        
        # 爬取论文（带进度回调）
        papers = st.session_state.crawler.crawl_new_submissions(category, progress_callback)
        
        progress_bar.progress(100)
        time_placeholder.empty()
        
        # 调试信息
        print(f"\n[DEBUG] 爬取结果: papers类型={type(papers)}, 长度={len(papers) if papers else 0}")
        if papers and len(papers) > 0:
            print(f"[DEBUG] 第一篇论文的键: {list(papers[0].keys()) if papers[0] else 'None'}")
        
        if papers and len(papers) > 0:
            st.session_state.papers = papers
            
            # 保存到文件
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"papers/crawled_{timestamp}.json"
                abs_filename = os.path.abspath(filename)
                
                print(f"\n[DEBUG] 准备保存文件: {abs_filename}")
                print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
                
                # 确保目录存在
                os.makedirs('papers', exist_ok=True)
                print(f"[DEBUG] papers目录已创建/存在")
                
                # 保存文件
                print(f"[DEBUG] 开始写入JSON文件，包含 {len(papers)} 篇论文...")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] JSON文件写入完成")
                
                # 验证文件是否创建成功
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"[DEBUG] 文件验证成功，大小: {file_size} 字节 ({file_size / 1024:.2f} KB)")
                    status_placeholder.success(f"✅ 成功爬取 {len(papers)} 篇论文！")
                    info_placeholder.success(
                        f"💾 已保存到: {filename}\n"
                        f"📦 文件大小: {file_size / 1024:.2f} KB\n"
                        f"📍 完整路径: {abs_filename}"
                    )
                else:
                    status_placeholder.warning(f"⚠️ 爬取成功但文件保存失败")
                    info_placeholder.error(f"文件路径: {os.path.abspath(filename)}")
                    
            except Exception as save_error:
                status_placeholder.warning(f"⚠️ 爬取成功但保存文件时出错")
                info_placeholder.error(f"保存错误: {str(save_error)}\n\n文件路径: {os.path.abspath(filename) if 'filename' in locals() else 'N/A'}")
                import traceback
                st.error(f"详细错误:\n```\n{traceback.format_exc()}\n```")
            
            time.sleep(3)
            status_placeholder.empty()
            info_placeholder.empty()
            st.rerun()
        else:
            status_placeholder.error("❌ 未找到论文")
            info_placeholder.warning("💡 建议：\n1. 检查类别是否正确\n2. 查看终端输出获取更多信息")
            
    except Exception as e:
        status_placeholder.error(f"❌ 爬取失败: {str(e)}")
    finally:
        progress_bar.empty()
        time_placeholder.empty()


def analyze_papers():
    """分析论文"""
    if not st.session_state.papers:
        st.warning("请先爬取论文")
        return
    
    if not st.session_state.analyzer:
        st.warning("请先配置LLM")
        return
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    info_placeholder = st.empty()
    
    # 进度回调函数
    def progress_callback(current, total, paper_title):
        progress = int((current / total) * 50)  # 前50%用于生成任务描述
        progress_bar.progress(progress)
        status_placeholder.info(f"🤖 正在生成任务描述 [{current}/{total}]")
        info_placeholder.info(f"📄 当前处理: {paper_title}")
    
    try:
        total_papers = len(st.session_state.papers)
        status_placeholder.info(f"🤖 开始为 {total_papers} 篇论文生成任务描述...")
        info_placeholder.info("⏳ 请稍候，这可能需要几分钟...")
        progress_bar.progress(5)
        
        print(f"\n[DEBUG] 开始分析 {total_papers} 篇论文")
        print(f"[DEBUG] 使用模型: {st.session_state.analyzer.model_name}")
        
        # 生成任务描述（带进度回调）
        st.session_state.papers = st.session_state.analyzer.batch_generate_task_descriptions(
            st.session_state.papers, 
            show_progress=True,
            progress_callback=progress_callback
        )
        
        progress_bar.progress(60)
        status_placeholder.info("🎯 正在智能分类...")
        info_placeholder.info("📊 基于任务描述进行聚类...")
        
        # 分类
        st.session_state.classified_papers = st.session_state.analyzer.classify_papers(
            st.session_state.papers
        )
        
        progress_bar.progress(100)
        status_placeholder.success(f"✅ 分析完成！共 {len(st.session_state.classified_papers)} 个类别")
        info_placeholder.success(f"📊 已为 {total_papers} 篇论文生成任务描述并完成分类")
        time.sleep(2)
        status_placeholder.empty()
        info_placeholder.empty()
        st.rerun()
        
    except Exception as e:
        status_placeholder.error(f"❌ 分析失败: {str(e)}")
        info_placeholder.error(f"详细错误信息请查看终端输出")
        import traceback
        print(f"\n[ERROR] 分析失败: {e}")
        traceback.print_exc()
    finally:
        progress_bar.empty()


def export_to_excel():
    """导出到Excel"""
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
        
        st.success(f"✅ 导出成功！")
        st.info(f"💾 文件保存在: {filename}")
        
        # 提供下载按钮
        with open(filename, 'rb') as f:
            st.download_button(
                label="📥 下载Excel文件",
                data=f,
                file_name=os.path.basename(filename),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"❌ 导出失败: {str(e)}")


def create_interactive_network_graph(classified_papers: Dict[str, List[Dict]]):
    """
    创建交互式网络图，展示论文分类/聚类结果
    
    Args:
        classified_papers: 分类后的论文字典 {类别: [论文列表]}
    
    Returns:
        Plotly图形对象
    """
    if not HAS_NETWORKX:
        print("[ERROR] networkx库未安装")
        return None
    
    if not classified_papers:
        print("[ERROR] classified_papers为空")
        return None
    
    try:
        # 验证数据
        total_papers = sum(len(papers) for papers in classified_papers.values())
        if total_papers == 0:
            print("[ERROR] 没有论文数据")
            return None
        
        print(f"[DEBUG] 开始创建网络图: {len(classified_papers)} 个类别, {total_papers} 篇论文")
        
        # 创建网络图
        G = nx.Graph()
        
        # 简洁清爽的配色方案
        color_palette = [
            '#FF6B6B',  # 珊瑚红
            '#4ECDC4',  # 青色
            '#45B7D1',  # 天蓝
            '#FFA07A',  # 浅橙
            '#98D8C8',  # 薄荷绿
            '#F7DC6F',  # 柠檬黄
            '#BB8FCE',  # 淡紫
            '#85C1E2',  # 浅蓝
            '#F8B739',  # 金黄
            '#52B788',  # 森林绿
            '#E63946',  # 深红
            '#457B9D',  # 钢蓝
        ]
        
        num_categories = len(classified_papers)
        # 如果类别数量超过预设颜色，循环使用
        colors = [color_palette[i % len(color_palette)] for i in range(num_categories)]
        category_colors = {cat: colors[i] for i, cat in enumerate(classified_papers.keys())}
        
        # 添加节点和边
        node_info = {}  # 存储节点信息用于悬停
        node_hover_texts = {}  # 存储每个节点的悬停文本
        node_urls = {}  # 存储节点URL（用于点击）
        
        node_list = []  # 按顺序存储所有节点ID
        category_paper_ids = {}  # 存储每个类别的论文ID列表，用于布局
        
        # 为每个分类创建中心节点
        category_nodes = {}
        for category, papers in classified_papers.items():
            # 分类中心节点
            cat_node_id = f"CAT_{category}"
            G.add_node(cat_node_id)
            node_list.append(cat_node_id)
            category_nodes[category] = cat_node_id
            node_info[cat_node_id] = {
                'type': 'category',
                'name': category,
                'count': len(papers)
            }
            node_hover_texts[cat_node_id] = f"<b>{category}</b><br>论文数: {len(papers)}"
            
            # 初始化该类别的论文ID列表
            category_paper_ids[category] = []
            
            # 为每篇论文创建节点并连接到分类节点
            for paper_idx, paper in enumerate(papers):
                # 确保每个论文都有唯一的ID
                paper_id = paper.get('arxiv_id', '')
                if not paper_id or paper_id in G.nodes():
                    # 如果arxiv_id为空或已存在，使用备用ID
                    paper_id = f"PAPER_{category}_{paper_idx}_{len(node_list)}"
                
                if paper_id not in G.nodes():
                    G.add_node(paper_id)
                    node_list.append(paper_id)
                    category_paper_ids[category].append(paper_id)  # 记录该论文属于这个类别
                    # 连接到分类节点
                    G.add_edge(cat_node_id, paper_id)
                    
                    # 存储论文信息
                    title = paper.get('title', 'N/A')
                    title_short = title[:50] + ('...' if len(title) > 50 else '')
                    authors = ', '.join(paper.get('authors', [])[:3])
                    if len(paper.get('authors', [])) > 3:
                        authors += f" 等{len(paper.get('authors', []))}人"
                    
                    task_desc = paper.get('task_description', 'N/A')
                    
                    node_info[paper_id] = {
                        'type': 'paper',
                        'title': title,
                        'authors': authors,
                        'task_description': task_desc,
                        'category': category
                    }
                    
                    # 悬停文本
                    hover_text = f"<b>{title_short}</b><br>"
                    hover_text += f"作者: {authors}<br>"
                    if task_desc and task_desc != 'N/A':
                        task_short = task_desc[:60] + ('...' if len(task_desc) > 60 else '')
                        hover_text += f"任务: {task_short}"
                    node_hover_texts[paper_id] = hover_text
                    
                    # 存储URL
                    arxiv_url = paper.get('arxiv_url') or paper.get('page_url', '')
                    if arxiv_url:
                        node_urls[paper_id] = arxiv_url
        
        # 检查节点数量
        if len(G.nodes()) == 0:
            print("[ERROR] 网络图没有节点")
            return None
        
        print(f"[DEBUG] 网络图节点数: {len(G.nodes())}, 边数: {len(G.edges())}")
        
        # 使用改进的力导向布局 - 平衡聚集和防重叠
        try:
            # 使用spring_layout，调整参数避免重叠
            pos = nx.spring_layout(
                G, 
                k=1.0 / (len(G.nodes()) ** 0.3),  # 根据节点数量自适应k值，避免重叠
                iterations=150,  # 更多迭代次数确保稳定
                seed=42,
                scale=20  # 更大的整体规模
            )
            print(f"[DEBUG] 使用力导向布局完成，定位了 {len(pos)} 个节点")
            
            # 后处理：检测并调整重叠的节点
            import math
            min_distance = 0.8  # 节点之间的最小距离
            
            node_positions = list(pos.items())
            for i in range(len(node_positions)):
                for j in range(i + 1, len(node_positions)):
                    node1, pos1 = node_positions[i]
                    node2, pos2 = node_positions[j]
                    
                    # 计算两节点之间的距离
                    dx = pos1[0] - pos2[0]
                    dy = pos1[1] - pos2[1]
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    # 如果距离太近，推开它们
                    if dist < min_distance and dist > 0:
                        # 计算推开的方向和距离
                        push_dist = (min_distance - dist) / 2
                        angle = math.atan2(dy, dx)
                        
                        # 更新位置
                        pos[node1] = (
                            pos1[0] + push_dist * math.cos(angle),
                            pos1[1] + push_dist * math.sin(angle)
                        )
                        pos[node2] = (
                            pos2[0] - push_dist * math.cos(angle),
                            pos2[1] - push_dist * math.sin(angle)
                        )
            
            print(f"[DEBUG] 防重叠处理完成")
            
        except Exception as layout_error:
            print(f"[ERROR] 力导向布局失败: {layout_error}，使用自定义布局")
            
            # 备用：自定义分散布局
            import math
            import random
            random.seed(42)
            pos = {}
            
            num_categories = len(classified_papers)
            used_positions = set()
            
            for cat_idx, category in enumerate(classified_papers.keys()):
                # 为类别中心找一个不重叠的位置
                max_attempts = 100
                for attempt in range(max_attempts):
                    # 随机分散类别中心 - 增大分布范围
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(8, 20)  # 从5-15增大到8-20
                    cat_x = radius * math.cos(angle)
                    cat_y = radius * math.sin(angle)
                    
                    # 检查是否与其他类别中心距离足够远
                    too_close = False
                    for other_pos in used_positions:
                        dist = math.sqrt((cat_x - other_pos[0])**2 + (cat_y - other_pos[1])**2)
                        if dist < 12:  # 进一步增大最小距离，避免类别簇重叠
                            too_close = True
                            break
                    
                    if not too_close or attempt == max_attempts - 1:
                        used_positions.add((cat_x, cat_y))
                        break
                
                cat_node_id = f"CAT_{category}"
                pos[cat_node_id] = (cat_x, cat_y)
                
                # 获取该类别的所有论文节点ID
                paper_ids = category_paper_ids.get(category, [])
                num_papers = len(paper_ids)
                
                if num_papers == 0:
                    continue
                
                # 根据论文数量调整分布半径 - 增大半径避免重叠
                if num_papers <= 5:
                    radius_papers = 1.5
                elif num_papers <= 10:
                    radius_papers = 2.0
                elif num_papers <= 20:
                    radius_papers = 2.8
                else:
                    radius_papers = 3.5
                
                # 将论文节点围绕类别中心分布，确保不重叠
                for paper_idx, paper_id in enumerate(paper_ids):
                    if num_papers == 1:
                        paper_angle = math.pi / 4
                        paper_radius = 1.2  # 保持一定距离
                    elif num_papers <= 6:
                        # 少量论文，单层分布
                        paper_angle = 2 * math.pi * paper_idx / num_papers
                        paper_radius = radius_papers
                    elif num_papers <= 12:
                        # 中等论文，单层但增大半径
                        paper_angle = 2 * math.pi * paper_idx / num_papers
                        paper_radius = radius_papers * 1.2
                    else:
                        # 多论文，多层螺旋分布
                        layer = paper_idx // 6  # 每6个论文一层
                        angle_offset = (layer % 2) * (math.pi / 6)  # 错开角度
                        paper_angle = 2 * math.pi * (paper_idx % 6) / 6 + angle_offset
                        paper_radius = radius_papers + layer * 1.0  # 增大层间距
                    
                    paper_x = cat_x + paper_radius * math.cos(paper_angle)
                    paper_y = cat_y + paper_radius * math.sin(paper_angle)
                    pos[paper_id] = (paper_x, paper_y)
            
            print(f"[DEBUG] 自定义分散布局完成，定位了 {len(pos)} 个节点")
        
        # 在确定布局后，进一步拉大论文节点与分类中心节点的距离
        # 这样可以让每个类别的“花瓣”更舒展，避免论文节点挤在分类节点附近
        try:
            distance_scale = 2.0  # 距离放大倍数，可根据需要调整（>1 表示拉远）
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
                
                # 如果刚好重合，给一个很小的偏移，避免除零或方向为零
                if dx == 0 and dy == 0:
                    dx, dy = 0.1, 0.1
                
                pos[node_id] = (cx + dx * distance_scale, cy + dy * distance_scale)
            
            print(f"[DEBUG] 已放大论文节点与分类节点的距离，scale={distance_scale}")
        except Exception as adjust_error:
            print(f"[WARN] 调整论文节点距离失败: {adjust_error}")
        
        # 提取边的坐标 - 使用渐变色和更精细的样式
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # 创建边的轨迹 - 更细的线条适合紧密布局
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(
                width=0.5,  # 减小线宽，更简洁
                color='rgba(180, 180, 180, 0.3)'  # 更淡的颜色
            ),
            hoverinfo='none',
            mode='lines'
        )
        
        # 提取节点坐标和文本（按照node_list的顺序）
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
            
            # 节点标签（只显示分类名称，简短避免重叠）
            if node_info.get(node, {}).get('type') == 'category':
                label = node_info[node].get('name', '')
                # 截断过长的标签
                if len(label) > 15:
                    label = label[:13] + '..'
                node_labels.append(label)
            else:
                node_labels.append('')
            
            # 悬停文本
            hover_texts_ordered.append(node_hover_texts.get(node, ''))
            
            # 节点大小和颜色 - 减小尺寸避免重叠
            if node.startswith('CAT_'):
                # 分类中心节点 - 适中大小
                cat_name = node.replace('CAT_', '')
                node_sizes_ordered.append(25)  # 从35减小到25
                node_colors_ordered.append(category_colors.get(cat_name, colors[0]))
            else:
                # 论文节点 - 更小的圆点避免重叠
                node_sizes_ordered.append(6)  # 从8减小到6
                paper_category = node_info.get(node, {}).get('category', '')
                node_colors_ordered.append(category_colors.get(paper_category, colors[0]))
        
        # 分离类别节点和论文节点的轨迹，避免标签重叠
        # 类别节点（带标签）
        cat_x, cat_y, cat_labels, cat_hover, cat_sizes, cat_colors = [], [], [], [], [], []
        # 论文节点（无标签）
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
        
        # 类别中心节点轨迹（带标签，标签显示在上方避免重叠）
        cat_trace = go.Scatter(
            x=cat_x, y=cat_y,
            mode='markers+text',
            hoverinfo='text',
            text=cat_labels,
            textposition="top center",  # 标签在节点上方
            textfont=dict(
                size=10,  # 稍小的字体避免重叠
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
            cliponaxis=False,  # 允许标签超出图表区域
            name='类别中心'
        )
        
        # 论文节点轨迹（无标签）
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
            name='论文'
        )
        
        # 在右侧显示图例
        legend_annotations = []
        legend_y_start = 0.98
        legend_spacing = 0.04  # 根据类别数量动态调整间距
        
        # 如果类别很多，缩小间距
        if num_categories > 15:
            legend_spacing = 0.03
        elif num_categories > 20:
            legend_spacing = 0.025
        
        for idx, (category, color) in enumerate(category_colors.items()):
            paper_count = len(classified_papers[category])
            y_position = legend_y_start - idx * legend_spacing
            
            # 只显示在可见范围内的图例
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
        
        # 创建图形（边在最底层，论文节点在中间，类别节点和标签在最上层）
        fig = go.Figure(
            data=[edge_trace, paper_trace, cat_trace],
            layout=go.Layout(
                title=dict(
                    text='论文分类网络图',
                    font=dict(size=18, color='#2c3e50'),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=40, l=40, r=right_margin, t=80),  # 增加上下左边距，防止标签被裁剪
                annotations=[
                    dict(
                        text="💡 提示: 同颜色节点属于同一类别 | 同类论文自动聚集 | 鼠标悬停查看详情",
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
                height=850,  # 增加高度以适应标签和内容
                autosize=True,  # 自动调整大小
                uniformtext=dict(
                    mode='hide',  # 隐藏空间不足的文本而不是缩放
                    minsize=8  # 最小字体大小
                )
            )
        )
        
        # 添加点击事件处理（通过自定义JavaScript）
        # 注意：Plotly在Streamlit中的点击事件需要通过其他方式处理
        # 这里我们通过悬停信息提示用户点击
        
        return fig
        
    except Exception as e:
        error_msg = f"创建网络图失败: {e}"
        print(f"[ERROR] {error_msg}")
        import traceback
        print("[ERROR] 详细错误信息:")
        traceback.print_exc()
        # 注意：这里不能使用st.error，因为可能不在Streamlit上下文中
        return None


def show_visualization():
    """显示数据可视化"""
    st.header("📊 数据可视化")
    
    if not st.session_state.papers:
        st.info("暂无数据，请先爬取论文")
        return
    
    # 基本统计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 论文总数", len(st.session_state.papers))
    
    with col2:
        new_count = sum(1 for p in st.session_state.papers if p.get('submission_type') == 'New submission')
        st.metric("🆕 新提交", new_count)
    
    with col3:
        cross_count = sum(1 for p in st.session_state.papers if p.get('submission_type') == 'Cross-list')
        st.metric("🔀 交叉列表", cross_count)
    
    st.divider()
    
    # 分类可视化
    if st.session_state.classified_papers:
        # 可视化模式选择
        viz_mode = st.radio(
            "选择可视化模式",
            ["📊 交互式网络图", "📈 统计图表"],
            horizontal=True,
            key="viz_mode"
        )
        
        if viz_mode == "📊 交互式网络图":
            st.subheader("📊 论文分类交互式网络图")
            st.caption("💡 提示：力导向算法自动聚类，同类论文聚集在一起，右侧显示图例")
            
            if HAS_NETWORKX:
                # 检查数据
                if not st.session_state.classified_papers:
                    st.warning("没有分类数据，请先执行AI分析")
                else:
                    # 调试信息
                    total_papers = sum(len(papers) for papers in st.session_state.classified_papers.values())
                    st.caption(f"📊 共 {len(st.session_state.classified_papers)} 个类别，{total_papers} 篇论文")
                    
                    # 创建交互式网络图
                    with st.spinner("正在生成网络图..."):
                        network_fig = create_interactive_network_graph(st.session_state.classified_papers)
                    
                    if network_fig:
                        # 配置图表显示选项
                        config = {
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                            'scrollZoom': True
                        }
                        st.plotly_chart(network_fig, use_container_width=True, config=config)
                    else:
                        st.warning("⚠️ 无法创建网络图")
                        st.info("💡 可能的原因：\n1. 数据格式不正确\n2. 网络图节点过多\n3. networkx库未正确安装\n4. 请查看终端输出的详细错误信息")
                        st.code("请检查终端输出中的 [ERROR] 和 [DEBUG] 信息", language='text')
            else:
                st.warning("⚠️ 需要安装 networkx 库来显示网络图。运行: pip install networkx")
                st.info("显示统计图表作为替代...")
                viz_mode = "📈 统计图表"
        
        if viz_mode == "📈 统计图表":
            st.subheader("📊 论文分类分布")
            
            # 准备数据
            categories = list(st.session_state.classified_papers.keys())
            counts = [len(papers) for papers in st.session_state.classified_papers.values()]
            
            # 创建柱状图
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
                title="各类别论文数量",
                xaxis_title="类别",
                yaxis_title="论文数量",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📌 请先执行 AI 分析以查看分类结果")
        
        # 显示提交类型分布
        st.subheader("📊 提交类型分布")
        
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
            title="提交类型占比",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_classification_details():
    """显示分类详情"""
    st.header("📋 分类详情")
    
    if not st.session_state.papers:
        st.info("暂无数据，请先爬取论文")
        return
    
    if not st.session_state.classified_papers:
        st.info("📌 请先执行 AI 分析以查看分类结果")
        return
    
    # 统计信息
    total_papers = sum(len(papers) for papers in st.session_state.classified_papers.values())
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 分类数量", len(st.session_state.classified_papers))
    with col2:
        st.metric("📄 论文总数", total_papers)
    
    st.divider()
    
    # 重新生成颜色映射
    color_palette = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
        '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
        '#F8B739', '#52B788', '#E63946', '#457B9D',
    ]
    num_categories = len(st.session_state.classified_papers)
    colors = [color_palette[i % len(color_palette)] for i in range(num_categories)]
    
    # 每个类别一行，可以展开查看论文
    for idx, (category, papers) in enumerate(st.session_state.classified_papers.items()):
        color = colors[idx]
        
        # 使用expander创建可展开的类别区域
        with st.expander(f"📁 **{category}** ({len(papers)} 篇)", expanded=False):
            # 显示类别统计信息
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
                        <div style="font-size: 1.1rem; font-weight: 600; color: #333; margin-bottom: 0.3rem;">
                            📚 {category}
                        </div>
                        <div style="font-size: 0.9rem; color: #666;">
                            共 <strong style="color: {color}; font-size: 1.2rem;">{len(papers)}</strong> 篇论文
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 显示该类别的所有论文（与已爬取的论文显示格式相同）
            for paper_idx, paper in enumerate(papers, 1):
                with st.expander(f"📄 {paper_idx}. {paper.get('title', '无标题')}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**arXiv ID:** {paper.get('arxiv_id', 'N/A')}")
                        
                        # 显示日期信息
                        if paper.get('published_date'):
                            st.markdown(f"**发布日期:** {paper.get('published_date')}")
                        elif paper.get('updated_date'):
                            st.markdown(f"**更新日期:** {paper.get('updated_date')}")
                        
                        # 显示作者
                        authors = paper.get('authors', [])
                        if authors:
                            author_list = ', '.join(authors[:5])
                            st.markdown(f"**作者:** {author_list}")
                            if len(authors) > 5:
                                st.markdown(f"*...等 {len(authors)} 位作者*")
                        
                        # 显示机构（如果有）
                        affiliations = paper.get('affiliations', [])
                        # 过滤出非空的机构信息
                        valid_affiliations = [a.strip() for a in affiliations if a and a.strip()]
                        if valid_affiliations:
                            # 去重并保持顺序
                            seen = set()
                            unique_affiliations = []
                            for aff in valid_affiliations:
                                if aff not in seen:
                                    seen.add(aff)
                                    unique_affiliations.append(aff)
                            
                            # 最多显示前3个机构
                            if unique_affiliations:
                                display_affiliations = unique_affiliations[:3]
                                st.markdown(f"**机构:** {', '.join(display_affiliations)}")
                                if len(unique_affiliations) > 3:
                                    st.markdown(f"*...等 {len(unique_affiliations)} 个机构*")
                        
                        # 任务描述
                        if 'task_description' in paper:
                            st.markdown(f"**任务描述:** 📌 {paper['task_description']}")
                        
                        # 分类和提交类型
                        st.markdown(f"**分类:** {', '.join(paper.get('categories', []))}")
                        st.markdown(f"**提交类型:** {paper.get('submission_type', 'N/A')}")
                    
                    with col2:
                        # PDF 链接
                        if paper.get('pdf_url'):
                            st.link_button("📄 查看PDF", paper['pdf_url'], use_container_width=True)
                        
                        # ArXiv 页面链接（兼容两种字段名）
                        arxiv_link = paper.get('page_url') or paper.get('arxiv_url')
                        if arxiv_link:
                            st.link_button("🔗 arXiv页面", arxiv_link, use_container_width=True)
                       
                        # 使用唯一的 key 避免冲突
                        if st.button("💬 研读此文", key=f"chat_btn_{paper.get('arxiv_id')}_{idx}_{paper_idx}", use_container_width=True):
                            # 构建与 show_paper_detail_chat 中完全一致的选项文本格式
                            # 逻辑：f"{arxiv_id}: {title[:100]}"
                            p_title = paper.get('title', 'N/A')[:100]
                            p_id = paper.get('arxiv_id', 'N/A')
                            target_option = f"{p_id}: {p_title}"
                            
                            # 更新 Session State 中的选择框值
                            st.session_state['paper_selector'] = target_option
                            
                            # 弹出成功提示
                            st.toast(f"✅ 已选中: {p_title[:20]}...", icon="🎉")
                            st.toast("👉 请点击上方的 '单篇论文问答' 标签页开始对话", icon="👆")
                    # 摘要
                    if paper.get('abstract'):
                        st.markdown("**摘要:**")
                        st.text_area("", paper['abstract'], height=150, key=f"class_abstract_{idx}_{paper_idx}", disabled=True, label_visibility="collapsed")
                
            st.divider()

def show_paper_detail_chat():
    """显示单篇论文深度问答"""
    st.header("📖 单篇论文深度问答")
    
    if not st.session_state.papers:
        st.info("暂无论文数据，请先爬取论文")
        return
    
    if not st.session_state.llm_configured:
        st.warning("⚠️ 请先在侧边栏配置 LLM")
        return
    
    # 论文选择
    st.subheader("1️⃣ 选择论文")
    
    # 创建论文选项
    paper_options = {}
    for i, paper in enumerate(st.session_state.papers):
        title = paper.get('title', 'N/A')[:100]
        arxiv_id = paper.get('arxiv_id', 'N/A')
        option_text = f"{arxiv_id}: {title}"
        paper_options[option_text] = i
    
    # 添加空选项作为placeholder
    options_list = ["-- 请选择论文 --"] + list(paper_options.keys())
    
    selected_option = st.selectbox(
        "选择要深度问答的论文",
        options=options_list,
        index=0,  # 默认选中第一项（placeholder）
        key="paper_selector"
    )
    
    # 如果没有选择有效论文，直接返回
    if not selected_option or selected_option == "-- 请选择论文 --":
        st.info("👆 请先从上方下拉框中选择一篇论文")
        return
    
    selected_paper_idx = paper_options[selected_option]
    selected_paper = st.session_state.papers[selected_paper_idx]
    
    # 显示论文基本信息
    with st.expander("📋 论文基本信息", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**标题:** {selected_paper.get('title', 'N/A')}")
            st.markdown(f"**ArXiv ID:** {selected_paper.get('arxiv_id', 'N/A')}")
            
            authors = selected_paper.get('authors', [])
            if authors:
                st.markdown(f"**作者:** {', '.join(authors[:5])}")
                if len(authors) > 5:
                    st.markdown(f"*...等 {len(authors)} 位作者*")
            
            categories = selected_paper.get('categories', [])
            if categories:
                st.markdown(f"**分类:** {', '.join(categories)}")
        
        with col2:
            if selected_paper.get('pdf_url'):
                st.link_button("📄 查看PDF", selected_paper['pdf_url'], use_container_width=True)
            
            arxiv_url = selected_paper.get('page_url') or selected_paper.get('arxiv_url')
            if arxiv_url:
                st.link_button("🔗 arXiv页面", arxiv_url, use_container_width=True)
    
    st.divider()
    
    # 加载论文按钮
    st.subheader("2️⃣ 加载论文全文")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        load_button = st.button("🔄 加载论文全文", use_container_width=True, type="primary")
    
    with col2:
        force_reload = st.checkbox("强制重新下载", value=False)
    
    with col3:
        if st.session_state.current_paper_for_chat:
            if st.button("🗑️ 清空对话", use_container_width=True):
                st.session_state.paper_chat_messages = []
                st.session_state.current_paper_for_chat = None
                st.session_state.paper_chatbot = None
                st.rerun()
    
    # 检查论文是否变化
    paper_changed = (st.session_state.current_paper_for_chat and 
                     st.session_state.current_paper_for_chat.get('arxiv_id') != selected_paper.get('arxiv_id'))
    
    # 如果论文变化了，显示提示
    if paper_changed:
        st.warning(f"⚠️ 您选择了新的论文，请点击'加载论文全文'按钮重新加载")
    
    # 加载论文（只在点击按钮时触发）
    if load_button:
        with st.spinner("正在下载并处理PDF，这可能需要几分钟..."):
            # 创建或获取chatbot
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
                    st.error(f"创建问答机器人失败: {e}")
                    return
            
            # 加载论文
            try:
                success = st.session_state.paper_chatbot.load_paper(
                    selected_paper, 
                    force_download=force_reload
                )
                
                if success:
                    # 如果是切换到新论文，清空对话历史
                    if (st.session_state.current_paper_for_chat and 
                        st.session_state.current_paper_for_chat.get('arxiv_id') != selected_paper.get('arxiv_id')):
                        st.session_state.paper_chat_messages = []
                    
                    st.session_state.current_paper_for_chat = selected_paper
                    st.session_state.paper_chat_messages = []
                    st.success("✅ 论文加载成功！现在可以开始问答了")
                    
                    # 显示加载信息
                    if st.session_state.paper_chatbot.current_full_text:
                        text_length = len(st.session_state.paper_chatbot.current_full_text)
                        st.info(f"📄 已加载全文，共 {text_length:,} 字符")
                    else:
                        st.warning("⚠️ 全文加载失败，将仅使用摘要信息")
                else:
                    st.error("❌ 论文加载失败")
            except Exception as e:
                st.error(f"加载论文时出错: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    st.divider()
    
    # 问答界面
    st.subheader("3️⃣ 开始问答")
    
    if not st.session_state.current_paper_for_chat:
        st.info("💡 请先点击上方的 '加载论文全文' 按钮")
        return
    
    # 显示当前论文信息
    st.caption(f"📚 当前论文: {st.session_state.current_paper_for_chat.get('title', 'N/A')[:80]}...")
    
    # 示例问题（仅在对话为空时显示）
    if not st.session_state.paper_chat_messages:
        st.markdown("💡 **示例问题:**")
        example_col1, example_col2 = st.columns(2)
        
        with example_col1:
            if st.button("📋 这篇论文的核心贡献是什么？", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "这篇论文的核心贡献是什么？"
                })
                st.rerun()
            
            if st.button("🔬 使用了什么研究方法？", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "这篇论文使用了什么研究方法？"
                })
                st.rerun()
                
            if st.button("📚 列出主要参考文献", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "请列出这篇论文引用的主要参考文献，并简要说明其中最关键的几篇。"
                })
                st.rerun()
        
        with example_col2:
            if st.button("📊 实验结果如何？", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "这篇论文的实验结果如何？有什么亮点？"
                })
                st.rerun()
            
            if st.button("🎯 有什么局限性或未来工作？", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "这篇论文有什么局限性？作者提出了哪些未来工作方向？"
                })
                st.rerun()
                
            if st.button("🧠 用通俗语言解释全文", use_container_width=True):
                st.session_state.paper_chat_messages.append({
                    "role": "user", 
                    "content": "请用通俗易懂的语言（就像给初学者讲课一样）解释这篇论文的核心思想和主要内容。"
                })
                st.rerun()
        
        st.markdown("---")
    
    # 显示聊天历史
    for message in st.session_state.paper_chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 如果有未处理的用户消息，生成AI回复
    if (st.session_state.paper_chat_messages and 
        st.session_state.paper_chat_messages[-1]["role"] == "user"):
        
        user_question = st.session_state.paper_chat_messages[-1]["content"]
        
        # 生成AI回复并显示
        with st.chat_message("assistant"):
            with st.spinner("AI正在分析论文并思考..."):
                try:
                    response = st.session_state.paper_chatbot.chat(user_question)
                    st.write(response)
                    st.session_state.paper_chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"❌ 对话出错: {str(e)}"
                    st.write(error_msg)
                    st.session_state.paper_chat_messages.append({"role": "assistant", "content": error_msg})
    
    # 聊天输入框始终在最底部
    if prompt := st.chat_input("输入您关于这篇论文的问题..."):
        # 立即添加用户消息到历史
        st.session_state.paper_chat_messages.append({"role": "user", "content": prompt})
        # 重新运行以显示用户问题并生成AI回复
        st.rerun()


def show_instructions():
    """显示使用说明"""
    st.header("ℹ️ 使用说明")
    
    st.markdown("""
    ## 🚀 快速开始
    
    ### 1. 配置 LLM（可选）
    - 在左侧栏输入模型名称（如：gpt-4, gpt-5）
    - 点击 "连接LLM" 按钮
    - 等待连接成功提示
    - **注意**: 仅在使用 AI 分析和智能问答时需要
    
    ### 2. 爬取论文
    
    #### API 爬取（推荐）⭐
    - 选择 "🔧 API爬取（推荐）"
    - 选择日期模式：
      - **单个日期**: 爬取指定日期的所有论文
      - **日期范围**: 爬取一段时间的论文
      - **最新论文**: 获取最近提交的论文
    - 选择是否限制数量（建议不限制，获取全部）
    - 点击 "开始爬取"
    - 优点：**稳定可靠，避免 reCAPTCHA，支持日期选择**
    
    #### 网页爬取（备选）
    - 选择 "🌐 网页爬取"
    - 系统会自动爬取 **New submissions** 和 **Cross submissions**
    - 等待爬取完成（会显示实时进度）
    - **注意**: 可能遇到 reCAPTCHA 验证
    
    ### 3. AI 分析（可选）
    - 爬取完成后，点击 "AI分析" 按钮
    - 系统自动生成任务描述并智能分类
    - 查看 "数据可视化" 标签页查看分类结果
    
    ### 4. 导出数据
    - 点击 "导出Excel" 按钮
    - 系统生成包含所有数据的 Excel 文件
    - 点击下载按钮保存到本地
    
    ### 5. 智能问答
    - 切换到 "智能问答" 标签页
    - 输入问题，AI 会基于论文库回答
    
    ## 📋 支持的类别
    
    - 🖥️ **cs** - Computer Science（计算机科学）
    - 📐 **math** - Mathematics（数学）
    - ⚛️ **physics** - Physics（物理）
    - 🧬 **q-bio** - Quantitative Biology（定量生物学）
    - 💰 **q-fin** - Quantitative Finance（定量金融）
    - 📊 **stat** - Statistics（统计）
    - ⚡ **eess** - Electrical Engineering（电气工程）
    - 💹 **econ** - Economics（经济学）
    
    ## ⚙️ 技术说明
    
    ### 爬取方式
    - **API 爬取**: 使用 ArXiv 官方 API，稳定可靠
    - **网页爬取**: 从 ArXiv 网站爬取（`/list/{category}/new`）
    - **数据获取**: 自动提取论文详细信息（标题、摘要、作者等）
    
    ### 作者单位信息
    - **网页爬取**: 尝试从论文详情页的 meta 标签提取单位信息
    - **API 爬取**: ArXiv API 通常不包含单位信息
    - **注意**: 并非所有论文都包含单位信息，这是正常现象
    - **显示规则**: 
      - 有单位信息时：显示在"机构"字段
      - 无单位信息时：不显示机构字段
    
    ### 其他功能
    - **AI 分析**: 使用 LLM 生成任务描述并智能分类
    - **数据存储**: 自动保存到 `papers/` 目录
    - **Excel 导出**: 保存到 `exports/` 目录
    
    ## 💡 提示
    
    - **推荐使用 API 爬取**：更稳定，支持日期选择
    - 首次使用 AI 分析需先配置 LLM
    - 爬取大量论文可能需要较长时间
    - 单位信息取决于论文本身是否提供
    - 智能问答基于已爬取的论文库
    """)


if __name__ == "__main__":
    main()

