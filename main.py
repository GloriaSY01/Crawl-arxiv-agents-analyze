import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        description='ArXiv Intelligent Q&A System'
    )

    # Simplified parameters, mainly for the web interface
    parser.add_argument(
        '--web_port', type=int, default=8080,
        help='Web server port (default: 8080)'
    )
    parser.add_argument(
        '--console', action='store_true',
        help='Use console mode (requires more parameters)'
    )
    parser.add_argument(
        '--chat_file',
        help='Start Q&A using an existing papers file'
    )

    # API configuration parameters
    parser.add_argument(
        '--base_url', type=str, default=None,
        help='API base URL (required)'
    )
    parser.add_argument(
        '--api_key', type=str, default=None,
        help='API key (required)'
    )

    # Full parameters for console mode (only needed with --console)
    if '--console' in sys.argv:
        # Add all original crawl parameters
        parser.add_argument(
            '--categories', '-c', nargs='+',
            help='Subject categories, e.g.: cs.AI cs.LG'
        )
        parser.add_argument(
            '--author', '-a',
            help='Author search'
        )
        parser.add_argument(
            '--keywords-all', nargs='+',
            help='All keywords must be included (AND)'
        )
        parser.add_argument(
            '--keywords-any', nargs='+',
            help='Any keyword included (OR)'
        )
        parser.add_argument(
            '--keywords-not', nargs='+',
            help='Keywords to exclude (NOT)'
        )
        parser.add_argument(
            '--title-keywords', nargs='+',
            help='Keywords to search in title only'
        )
        parser.add_argument(
            '--abstract-keywords', nargs='+',
            help='Keywords to search in abstract only'
        )
        parser.add_argument(
            '--title-abstract-keywords', nargs='+',
            help='Keywords to search in title or abstract'
        )
        parser.add_argument(
            '--keywords', '-k',
            help='Simple keyword search'
        )
        parser.add_argument(
            '--title', '-t',
            help='Title search'
        )
        parser.add_argument(
            '--start-date',
            help='Start date (YYYYMMDD)'
        )
        parser.add_argument(
            '--end-date',
            help='End date (YYYYMMDD)'
        )
        parser.add_argument(
            '--date-type',
            choices=['submittedDate', 'lastUpdatedDate'],
            default='submittedDate',
            help='Date type'
        )
        parser.add_argument(
            '--max-results', '-m', type=int, default=100,
            help='Maximum crawl results'
        )
        parser.add_argument(
            '--batch-size', '-b', type=int, default=50,
            help='Batch size per crawl'
        )
        parser.add_argument(
            '--delay', '-d', type=float, default=1.0,
            help='Request delay in seconds'
        )
        parser.add_argument(
            '--sort-by',
            choices=['relevance', 'lastUpdatedDate', 'submittedDate'],
            default='submittedDate',
            help='Sort field'
        )
        parser.add_argument(
            '--sort-order', choices=['ascending', 'descending'],
            default='descending',
            help='Sort order'
        )
        parser.add_argument(
            '--output', '-o', required=True,
            help='Output filename'
        )
        parser.add_argument(
            '--show-query',
            action='store_true',
            help='Show constructed API query string'
        )
        parser.add_argument(
            '--show-abstracts', action='store_true',
            help='Display abstracts in terminal output'
        )
        parser.add_argument(
            '--abstract-length', type=int, default=200,
            help='Max characters to display for abstracts'
        )
        parser.add_argument(
            '--translate_llm', required=True,
            help='LLM model name for translation'
        )
        parser.add_argument(
            '--port', type=int, default=9000,
            help='LLM server port'
        )
        parser.add_argument(
            '--batchsize', type=int, default=5,
            help='Translation concurrency'
        )
        parser.add_argument(
            '--max_load_files', type=int, default=10,
            help='Maximum number of papers to load simultaneously'
        )

    args = parser.parse_args()

    # Validate required API configuration parameters
    if args.base_url is None:
        parser.error("--base_url is required. Please provide the API base URL")
    if args.api_key is None:
        parser.error("--api_key is required. Please provide the API key")

    if args.console:
        # Console mode: crawl -> translate -> Q&A
        print("🖥️ Starting console mode...")

        # Lazy imports, only when needed
        from chat import ask
        from crawl import crawl
        from translate import translate

        if not args.chat_file:
            print("Starting to crawl arXiv papers...")
            crawl(args)
            print("Starting to translate abstracts...")
            translate(args)

        print("Starting Q&A mode...")
        ask(args)
    else:
        # Web mode: launch Streamlit UI
        print("🌐 Launching Streamlit Web UI...")
        print("📚 Browser will open: http://localhost:8501")
        print("\n" + "="*60)

        # Pass API config to Streamlit via environment variables
        env = os.environ.copy()
        env['YUNWU_API_BASE'] = args.base_url
        env['YUNWU_API_KEY'] = args.api_key

        try:
            import subprocess

            # Use python -m streamlit; add headless mode to avoid email prompt
            result = subprocess.run([
                sys.executable, '-m', 'streamlit', 'run',
                'streamlit_app.py',
                '--server.headless', 'true'
            ], env=env)

            if result.returncode != 0:
                print("\n❌ Streamlit failed to start")
                print("Please run manually: streamlit run streamlit_app.py")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nPlease ensure Streamlit is installed:")
            print("  pip install streamlit")
            print("\nOr run manually:")
            print("  streamlit run streamlit_app.py")


if __name__ == "__main__":
    main()

"""
Usage Examples:

1. Full pipeline (crawl + translate + Q&A):
python main.py \
    --abstract-keywords "tool use" "reinforcement learning" \
    --start-date 20250501 \
    --end-date 20250805 \
    --batchsize 10 \
    --max-results 100 \
    --output tool-rl/output.json \
    --translate_llm "Qwen/Qwen3-32B" \
    --port 10006

2. Q&A only (based on existing file):
python main.py \
    --chat_file tool-rl/output.json \
    --translate_llm "Qwen/Qwen3-32B" \
    --port 10006
"""
