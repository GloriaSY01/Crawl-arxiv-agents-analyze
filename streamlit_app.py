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
    tab1, tab2, tab3, tab4 = st.tabs(["📚 论文列表", "📊 数据可视化", "💬 智能问答", "ℹ️ 使用说明"])
    
    with tab1:
        show_papers_list()
    
    with tab2:
        show_visualization()
    
    with tab3:
        show_chat()
    
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


def show_papers_list():
    """显示论文列表"""
    st.header("📚 已爬取的论文")
    
    if not st.session_state.papers:
        st.info("暂无论文数据，请先爬取论文")
        return
    
    # 搜索和过滤
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 搜索论文", placeholder="输入关键词搜索标题或摘要...")
    with col2:
        sort_by = st.selectbox("排序方式", ["最新", "标题"])
    
    # 过滤论文
    filtered_papers = st.session_state.papers
    if search_term:
        filtered_papers = [
            p for p in filtered_papers 
            if search_term.lower() in p.get('title', '').lower() 
            or search_term.lower() in p.get('abstract', '').lower()
        ]
    
    st.write(f"显示 {len(filtered_papers)} 篇论文")
    
    # 显示论文
    for idx, paper in enumerate(filtered_papers, 1):
        with st.expander(f"📄 {idx}. {paper.get('title', '无标题')}", expanded=False):
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
                
                # 显示统计信息
                st.metric("作者数", len(paper.get('authors', [])))
                st.metric("分类数", len(paper.get('categories', [])))
            
            # 摘要
            if paper.get('abstract'):
                st.markdown("**摘要:**")
                st.text_area("", paper['abstract'], height=150, key=f"abstract_{idx}", disabled=True, label_visibility="collapsed")


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
        
        # 颜色映射
        import colorsys
        num_categories = len(classified_papers)
        colors = []
        for i in range(num_categories):
            hue = i / num_categories
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            colors.append(f'rgb({int(rgb[0]*255)},{int(rgb[1]*255)},{int(rgb[2]*255)})')
        
        category_colors = {cat: colors[i] for i, cat in enumerate(classified_papers.keys())}
        
        # 添加节点和边
        node_info = {}  # 存储节点信息用于悬停
        node_hover_texts = {}  # 存储每个节点的悬停文本
        node_urls = {}  # 存储节点URL（用于点击）
        
        node_list = []  # 按顺序存储所有节点ID
        
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
                    hover_text += f"任务: {task_desc}<br>"
                    hover_text += f"分类: {category}"
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
        
        # 使用力导向布局
        try:
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        except Exception as layout_error:
            print(f"[ERROR] 布局计算失败: {layout_error}")
            # 尝试使用更简单的布局
            try:
                pos = nx.circular_layout(G)
                print("[DEBUG] 使用圆形布局作为备选")
            except:
                print("[ERROR] 所有布局方法都失败")
                return None
        
        # 提取边的坐标
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # 创建边的轨迹
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
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
            
            # 节点标签（只显示分类名称）
            if node_info.get(node, {}).get('type') == 'category':
                node_labels.append(node_info[node].get('name', '')[:20])
            else:
                node_labels.append('')
            
            # 悬停文本
            hover_texts_ordered.append(node_hover_texts.get(node, ''))
            
            # 节点大小和颜色
            if node.startswith('CAT_'):
                # 分类节点
                cat_name = node.replace('CAT_', '')
                node_sizes_ordered.append(30)
                node_colors_ordered.append(category_colors.get(cat_name, colors[0]))
            else:
                # 论文节点
                node_sizes_ordered.append(15)
                # 从node_info中获取分类
                paper_category = node_info.get(node, {}).get('category', '')
                node_colors_ordered.append(category_colors.get(paper_category, colors[0]))
        
        # 创建节点的轨迹
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_labels,
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            hovertext=hover_texts_ordered,
            marker=dict(
                size=node_sizes_ordered,
                color=node_colors_ordered,
                line=dict(width=2, color='white')
            )
        )
        
        # 创建图形
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text='论文分类/聚类网络图',
                    font=dict(size=16)
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[
                    dict(
                        text="💡 鼠标悬停查看论文详情，点击节点打开论文网页",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor="left", yanchor="bottom",
                        font=dict(size=12, color="#666")
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                height=600
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
            st.caption("💡 提示：鼠标悬停查看论文详情。下方表格中可点击链接打开论文网页")
            
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
                        st.plotly_chart(network_fig, use_container_width=True)
                        
                        # 添加论文链接表格（方便点击打开）
                        st.subheader("📋 论文链接列表")
                        with st.expander("点击展开查看所有论文链接", expanded=False):
                            for category, papers in st.session_state.classified_papers.items():
                                st.markdown(f"### {category} ({len(papers)} 篇)")
                                for paper in papers:
                                    title = paper.get('title', 'N/A')
                                    arxiv_url = paper.get('arxiv_url') or paper.get('page_url', '')
                                    if arxiv_url:
                                        st.markdown(f"- [{title}]({arxiv_url})")
                                    else:
                                        st.markdown(f"- {title} (无链接)")
                                st.divider()
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
        
        # 分类卡片
        st.subheader("📋 分类详情")
        cols = st.columns(3)
        for idx, (category, papers) in enumerate(st.session_state.classified_papers.items()):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{category}</h3>
                    <h1>{len(papers)}</h1>
                    <p>篇论文</p>
                </div>
                """, unsafe_allow_html=True)
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


def show_chat():
    """显示智能问答"""
    st.header("💬 智能问答")
    
    if not st.session_state.papers:
        st.info("暂无论文数据，请先爬取论文")
        return
    
    if not st.session_state.llm_configured:
        st.warning("⚠️ 请先配置 LLM")
        return
    
    # 初始化聊天历史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 显示聊天历史
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 聊天输入
    if prompt := st.chat_input("输入您的问题..."):
        # 添加用户消息
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # 生成AI回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = chat_with_papers(prompt)
                st.write(response)
        
        st.session_state.chat_history.append({"role": "assistant", "content": response})


def chat_with_papers(message: str) -> str:
    """与论文库对话"""
    try:
        # 构建上下文
        context_papers = st.session_state.papers[:10]
        context = "当前论文库：\n"
        for i, paper in enumerate(context_papers, 1):
            context += f"{i}. {paper.get('title', '无标题')}\n"
            if 'task_description' in paper:
                context += f"   任务: {paper['task_description']}\n"
        
        prompt = f"""{context}

用户问题: {message}

请基于论文库回答用户的问题。"""
        
        response = st.session_state.llm_client.chat.completions.create(
            model=st.session_state.llm_model,
            messages=[
                {"role": "system", "content": "你是一个专业的学术论文分析助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 对话失败: {str(e)}"


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

