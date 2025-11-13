import json
import argparse
from typing import List, Dict

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai库未安装。请运行: pip install openai")
    OpenAI = None


class ArxivChatBot:
    def __init__(self, model_name: str, port: int, host: str = "0.0.0.0", 
                 base_url: str = None, 
                 api_key: str = None):
        """
        初始化问答机器人
        
        Args:
            model_name: LLM模型名称
            port: 服务端口
            host: 服务地址
            base_url: API基础URL
            api_key: API密钥
        """
        if OpenAI is None:
            raise ImportError("openai库未安装。请运行: pip install openai")
        
        if base_url is None:
            raise ValueError("base_url 参数不能为 None，请提供 API 基础 URL")
        if api_key is None:
            raise ValueError("api_key 参数不能为 None，请提供 API 密钥")
            
        self.model_name = model_name
        self.host = host
        self.port = port
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        self.papers = []
        self.conversation_history = []
        
    def load_papers(self, papers_data: List[Dict]) -> None:
        """
        加载文章数据
        
        Args:
            papers_data: 包含文章信息的列表
        """
        self.papers = papers_data
        print(f"已加载 {len(self.papers)} 篇文章")
        
        # 统计有摘要的文章数量
        papers_with_abstracts = [p for p in self.papers if p.get('abstract')]
        papers_with_cn_abstracts = [p for p in self.papers if p.get('abstract_cn')]
        
        print(f"其中 {len(papers_with_abstracts)} 篇有英文摘要")
        print(f"其中 {len(papers_with_cn_abstracts)} 篇有中文摘要")
        
    def build_context_prompt(self) -> str:
        """
        构建包含所有文章摘要的上下文提示
        
        Returns:
            包含文章信息的上下文字符串
        """
        context_parts = []
        context_parts.append("以下是相关的学术论文摘要信息，请基于这些内容回答用户的问题：\n")
        
        for i, paper in enumerate(self.papers, 1):
            context_parts.append(f"=== 论文 {i} ===")
            context_parts.append(f"标题: {paper.get('title', 'No title')}")
            context_parts.append(f"ArXiv ID: {paper.get('arxiv_id', 'No ID')}")
            context_parts.append(f"作者: {', '.join(paper.get('authors', []))}")
            context_parts.append(f"分类: {', '.join(paper.get('categories', []))}")
            context_parts.append(f"发布时间: {paper.get('published', 'No date')}")
            
            # 优先使用中文摘要，如果没有则使用英文摘要
            abstract = paper.get('abstract_cn') or paper.get('abstract', 'No abstract')
            context_parts.append(f"摘要: {abstract}")
            context_parts.append("")  # 空行分隔
            
        return "\n".join(context_parts)
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        Returns:
            系统提示词字符串
        """
        return """你是一个专业的学术论文分析助手。你的任务是基于提供的ArXiv论文摘要来回答用户的问题。

请遵循以下原则：
1. 仅基于提供的论文摘要内容回答问题
2. 如果问题无法从提供的摘要中找到答案，请明确说明
3. 回答时可以引用具体的论文标题和作者
4. 保持专业、准确、有条理的回答风格
5. 如果用户询问特定论文，请提供ArXiv ID以便查找
6. 可以对多篇论文进行对比分析
7. 支持中英文问答

你可以帮助用户：
- 总结论文的主要贡献
- 分析研究方法和技术
- 比较不同论文的异同
- 查找特定主题的相关论文
- 解释技术概念和术语"""

    def chat_with_user(self, user_input: str) -> str:
        """
        与用户进行对话
        
        Args:
            user_input: 用户输入
            
        Returns:
            AI回复
        """
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统提示词
            messages.append({
                "role": "system", 
                "content": self.get_system_prompt()
            })
            
            # 添加文章上下文（只在第一次或者需要时添加）
            if not self.conversation_history:
                context = self.build_context_prompt()
                messages.append({
                    "role": "system",
                    "content": context
                })
            
            # 添加对话历史（保持最近的对话）
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
            messages.extend(recent_history)
            
            # 添加当前用户输入
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            return f"抱歉，处理您的请求时出现错误: {e}"
    
    def start_interactive_chat(self):
        """
        启动交互式对话
        """
        print("\n" + "="*60)
        print("🤖 ArXiv论文助手已启动！")
        print("="*60)
        print(f"📚 已加载 {len(self.papers)} 篇论文")
        print("💬 您可以询问关于这些论文的任何问题")
        print("🔍 支持主题搜索、论文对比、技术分析等")
        print("📝 输入 'quit', 'exit' 或 '退出' 来结束对话")
        print("="*60)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n👤 您: ").strip()
                
                # 检查退出命令
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("\n👋 再见！感谢使用ArXiv论文助手！")
                    break
                
                if not user_input:
                    print("请输入您的问题...")
                    continue
                
                # 显示AI正在思考
                print("\n🤔 AI正在分析...")
                
                # 获取AI回复
                ai_response = self.chat_with_user(user_input)
                
                # 显示AI回复
                print(f"\n🤖 助手: {ai_response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！感谢使用ArXiv论文助手！")
                break
            except Exception as e:
                print(f"\n❌ 出现错误: {e}")
                print("请重试或输入 'quit' 退出")


def ask(args):
    """
    问答函数，基于爬虫输出的文件进行问答
    
    Args:
        args: 包含配置参数的对象，应该有以下属性：
            - output: 输入文件路径（爬虫输出的JSON文件）
            - translate_llm: LLM模型名称
            - port: 服务端口
            - max_load_files: 最大同时加载文件数（可选）
    """
    input_file = args.output
    
    print(f"\n=== 启动问答模式 ===")
    print(f"读取文件: {input_file}")
    print(f"使用模型: {args.translate_llm}")
    print(f"服务地址: http://0.0.0.0:{args.port}")
    
    # 检查是否有max_load_files参数
    max_load_files = getattr(args, 'max_load_files', None)
    if max_load_files:
        print(f"最大同时加载: {max_load_files} 篇论文")
    
    # 读取JSON文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"成功读取文件，包含 {len(papers)} 篇文章")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 为每篇论文初始化conversation字段
    for i, paper in enumerate(papers):
        if 'conversation' not in paper:
            paper['conversation'] = []
        # 确保每篇论文有唯一且稳定的ID  
        paper['_paper_id'] = i + 1
    
    # 创建聊天机器人
    try:
        base_url = getattr(args, 'base_url', None)
        api_key = getattr(args, 'api_key', None)
        if base_url is None or api_key is None:
            raise ValueError("缺少必需的参数: base_url 和 api_key 必须通过命令行参数提供")
        chatbot = ArxivChatBot(
            model_name=args.translate_llm,
            port=args.port,
            base_url=base_url,
            api_key=api_key
        )
        
        # 加载文章数据
        chatbot.load_papers(papers)
        
        # 启动交互式对话
        chatbot.start_interactive_chat()
        
    except Exception as e:
        print(f"❌ 初始化聊天机器人失败: {e}")
        return


def main():
    """
    测试用的主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ArXiv论文问答助手')
    parser.add_argument('--output', required=True, help='论文数据JSON文件路径')
    parser.add_argument('--translate_llm', required=True, help='LLM模型名称')
    parser.add_argument('--port', type=int, default=5000, help='LLM服务端口')
    
    args = parser.parse_args()
    ask(args)


if __name__ == "__main__":
    main()
