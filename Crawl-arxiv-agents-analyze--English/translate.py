#!/usr/bin/env python3
"""
ArXiv Article Abstract Translation Module

"""

import json
import asyncio
import aiohttp
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from tqdm import tqdm

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai library is not installed. Please run: pip install openai")
    OpenAI = None


class ArxivTranslator:
    def __init__(self, model_name: str, port: int, host: str = "0.0.0.0",
                 base_url: str = None,
                 api_key: str = None):
        """
        Initialize the translator
        
        Args:
            model_name: LLM model name
            port: Service port
            host: Service address
            base_url: API base URL
            api_key: API key
        """
        if OpenAI is None:
            raise ImportError("openai library is not installed. Please run: pip install openai")
        
        if base_url is None:
            raise ValueError("base_url parameter cannot be None, please provide the API base URL")
        if api_key is None:
            raise ValueError("api_key parameter cannot be None, please provide the API key")
            
        self.model_name = model_name
        self.host = host
        self.port = port
        self.base_url = base_url
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Processing prompt
        self.system_prompt = """You are a professional academic paper expert. Please process the English abstract provided by the user.

Requirements:
1. Maintain the accuracy of academic terminology
2. Maintain the original logical structure and technical details
3. Output only the result without any explanations or additional content

Please output in English directly."""
    def translate_single_abstract(self, abstract: str) -> str:
        """
        Translate a single abstract
        
        Args:
            abstract: English abstract
            
        Returns:
            abstract: English abstract
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": abstract}
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            translation = response.choices[0].message.content.strip()
            return translation
            
        except Exception as e:
            print(f"Translation failed: {e}")
            return abstract  # If translation fails, return the original text
    
    def translate_abstracts_batch(self, papers: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Batch translate abstracts
        
        Args:
            papers: List of papers containing abstracts
            batch_size: Concurrency level
            
        Returns:
            List of papers with added English abstracts
        """
        print(f"Starting translation of abstracts for {len(papers)} papers...")
        print(f"Using model: {self.model_name}")
        print(f"Service address: {self.base_url}")
        print(f"Concurrency level: {batch_size}")
        
        # Filter papers with abstracts
        papers_with_abstracts = [p for p in papers if p.get('abstract')]
        print(f"{len(papers_with_abstracts)} papers have abstracts that need translation")
        
        # Use thread pool for concurrent translation
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit translation tasks
            future_to_paper = {}
            for paper in papers_with_abstracts:
                abstract = paper.get('abstract', '')
                if abstract:
                    future = executor.submit(self.translate_single_abstract, abstract)
                    future_to_paper[future] = paper
            
            # Collect translation results
            completed_count = 0
            for future in tqdm(as_completed(future_to_paper), total=len(future_to_paper)):
                paper = future_to_paper[future]
                try:
                    translation = future.result()
                    paper['abstract_cn'] = translation
                    completed_count += 1
                    
                    # Show progress
                    if completed_count % max(1, len(papers_with_abstracts) // 10) == 0:
                        progress = (completed_count / len(papers_with_abstracts)) * 100
                        print(f"Translation progress: {completed_count}/{len(papers_with_abstracts)} ({progress:.1f}%)")
                
                except Exception as e:
                    print(f"Error translating paper {paper.get('arxiv_id', 'unknown')}: {e}")
                    paper['abstract_cn'] = paper.get('abstract', '')  # Use original text if translation fails
        
        print(f"Translation completed! Processed {len(papers_with_abstracts)} papers")
        return papers


def translate(args):
    """
    Translation function to process the output file from the crawler
    
    Args:
        args: An object containing translation parameters, which should have the following attributes:
            - output: Input/output file path
            - translate_llm: Translation model name
            - port: Service port
            - batchsize: Concurrency level
    """
    input_file = args.output  # Use the crawler's output file as input
    
    print(f"\n=== Starting translation phase ===")
    print(f"Input file: {input_file}")
    
    # Read JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"Successfully read {len(papers)} papers")
    except Exception as e:
        print(f"Failed to read file: {e}")
        return
    
    # Create translator and translate
    base_url = getattr(args, 'base_url', None)
    api_key = getattr(args, 'api_key', None)
    if base_url is None or api_key is None:
        raise ValueError("Missing required parameters: base_url and api_key must be provided via command line arguments")
    translator = ArxivTranslator(
        model_name=args.translate_llm,
        port=args.port,
        base_url=base_url,
        api_key=api_key
    )
    
    # Execute translation
    translated_papers = translator.translate_abstracts_batch(
        papers=papers,
        batch_size=args.batchsize
    )
    
    # Save results to the original file (remove think token)
    for paper_item in translated_papers:
        abs_cn = paper_item.get('abstract_cn', '')
        if abs_cn and '</think>' in abs_cn:
            paper_item['abstract_cn'] = abs_cn.split('</think>')[-1]
    try:
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(translated_papers, f, ensure_ascii=False, indent=2)
        print(f"Translation results saved to: {input_file}")
    except Exception as e:
        print(f"Failed to save file: {e}")
        return
    
    print("=== Translation phase completed ===\n")


if __name__ == "__main__":
    # Simple parameters for testing
    class Args:
        def __init__(self):
            self.output = "test.json"
            self.translate_llm = "gpt-3.5-turbo"
            self.port = 5000
            self.batchsize = 3
    
    # Create test data
    test_data = [
        {
            "arxiv_id": "test1",
            "title": "Test Paper 1",
            "abstract": "This is a test abstract for machine learning research.",
            "authors": ["Test Author"]
        },
        {
            "arxiv_id": "test2", 
            "title": "Test Paper 2",
            "abstract": "Another test abstract about artificial intelligence.",
            "authors": ["Another Author"]
        }
    ]
    
    # Save test data
    with open("test/test.json", 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # Test translation
    args = Args()
    translate(args)
