import json
import argparse
from typing import List, Dict

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai library is not installed. Please run: pip install openai")
    OpenAI = None


class ArxivChatBot:
    def __init__(self, model_name: str, port: int, host: str = "0.0.0.0",
                 base_url: str = None,
                 api_key: str = None):
        """
        Initialize the Q&A chatbot

        Args:
            model_name: Name of the LLM model
            port: Server port
            host: Server host/address
            base_url: Base URL for the API
            api_key: API key
        """
        if OpenAI is None:
            raise ImportError("openai library is not installed. Please run: pip install openai")

        if base_url is None:
            raise ValueError("base_url argument cannot be None; please provide the API base URL")
        if api_key is None:
            raise ValueError("api_key argument cannot be None; please provide the API key")

        self.model_name = model_name
        self.host = host
        self.port = port

        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        self.papers = []
        self.conversation_history = []
        
    def load_papers(self, papers_data: List[Dict]) -> None:
        """Load papers data

        Args:
            papers_data: list containing paper information
        """
        self.papers = papers_data
        print(f"Loaded {len(self.papers)} papers")

        # Count papers that have abstracts
        papers_with_abstracts = [p for p in self.papers if p.get('abstract')]
        papers_with_cn_abstracts = [p for p in self.papers if p.get('abstract_cn')]

        print(f"Of which {len(papers_with_abstracts)} have English abstracts")
        print(f"Of which {len(papers_with_cn_abstracts)} have Chinese abstracts")
        
    def build_context_prompt(self) -> str:
        """Build a context prompt containing all paper abstracts

        Returns:
            Context string containing paper information
        """
        context_parts = []
        context_parts.append(
            "The following are summaries of relevant academic papers. "
            "Please answer user questions based on these.\n"
        )
        
        for i, paper in enumerate(self.papers, 1):
            context_parts.append(f"=== Paper {i} ===")
            context_parts.append(f"Title: {paper.get('title', 'No title')}")
            context_parts.append(f"ArXiv ID: {paper.get('arxiv_id', 'No ID')}")
            context_parts.append(f"Authors: {', '.join(paper.get('authors', []))}")
            context_parts.append(f"Categories: {', '.join(paper.get('categories', []))}")
            context_parts.append(f"Published: {paper.get('published', 'No date')}")

            # Prefer Chinese abstract when available; otherwise use English abstract
            abstract = paper.get('abstract_cn') or paper.get('abstract', 'No abstract')
            context_parts.append(f"Abstract: {abstract}")
            context_parts.append("")  # blank line separator
            
        return "\n".join(context_parts)
    
    def get_system_prompt(self) -> str:
        """Get system prompt

        Returns:
            System prompt string
        """
        return (
            "You are a professional academic paper analysis assistant. "
            "Your task is to answer user questions based on the provided ArXiv paper abstracts.\n\n"
            "Please follow these guidelines:\n"
            "1. Answer questions only based on the provided paper abstracts.\n"
            "2. If the answer cannot be found in the provided abstracts, state that explicitly.\n"
            "3. You may cite specific paper titles and authors when answering.\n"
            "4. Keep responses professional, accurate, and well-structured.\n"
            "5. If the user asks about a specific paper, provide the ArXiv ID for reference.\n"
            "6. You may perform comparative analysis across multiple papers.\n"
            "7. Support both Chinese and English Q&A.\n\n"
            "You can help users with:\n"
            "- Summarizing the main contributions of papers\n"
            "- Analyzing research methods and techniques\n"
            "- Comparing similarities and differences between papers\n"
            "- Finding papers relevant to a specific topic\n"
            "- Explaining technical concepts and terminology"
        )

    def chat_with_user(self, user_input: str) -> str:
        """Chat with the user

        Args:
            user_input: the user's input

        Returns:
            AI response string
        """
        try:
            # Build messages list
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system", 
                "content": self.get_system_prompt()
            })
            
            # Add papers context (only on first run or when needed)
            if not self.conversation_history:
                context = self.build_context_prompt()
                messages.append({
                    "role": "system",
                    "content": context
                })
            
            # Add conversation history (keep recent messages)
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
            messages.extend(recent_history)
            
            # Add current user input
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Call the LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            return f"Sorry, an error occurred while processing your request: {e}"
    
    def start_interactive_chat(self):
        """Start interactive chat session"""
        print("\n" + "="*60)
        print("🤖 ArXiv Paper Assistant started!")
        print("="*60)
        print(f"📚 Loaded {len(self.papers)} papers")
        print("💬 You can ask questions about these papers")
        print("🔍 Supports topic search, paper comparison, technical analysis, etc.")
        print("📝 Type 'quit', 'exit', or 'q' to end the session")
        print("="*60)
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Thanks for using the ArXiv Paper Assistant!")
                    break
                
                if not user_input:
                    print("Please enter your question...")
                    continue
                
                # Show AI is thinking
                print("\n🤔 AI is analyzing...")
                
                # Get AI response
                ai_response = self.chat_with_user(user_input)
                
                # Display AI response
                print(f"\n🤖 Assistant: {ai_response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using the ArXiv Paper Assistant!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Please try again or type 'quit' to exit")


def ask(args):
    """Q&A function that runs against crawler output

    Args:
        args: an object with configuration attributes:
            - output: input file path (crawler JSON output)
            - translate_llm: LLM model name
            - port: server port
            - max_load_files: maximum number of papers to load at once (opt)
    """
    input_file = args.output
    
    print("\n=== Starting Q&A mode ===")
    print(f"Reading file: {input_file}")
    print(f"Using model: {args.translate_llm}")
    print(f"Service URL: http://0.0.0.0:{args.port}")
    
    # Check for max_load_files parameter
    max_load_files = getattr(args, 'max_load_files', None)
    if max_load_files:
        print(f"Max papers to load concurrently: {max_load_files}")
    
    # Read JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"Successfully read file, containing {len(papers)} papers")
    except Exception as e:
        print(f"❌ Failed to read input file: {e}")
        return
    
    # Initialize 'conversation' field for each paper
    for i, paper in enumerate(papers):
        if 'conversation' not in paper:
            paper['conversation'] = []
        # Ensure each paper has a unique stable ID
        paper['_paper_id'] = i + 1
    
    # Create chatbot
    try:
        base_url = getattr(args, 'base_url', None)
        api_key = getattr(args, 'api_key', None)
        if base_url is None or api_key is None:
            raise ValueError(
                "Missing required parameters: base_url and api_key must be provided"
            )
        chatbot = ArxivChatBot(
            model_name=args.translate_llm,
            port=args.port,
            base_url=base_url,
            api_key=api_key
        )
        
        # Load papers data
        chatbot.load_papers(papers)
        
        # Start interactive chat
        chatbot.start_interactive_chat()
        
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return


def main():
    """Simple main for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ArXiv paper Q&A assistant')
    parser.add_argument(
        '--output', required=True, help='path to paper data JSON file'
    )
    parser.add_argument(
        '--translate_llm', required=True, help='LLM model name'
    )
    parser.add_argument(
        '--port', type=int, default=5000, help='LLM service port'
    )
    
    args = parser.parse_args()
    ask(args)


if __name__ == "__main__":
    main()
