#!/usr/bin/env python3
"""
单篇论文深度问答模块
支持基于论文全文（标题、摘要、作者、正文）的智能对话
"""

from typing import Dict, List, Optional
from openai import OpenAI
from pdf_processor import PDFProcessor
import json


class PaperChatBot:
    def __init__(self, model_name: str = "gpt-4",
                 base_url: str = "https://yunwu.ai/v1",
                 api_key: str = "sk-5N0wwebNZWT1DkAMVkRTbjMrfRSKlO0q4crzwLwcoPhrL043"):
        """
        初始化单篇论文问答机器人
        
        Args:
            model_name: LLM模型名称
            base_url: API基础URL
            api_key: API密钥
        """
        self.model_name = model_name
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # 初始化PDF处理器
        self.pdf_processor = PDFProcessor()
        
        # 当前论文信息
        self.current_paper = None
        self.current_full_text = None
        self.conversation_history = []
        
        # 文本分块配置（用于处理超长文本）
        self.max_context_length = 100000  # 约25k tokens，为对话历史留出空间
        self.max_conversation_history = 10  # 最多保留10轮对话
        
        # 缓存构建好的论文上下文，避免重复构建
        self._cached_paper_context = None
    
    def load_paper(self, paper: Dict, force_download: bool = False) -> bool:
        """
        加载论文并提取全文
        
        Args:
            paper: 论文信息字典（包含arxiv_id, title, abstract等）
            force_download: 是否强制重新下载PDF
        
        Returns:
            是否加载成功
        """
        arxiv_id = paper.get('arxiv_id')
        if not arxiv_id:
            print("❌ 论文缺少arxiv_id")
            return False
        
        print(f"\n{'='*60}")
        print(f"📚 加载论文: {paper.get('title', arxiv_id)}")
        print(f"{'='*60}")
        
        # 保存基本信息
        self.current_paper = paper
        
        # 尝试获取缓存的文本（除非强制重新下载）
        if not force_download:
            cached_text = self.pdf_processor.get_cached_text(arxiv_id)
            if cached_text:
                self.current_full_text = cached_text
                print(f"✅ 使用缓存的全文 ({len(cached_text)} 字符)")
                self._prepare_context()
                return True
            else:
                print(f"🔍 未找到缓存，将下载PDF")
        else:
            print(f"🔄 强制重新下载")
        
        # 下载并提取PDF全文
        pdf_url = paper.get('pdf_url')
        result = self.pdf_processor.process_paper(arxiv_id, pdf_url)
        
        if result['success']:
            self.current_full_text = result['full_text']
            self._prepare_context()
            return True
        else:
            print(f"❌ 加载论文失败: {result.get('error', 'Unknown error')}")
            # 即使PDF加载失败，也可以基于摘要进行问答
            print("⚠️  将仅使用摘要信息进行问答")
            self.current_full_text = None
            self._prepare_context()
            return True  # 仍然返回True，允许基于摘要问答
    
    def _prepare_context(self):
        """准备论文上下文信息"""
        # 清空对话历史
        self.conversation_history = []
        
        # 清空缓存的上下文
        self._cached_paper_context = None
        
        print(f"\n📋 论文信息:")
        print(f"  标题: {self.current_paper.get('title', 'N/A')}")
        print(f"  作者: {', '.join(self.current_paper.get('authors', [])[:3])}...")
        print(f"  ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
        
        if self.current_full_text:
            print(f"  全文长度: {len(self.current_full_text)} 字符")
            # 检查是否需要截断
            if len(self.current_full_text) > self.max_context_length:
                print(f"  ⚠️  全文过长，将使用前 {self.max_context_length} 字符")
        else:
            print(f"  摘要长度: {len(self.current_paper.get('abstract', ''))} 字符")
        
        print(f"\n💬 现在可以开始针对这篇论文进行问答了！")
    
    def _build_paper_context(self) -> str:
        """
        构建论文上下文信息（带缓存）
        
        Returns:
            论文上下文字符串
        """
        # 如果已经构建过，直接返回缓存
        if self._cached_paper_context is not None:
            return self._cached_paper_context
        
        context_parts = []
        
        # 基本信息
        context_parts.append("=" * 60)
        context_parts.append("论文信息")
        context_parts.append("=" * 60)
        context_parts.append(f"标题: {self.current_paper.get('title', 'N/A')}")
        context_parts.append(f"ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
        
        # 作者
        authors = self.current_paper.get('authors', [])
        if authors:
            context_parts.append(f"作者: {', '.join(authors)}")
        
        # 机构
        affiliations = self.current_paper.get('affiliations', [])
        if affiliations and any(a for a in affiliations if a and a.strip()):
            valid_affs = [a for a in affiliations if a and a.strip()]
            context_parts.append(f"机构: {'; '.join(set(valid_affs))}")
        
        # 分类
        categories = self.current_paper.get('categories', [])
        if categories:
            context_parts.append(f"分类: {', '.join(categories)}")
        
        # 发布日期
        if self.current_paper.get('published'):
            context_parts.append(f"发布日期: {self.current_paper.get('published')}")
        
        context_parts.append("")
        
        # 摘要
        abstract = self.current_paper.get('abstract_cn') or self.current_paper.get('abstract', '')
        if abstract:
            context_parts.append("=" * 60)
            context_parts.append("摘要")
            context_parts.append("=" * 60)
            context_parts.append(abstract)
            context_parts.append("")
        
        # 全文（如果有）
        if self.current_full_text:
            context_parts.append("=" * 60)
            context_parts.append("论文全文")
            context_parts.append("=" * 60)
            
            # 截断过长的文本
            full_text = self.current_full_text
            if len(full_text) > self.max_context_length:
                full_text = full_text[:self.max_context_length]
                context_parts.append("(注: 全文过长，已截取前半部分)")
                context_parts.append("")
            
            context_parts.append(full_text)
        
        # 缓存构建好的上下文
        self._cached_paper_context = "\n".join(context_parts)
        return self._cached_paper_context
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的学术论文分析专家。你正在帮助用户深入理解一篇具体的学术论文。

你的任务：
1. 基于提供的论文全文（包括标题、摘要、作者、正文等）回答用户的问题
2. 提供准确、详细、有深度的回答
3. 引用论文中的具体内容来支持你的回答
4. 如果问题无法从论文中找到答案，请明确说明
5. 可以解释技术概念、分析研究方法、总结关键发现等
6. 支持中英文问答

你可以帮助用户：
- 理解论文的核心贡献和创新点
- 分析研究方法和实验设计
- 解释技术细节和算法
- 总结关键结论和发现
- 评估论文的优缺点
- 比较与其他研究的异同
- 解答任何关于这篇论文的问题

请保持专业、准确、有条理的回答风格。"""
    
    def chat(self, user_message: str) -> str:
        """
        与用户对话
        
        Args:
            user_message: 用户消息
        
        Returns:
            AI回复
        """
        if not self.current_paper:
            return "❌ 请先加载论文后再进行问答"
        
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统提示词
            messages.append({
                "role": "system",
                "content": self._get_system_prompt()
            })
            
            # ⭐ 重要修改：每次对话都添加论文上下文，确保AI始终能访问论文全文
            # 这样即使对话历史很长，AI也能正确回答关于论文的基本问题
            paper_context = self._build_paper_context()
            messages.append({
                "role": "system",
                "content": f"以下是用户想要了解的论文内容：\n\n{paper_context}"
            })
            
            # 添加对话历史（最近10轮对话，避免上下文过长）
            # 只保留最近的对话，因为论文全文已经在上面了
            recent_history = self.conversation_history[-self.max_conversation_history:] if len(self.conversation_history) > self.max_conversation_history else self.conversation_history
            messages.extend(recent_history)
            
            # 添加当前用户消息
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # 调用LLM
            print("  🤔 AI正在思考...", end='', flush=True)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            
            print("\r  ✓ AI回复完成     ")
            
            ai_response = response.choices[0].message.content.strip()
            
            # 更新对话历史
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ai_response
            
        except Exception as e:
            error_msg = f"❌ 对话出错: {str(e)}"
            print(f"\n{error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    def start_interactive_chat(self):
        """启动交互式对话"""
        if not self.current_paper:
            print("❌ 请先加载论文")
            return
        
        print(f"\n{'='*60}")
        print("💬 单篇论文深度问答已启动")
        print(f"{'='*60}")
        print(f"📚 当前论文: {self.current_paper.get('title', 'N/A')[:80]}...")
        print(f"🔗 ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
        
        if self.current_full_text:
            print(f"✅ 已加载全文 ({len(self.current_full_text)} 字符)")
        else:
            print(f"⚠️  仅使用摘要信息")
        
        print(f"\n{'='*60}")
        print("💡 提示:")
        print("  - 输入 'quit', 'exit' 或 '退出' 结束对话")
        print("  - 输入 'clear' 清空对话历史")
        print("  - 输入 'info' 查看论文信息")
        print(f"{'='*60}\n")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("👤 您: ").strip()
                
                # 检查命令
                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("\n👋 结束对话，感谢使用！")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("\n✅ 对话历史已清空\n")
                    continue
                
                if user_input.lower() == 'info':
                    print(f"\n{'='*60}")
                    print("📋 论文信息")
                    print(f"{'='*60}")
                    print(f"标题: {self.current_paper.get('title', 'N/A')}")
                    print(f"ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
                    print(f"作者: {', '.join(self.current_paper.get('authors', [])[:5])}")
                    if self.current_full_text:
                        print(f"全文长度: {len(self.current_full_text)} 字符")
                    print(f"{'='*60}\n")
                    continue
                
                if not user_input:
                    print("请输入您的问题...\n")
                    continue
                
                # 对话
                ai_response = self.chat(user_input)
                print(f"\n🤖 助手: {ai_response}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 结束对话，感谢使用！")
                break
            except Exception as e:
                print(f"\n❌ 出现错误: {e}\n")
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_history = []
        # 保留缓存的论文上下文
        print("✅ 对话历史已清空（论文内容仍保留）")
    
    def save_conversation(self, filepath: str):
        """
        保存对话历史到文件
        
        Args:
            filepath: 保存路径
        """
        data = {
            'paper': self.current_paper,
            'conversation': self.conversation_history
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 对话历史已保存到: {filepath}")


def main():
    """测试用主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='单篇论文深度问答')
    parser.add_argument('--arxiv_id', required=True, help='ArXiv ID')
    parser.add_argument('--model', default='gpt-4', help='LLM模型')
    parser.add_argument('--papers_file', help='论文数据JSON文件（可选）')
    
    args = parser.parse_args()
    
    # 创建问答机器人
    chatbot = PaperChatBot(model_name=args.model)
    
    # 加载论文
    paper = None
    if args.papers_file:
        # 从文件加载
        with open(args.papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        # 查找指定论文
        for p in papers:
            if p.get('arxiv_id') == args.arxiv_id:
                paper = p
                break
    
    if not paper:
        # 创建基本论文信息
        paper = {
            'arxiv_id': args.arxiv_id,
            'title': f'ArXiv Paper {args.arxiv_id}',
            'pdf_url': f'https://arxiv.org/pdf/{args.arxiv_id}.pdf'
        }
    
    # 加载论文
    if chatbot.load_paper(paper):
        # 启动交互式对话
        chatbot.start_interactive_chat()
    else:
        print("❌ 论文加载失败")


if __name__ == "__main__":
    main()
