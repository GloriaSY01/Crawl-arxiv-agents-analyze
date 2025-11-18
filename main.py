import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(description='ArXiv论文智能问答系统')
    
    # 简化的参数，主要用于Web界面
    parser.add_argument('--web_port', type=int, default=8080,
                       help='网页服务器端口 (默认: 8080)')
    parser.add_argument('--console', action='store_true',
                       help='使用命令行模式（需要提供更多参数）')
    parser.add_argument('--chat_file', 
                       help='直接使用已有论文文件启动问答')
    
    # API配置参数
    parser.add_argument('--base_url', type=str, default=None,
                       help='API基础URL (必需)')
    parser.add_argument('--api_key', type=str, default=None,
                       help='API密钥 (必需)')
    
    # 命令行模式的完整参数（仅在--console时需要）
    if '--console' in sys.argv:
        # 添加所有原有的爬取参数
        parser.add_argument('--categories', '-c', nargs='+', 
                           help='学科分类，如: cs.AI cs.LG')
        parser.add_argument('--author', '-a', 
                           help='作者搜索')
        parser.add_argument('--keywords-all', nargs='+',
                           help='所有关键词都必须包含 (AND关系)')
        parser.add_argument('--keywords-any', nargs='+',
                           help='任一关键词包含即可 (OR关系)')
        parser.add_argument('--keywords-not', nargs='+',
                           help='不能包含的关键词 (NOT关系)')
        parser.add_argument('--title-keywords', nargs='+',
                           help='仅在标题中搜索的关键词')
        parser.add_argument('--abstract-keywords', nargs='+',
                           help='仅在摘要中搜索的关键词')
        parser.add_argument('--title-abstract-keywords', nargs='+',
                           help='在标题或摘要中搜索的关键词')
        parser.add_argument('--keywords', '-k', 
                           help='简单关键词搜索')
        parser.add_argument('--title', '-t', 
                           help='标题搜索')
        parser.add_argument('--start-date', 
                           help='开始日期 (YYYYMMDD格式)')
        parser.add_argument('--end-date', 
                           help='结束日期 (YYYYMMDD格式)')
        parser.add_argument('--date-type', choices=['submittedDate', 'lastUpdatedDate'],
                           default='submittedDate',
                           help='日期类型')
        parser.add_argument('--max-results', '-m', type=int, default=100,
                           help='最大爬取数量')
        parser.add_argument('--batch-size', '-b', type=int, default=50,
                           help='每批爬取数量')
        parser.add_argument('--delay', '-d', type=float, default=1.0,
                           help='请求间隔秒数')
        parser.add_argument('--sort-by', choices=['relevance', 'lastUpdatedDate', 'submittedDate'],
                           default='submittedDate',
                           help='排序字段')
        parser.add_argument('--sort-order', choices=['ascending', 'descending'],
                           default='descending',
                           help='排序顺序')
        parser.add_argument('--output', '-o', required=True,
                           help='输出文件名')
        parser.add_argument('--show-query', action='store_true',
                           help='显示构建的API查询字符串')
        parser.add_argument('--show-abstracts', action='store_true',
                           help='在终端输出中显示文章摘要')
        parser.add_argument('--abstract-length', type=int, default=200,
                           help='显示摘要的最大字符数')
        parser.add_argument('--translate_llm', required=True,
                           help='用于翻译的LLM模型名称')
        parser.add_argument('--port', type=int, default=9000,
                           help='LLM服务器端口')
        parser.add_argument('--batchsize', type=int, default=5,
                           help='翻译并发数量')
        parser.add_argument('--max_load_files', type=int, default=10,
                           help='最大同时加载的论文数量')

    args = parser.parse_args()
    
    # 验证必需的API配置参数
    if args.base_url is None:
        parser.error("--base_url 参数是必需的，请提供 API 基础 URL")
    if args.api_key is None:
        parser.error("--api_key 参数是必需的，请提供 API 密钥")
    
    if args.console:
        # 命令行模式：执行完整的爬取->翻译->问答流程
        print("🖥️ 启动命令行模式...")
        
        # 延迟导入，只在需要时才导入
        from chat import ask
        from crawl import crawl
        from translate import translate
        
        if not args.chat_file:
            print("开始爬取ArXiv文章...")
            crawl(args)
            print("开始翻译摘要...")
            translate(args)
        
        print("开始问答模式...")
        ask(args)
    else:
        # Web模式：启动Streamlit界面
        print("🌐 启动Streamlit Web界面...")
        print(f"📚 浏览器将自动打开: http://localhost:8501")
        print("\n" + "="*60)
        
        # 将API配置传递给Streamlit（通过环境变量）
        env = os.environ.copy()
        env['YUNWU_API_BASE'] = args.base_url
        env['YUNWU_API_KEY'] = args.api_key
        
        try:
            import subprocess
            
            # 使用 python -m streamlit 更可靠，添加 headless 模式避免邮箱提示
            result = subprocess.run([
                sys.executable, '-m', 'streamlit', 'run', 
                'streamlit_app.py',
                '--server.headless', 'true'
            ], env=env)
            
            if result.returncode != 0:
                print("\n❌ Streamlit 启动失败")
                print("请手动运行: streamlit run streamlit_app.py")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            print("\n请确保已安装 Streamlit:")
            print("  pip install streamlit")
            print("\n或手动运行:")
            print("  streamlit run streamlit_app.py")


if __name__ == "__main__":
    main()

"""
使用示例：

1. 完整流程（爬取 + 翻译 + 问答）：
python main.py \
    --abstract-keywords "tool use" "reinforcement learning" \
    --start-date 20250501 \
    --end-date 20250805 \
    --batchsize 10 \
    --max-results 100 \
    --output tool-rl/output.json \
    --translate_llm "Qwen/Qwen3-32B" \
    --port 10006

2. 仅问答模式（基于现有文件）：
python main.py \
    --chat_file tool-rl/output.json \
    --translate_llm "Qwen/Qwen3-32B" \
    --port 10006
"""