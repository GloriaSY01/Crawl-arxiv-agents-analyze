#!/usr/bin/env python3
"""
Deep Q&A module for a single paper
Supports intelligent dialogue based on the full paper
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
        Initialize the single-paper Q&A bot
        
        Args:
            model_name: Name of the LLM model
            base_url: API base URL
            api_key: API key
        """
        self.model_name = model_name
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Initialize PDF processor
        self.pdf_processor = PDFProcessor()
        
        # Current paper info
        self.current_paper = None
        self.current_full_text = None
        self.conversation_history = []
        
        # Text chunking config (for handling long text)
        self.max_context_length = 100000  # ~25k tokens; keep room for history
        self.max_conversation_history = 10  # keep at most 10 turns
        
        # Cache the built paper context to avoid rebuilding
        self._cached_paper_context = None
    
    def load_paper(self, paper: Dict, force_download: bool = False) -> bool:
        """
        Load the paper and extract full text
        
        Args:
            paper: Paper info dict (includes arxiv_id, title, abstract, etc.)
            force_download: Whether to force re-download the PDF
        
        Returns:
            Whether loading succeeded
        """
        arxiv_id = paper.get('arxiv_id')
        if not arxiv_id:
            print("❌ Paper missing arxiv_id")
            return False
        
        print(f"\n{'='*60}")
        print(f"📚 Loading paper: {paper.get('title', arxiv_id)}")
        print(f"{'='*60}")
        
        # Save basic info
        self.current_paper = paper
        
        # Try to get cached text (unless forcing re-download)
        if not force_download:
            cached_text = self.pdf_processor.get_cached_text(arxiv_id)
            if cached_text:
                self.current_full_text = cached_text
                chars = len(cached_text)
                print(f"✅ Using cached full text ({chars} characters)")
                self._prepare_context()
                return True
            else:
                print("🔍 No cache found, will download PDF")
        else:
            print("🔄 Forcing re-download")
        
        # Download and extract full PDF text
        pdf_url = paper.get('pdf_url')
        result = self.pdf_processor.process_paper(arxiv_id, pdf_url)
        
        if result['success']:
            self.current_full_text = result['full_text']
            self._prepare_context()
            return True
        else:
            err = result.get('error', 'Unknown error')
            print(f"❌ Failed to load paper: {err}")
            # Even if PDF loading fails, Q&A can be based on the abstract
            print("⚠️  Will use abstract-only for Q&A")
            self.current_full_text = None
            self._prepare_context()
            return True  # still return True to allow abstract-based Q&A
    
    def _prepare_context(self):
        """Prepare paper context info"""
        # Clear conversation history
        self.conversation_history = []
        
        # Clear cached context
        self._cached_paper_context = None
        
        print("\n📋 Paper Info:")
        print(f"  Title: {self.current_paper.get('title', 'N/A')}")
        first_authors = ', '.join(self.current_paper.get('authors', [])[:3])
        print(f"  Authors: {first_authors}...")
        print(f"  ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
        
        if self.current_full_text:
            full_len = len(self.current_full_text)
            print(f"  Full text length: {full_len} characters")
            # Check if truncation needed
            if len(self.current_full_text) > self.max_context_length:
                use_len = self.max_context_length
                print(
                    f"  ⚠️  Full text too long, will use first {use_len} chars"
                )
        else:
            abs_len = len(self.current_paper.get('abstract', ''))
            print(f"  Abstract length: {abs_len} characters")
        
        print("\n💬 You can now start Q&A for this paper!")
    
    def _build_paper_context(self) -> str:
        """
        Build paper context (with caching)
        
        Returns:
            Paper context string
        """
        # If already built, return cached
        if self._cached_paper_context is not None:
            return self._cached_paper_context
        
        context_parts = []
        
        # Basic info
        context_parts.append("=" * 60)
        context_parts.append("Paper Info")
        context_parts.append("=" * 60)
        title = self.current_paper.get('title', 'N/A')
        context_parts.append(f"Title: {title}")
        arx_id = self.current_paper.get('arxiv_id', 'N/A')
        context_parts.append(f"ArXiv ID: {arx_id}")
        
        # Authors
        authors = self.current_paper.get('authors', [])
        if authors:
            context_parts.append(f"Authors: {', '.join(authors)}")
        
        # Affiliations
        affiliations = self.current_paper.get('affiliations', [])
        if affiliations and any(a for a in affiliations if a and a.strip()):
            valid_affs = [a for a in affiliations if a and a.strip()]
            context_parts.append(f"Affiliations: {'; '.join(set(valid_affs))}")
        
        # Categories
        categories = self.current_paper.get('categories', [])
        if categories:
            context_parts.append(f"Categories: {', '.join(categories)}")
        
        # Published date
        if self.current_paper.get('published'):
            pub = self.current_paper.get('published')
            context_parts.append(f"Published date: {pub}")
        
        context_parts.append("")
        
        # Abstract
        abstract = (
            self.current_paper.get('abstract_cn')
            or self.current_paper.get('abstract', '')
        )
        if abstract:
            context_parts.append("=" * 60)
            context_parts.append("Abstract")
            context_parts.append("=" * 60)
            context_parts.append(abstract)
            context_parts.append("")
        
        # Full text (if available)
        if self.current_full_text:
            context_parts.append("=" * 60)
            context_parts.append("Full Paper Text")
            context_parts.append("=" * 60)
            
            # Truncate overly long text
            full_text = self.current_full_text
            if len(full_text) > self.max_context_length:
                full_text = full_text[:self.max_context_length]
                context_parts.append(
                    "(Note: Full text too long; only first part included)"
                )
                context_parts.append("")
            
            context_parts.append(full_text)
        
        # Cache the built context
        self._cached_paper_context = "\n".join(context_parts)
        return self._cached_paper_context
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt"""
        return (
            "You are a professional academic paper analysis expert. "
            "You are helping the user deeply understand a specific paper.\n\n"
            "Your tasks:\n"
            "1. Answer questions using the full paper (title, abstract).\n"
            "2. Provide accurate, detailed, and insightful answers.\n"
            "3. Cite specific content from the paper to support answers.\n"
            "4. If an answer is not in the paper, state that clearly.\n"
            "5. Explain concepts, analyze methods, and summarize findings.\n"
            "6. Support both Chinese and English Q&A.\n\n"
            "You can help the user:\n"
            "- Understand core contributions and innovations\n"
            "- Analyze research methods and experimental design\n"
            "- Explain technical details and algorithms\n"
            "- Summarize key conclusions and findings\n"
            "- Evaluate strengths and weaknesses\n"
            "- Compare with related work\n"
            "- Answer any questions about this paper\n\n"
            "Please keep a professional, accurate, and well-structured style."
        )
    
    def chat(self, user_message: str) -> str:
        """
        Chat with the user
        
        Args:
            user_message: User message
        
        Returns:
            AI response
        """
        if not self.current_paper:
            return "❌ Please load a paper before starting Q&A"
        
        try:
            # Build message list
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system",
                "content": self._get_system_prompt()
            })
            
            # ⭐ Important change: add paper context on every turn to
            # ensure the AI can always access the full paper
            # Even with long history, the AI can answer paper basics
            paper_context = self._build_paper_context()
            messages.append({
                "role": "system",
                "content": f"Below is the paper content the user wants to explore:\n\n{paper_context}"
            })
            
            # Add recent conversation history (last 10 turns)
            # Keep only recent turns since the full paper is above
            recent_history = self.conversation_history[-self.max_conversation_history:] if len(self.conversation_history) > self.max_conversation_history else self.conversation_history
            messages.extend(recent_history)
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call the LLM
            print("  🤔 AI is thinking...", end='', flush=True)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            
            print("\r  ✓ AI response complete     ")
            
            ai_response = response.choices[0].message.content.strip()
            
            # Update conversation history
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
            error_msg = f"❌ Chat error: {str(e)}"
            print(f"\n{error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    def start_interactive_chat(self):
        """Start interactive chat"""
        if not self.current_paper:
            print("❌ Please load a paper first")
            return
        
        print(f"\n{'='*60}")
        print("💬 Single-paper deep Q&A started")
        print(f"{'='*60}")
        print(f"📚 Current paper: {self.current_paper.get('title', 'N/A')[:80]}...")
        print(f"🔗 ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
        
        if self.current_full_text:
            print(f"✅ Full text loaded ({len(self.current_full_text)} characters)")
        else:
            print(f"⚠️  Using abstract only")
        
        print(f"\n{'='*60}")
        print("💡 Tips:")
        print("  - Type 'quit' or 'exit' to end the chat")
        print("  - Type 'clear' to clear conversation history")
        print("  - Type 'info' to view paper info")
        print(f"{'='*60}\n")
        
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                # Check commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Ending chat, thank you!")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("\n✅ Conversation history cleared\n")
                    continue
                
                if user_input.lower() == 'info':
                    print(f"\n{'='*60}")
                    print("📋 Paper Info")
                    print(f"{'='*60}")
                    print(f"Title: {self.current_paper.get('title', 'N/A')}")
                    print(f"ArXiv ID: {self.current_paper.get('arxiv_id', 'N/A')}")
                    print(f"Authors: {', '.join(self.current_paper.get('authors', [])[:5])}")
                    if self.current_full_text:
                        print(f"Full text length: {len(self.current_full_text)} characters")
                    print(f"{'='*60}\n")
                    continue
                
                if not user_input:
                    print("Please enter your question...\n")
                    continue
                
                # Chat
                ai_response = self.chat(user_input)
                print(f"\n🤖 Assistant: {ai_response}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Ending chat, thank you!")
                break
            except Exception as e:
                print(f"\n❌ Error occurred: {e}\n")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        # Keep cached paper context
        print("✅ Conversation history cleared (paper context retained)")
    
    def save_conversation(self, filepath: str):
        """
        Save conversation to file
        
        Args:
            filepath: Save path
        """
        data = {
            'paper': self.current_paper,
            'conversation': self.conversation_history
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Conversation saved to: {filepath}")


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Single-paper deep Q&A')
    parser.add_argument('--arxiv_id', required=True, help='ArXiv ID')
    parser.add_argument('--model', default='gpt-4', help='LLM model')
    parser.add_argument('--papers_file', help='Papers data JSON file (optional)')
    
    args = parser.parse_args()
    
    # Create chatbot instance
    chatbot = PaperChatBot(model_name=args.model)
    
    # Load paper
    paper = None
    if args.papers_file:
        # Load from file
        with open(args.papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        # Find the specified paper
        for p in papers:
            if p.get('arxiv_id') == args.arxiv_id:
                paper = p
                break
    
    if not paper:
        # Create basic paper information
        paper = {
            'arxiv_id': args.arxiv_id,
            'title': f'ArXiv Paper {args.arxiv_id}',
            'pdf_url': f'https://arxiv.org/pdf/{args.arxiv_id}.pdf'
        }
    
    # Load paper
    if chatbot.load_paper(paper):
        # Start interactive chat
        chatbot.start_interactive_chat()
    else:
        print("❌ Failed to load paper")

if __name__ == "__main__":
    main()
