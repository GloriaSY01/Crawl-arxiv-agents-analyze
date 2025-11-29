#!/usr/bin/env python3
"""
ArXiv Paper AI Analysis Module
Use LLM to generate task descriptions, classify, and cluster papers
"""

import json
from typing import List, Dict
from collections import defaultdict
import re

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai library not installed. Please run: pip install openai")
    OpenAI = None


class PaperAnalyzer:
    def __init__(self, model_name: str = "gpt-4", 
                 base_url: str = None,
                 api_key: str = None):
        """
        Initialize the paper analyzer

        Args:
            model_name: Name of the LLM model
            base_url: API base URL
            api_key: API key
        """
        if OpenAI is None:
            raise ImportError("openai library not installed. Please run: pip install openai")
        
        if base_url is None:
            raise ValueError("base_url cannot be None. Please provide the API base URL")
        if api_key is None:
            raise ValueError("api_key cannot be None. Please provide the API key")
        
        self.model_name = model_name
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=30.0 
        )
    
    def generate_task_description(self, paper: Dict) -> str:
        """
        Generate a task description for a single paper

        Args:
            paper: Dictionary containing paper data

        Returns:
            Task description string
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', paper.get('abstract_cn', ''))
        
        if not title and not abstract:
            return "Unable to generate task description: missing title and abstract"
        
        prompt = f"""Based on the paper's title and abstract below, describe in one concise sentence (no more than 25 English words) the main task or problem this paper aims to solve.

Title: {title}

Abstract: {abstract[:500]}

Please output ONLY the task description without any additional explanations. Examples:
- "Improving synthetic data quality for video generation models"
- "Optimizing tool use via reinforcement learning"
- "Studying in-context learning in multimodal large models"
"""
        
        try:
            print(f"  [API] Requesting LLM...", end='', flush=True)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional academic paper analysis assistant, skilled at extracting core tasks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            print(" ✓", flush=True)
            
            task_description = response.choices[0].message.content.strip()
            # Remove possible quotes and prefixes
            task_description = task_description.strip('"\'').replace('Task description:', '').replace('任务描述：', '').replace('任务描述:', '')
            task_description = task_description.strip('- ').strip()
            
            return task_description
            
        except Exception as e:
            print(f" ✗", flush=True)
            print(f"  [Error] Failed to generate task description: {e}")
            import traceback
            traceback.print_exc()
            return "Generation failed"
    
    def batch_generate_task_descriptions(self, papers: List[Dict], show_progress: bool = True, progress_callback=None) -> List[Dict]:
        """
        Batch generate task descriptions

        Args:
            papers: List of papers
            show_progress: Whether to display progress
            progress_callback: Progress callback function, receives parameters (current, total, paper_title)

        Returns:
            List of papers with task descriptions added
        """
        print(f"\nStarting to generate task descriptions for {len(papers)} papers...")
        
        success_count = 0
        fail_count = 0
        
        for i, paper in enumerate(papers, 1):
            paper_title = paper.get('title', f'Paper {i}')[:50]  # Truncate title for display
            
            try:
                # Update progress
                if progress_callback:
                    progress_callback(i, len(papers), paper_title)
                
                if show_progress:
                    print(f"[{i}/{len(papers)}] Processing: {paper_title}...")
                
                # Generate task description
                task_desc = self.generate_task_description(paper)
                paper['task_description'] = task_desc
                
                if task_desc and task_desc != "Generation failed":
                    success_count += 1
                    if show_progress:
                        print(f"  ✓ Success: {task_desc[:50]}")
                else:
                    fail_count += 1
                    print(f"  ✗ Failed: Unable to generate task description")
                    
            except Exception as e:
                fail_count += 1
                print(f"  ✗ Processing failed ({paper_title}): {e}")
                paper['task_description'] = "Generation failed"
                import traceback
                traceback.print_exc()
        
            print(f"\n✅ Task description generation complete! Success: {success_count}, Fail: {fail_count}")
        return papers
    
    def classify_papers(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classify papers based on task descriptions

        Args:
            papers: List of papers with task descriptions

        Returns:
            Dictionary of classification results {category_name: list_of_papers}
        """
        print(f"\nStarting intelligent classification for {len(papers)} papers...")

        # Collect all task descriptions
        task_descriptions = []
        for paper in papers:
            task_desc = paper.get('task_description', '')
            if task_desc and task_desc != "Generation failed":
                task_descriptions.append({
                    'index': papers.index(paper),
                    'title': paper.get('title', ''),
                    'task': task_desc
                })

        if not task_descriptions:
            print("No available task descriptions for classification")
            return {"Unclassified": papers}

        # Build classification prompt
        paper_list_block = "\n".join([
            f"{i+1}. {td['task']}" for i, td in enumerate(task_descriptions)
        ])
        prompt = (
            "Please classify the following papers into a set of similar thematic "
            "categories based on their task descriptions.\n\n"
            "Paper list:\n"
            f"{paper_list_block}\n\n"
            "Requirements:\n"
            "1. Identify the main research themes/task types\n"
            "2. Give each category a concise name (no more than 15 characters)\n"
            "3. Group papers with similar tasks into the same category\n"
            "4. Each paper belongs to only one category\n"
            "5. Output JSON format, for example:\n"
            "{\n"
            "    \"Video Generation\": [1, 3, 5],\n"
            "    \"Reinforcement Learning\": [2, 7],\n"
            "    \"Multimodal Learning\": [4, 6, 8]\n"
            "}\n\n"
            "Please output ONLY the classification result in JSON format, without other explanations."
        )
                    
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional paper classification expert. Strictly output results in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON portion
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group()
            
            classification = json.loads(result_text)
            
            # Convert indices to paper objects
            classified_papers = {}
            for category, indices in classification.items():
                classified_papers[category] = []
                for idx in indices:
                    if 0 <= idx - 1 < len(task_descriptions):
                        paper_idx = task_descriptions[idx - 1]['index']
                        if 0 <= paper_idx < len(papers):
                            paper = papers[paper_idx].copy()
                            paper['category'] = category
                            classified_papers[category].append(paper)
            
            print(f"✅ Classification complete! Total categories: {len(classified_papers)}")
            for category, paper_list in classified_papers.items():
                print(f"  - {category}: {len(paper_list)} papers")
            
            return classified_papers
            
        except Exception as e:
            print(f"Classification failed: {e}")
            # Fallback: keyword-based simple classification
            return self._simple_classify(papers)
    
    def _simple_classify(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Simple keyword-based classification (fallback method)

        Args:
            papers: List of papers

        Returns:
            Classification results
        """
        print("Using simple classification method...")
        
        # Define keyword mapping
        keyword_map = {
            "Video Generation": ["video", "synthesis", "generation"],
            "Reinforcement Learning": ["reinforcement", "rl", "agent", "policy"],
            "Multimodal Learning": ["multimodal", "vision", "language", "vlm"],
            "Tool Use": ["tool", "function", "api", "calling"],
            "Large Language Models": ["llm", "language model", "gpt", "bert", "transformer"],
            "Computer Vision": ["image", "detection", "segmentation", "classification"],
            "Natural Language Processing": ["nlp", "text", "translation", "summarization"]
        }
        
        classified = defaultdict(list)
        
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            task_desc = paper.get('task_description', '').lower()
            
            text = f"{title} {abstract} {task_desc}"
            
            matched = False
            for category, keywords in keyword_map.items():
                if any(kw in text for kw in keywords):
                    paper_copy = paper.copy()
                    paper_copy['category'] = category
                    classified[category].append(paper_copy)
                    matched = True
                    break
            
            if not matched:
                paper_copy = paper.copy()
                paper_copy['category'] = "Other"
                classified["Other"].append(paper_copy)
        
        return dict(classified)
    
    def cluster_papers_by_similarity(self, papers: List[Dict], num_clusters: int = 5) -> Dict[str, List[Dict]]:
        """
        Cluster papers based on similarity

        Args:
            papers: List of papers
            num_clusters: Number of clusters

        Returns:
            Clustering results
        """
        print(f"\nStarting clustering analysis, target clusters: {num_clusters}...")
        
        # Use classification as the basis for clustering
        # Actual clustering can use embeddings + k-means; simplified here
        classified = self.classify_papers(papers)
        
        # If number of categories exceeds target clusters, merge similar categories
        if len(classified) > num_clusters:
            print(f"Number of categories ({len(classified)}) exceeds target clusters ({num_clusters}), merging...")
            # Simplified: take the top num_clusters largest categories
            sorted_categories = sorted(classified.items(), key=lambda x: len(x[1]), reverse=True)
            result = {}
            for i, (cat, papers_list) in enumerate(sorted_categories[:num_clusters]):
                result[f"Cluster{i+1}-{cat}"] = papers_list
            
            # Put the remainder into "Other" category
            if len(sorted_categories) > num_clusters:
                other_papers = []
                for cat, papers_list in sorted_categories[num_clusters:]:
                    for p in papers_list:
                        p['category'] = "Other"
                    other_papers.extend(papers_list)
                if other_papers:
                    result["Other"] = other_papers
            
            return result
        
        # Ensure every paper has a category field
        for category, papers_list in classified.items():
            for paper in papers_list:
                if 'category' not in paper:
                    paper['category'] = category
        
        return classified
    
    def generate_summary_report(self, classified_papers: Dict[str, List[Dict]]) -> str:
        """
        Generate a summary report of the classification

        Args:
            classified_papers: Classified papers

        Returns:
            Summary report text
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 Paper Classification Analysis Report")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        total_papers = sum(len(papers) for papers in classified_papers.values())
        report_lines.append(f"Total papers: {total_papers}")
        report_lines.append(f"Number of categories: {len(classified_papers)}")
        report_lines.append("")
        
        for category, papers in classified_papers.items():
            report_lines.append(f"\n{'='*60}")
            report_lines.append(f"📁 Category: {category} ({len(papers)} papers)")
            report_lines.append(f"{'='*60}")
            
            for i, paper in enumerate(papers, 1):
                report_lines.append(f"\n{i}. {paper.get('title', 'Untitled')}")
                report_lines.append(f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}")
                report_lines.append(f"   Task: {paper.get('task_description', 'None')}")
                if paper.get('authors'):
                    authors_str = ', '.join(paper['authors'][:3])
                    if len(paper['authors']) > 3:
                        authors_str += f" and {len(paper['authors'])} authors total"
                    report_lines.append(f"   Authors: {authors_str}")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("Report generation complete")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


def analyze(papers_file: str, output_file: str = None, model_name: str = "gpt-4",
            base_url: str = None,
            api_key: str = None):
    """
    Analyze papers and generate a report

    Args:
        papers_file: Input JSON file containing papers
        output_file: Output file path
        model_name: Name of the model to use
        base_url: API base URL
        api_key: API key
    """
    if base_url is None:
        raise ValueError("base_url cannot be None. Please provide the API base URL")
    if api_key is None:
        raise ValueError("api_key cannot be None. Please provide the API key")
    print(f"\n{'='*60}")
    print("🤖 Starting AI analysis for papers")
    print(f"{'='*60}\n")
    
    # Read paper data
    try:
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"✅ Successfully loaded {len(papers)} papers")
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return
    
    # Create analyzer
    analyzer = PaperAnalyzer(model_name=model_name, base_url=base_url, api_key=api_key)
    
    # Generate task descriptions
    papers = analyzer.batch_generate_task_descriptions(papers)
    
    # Classify papers
    classified_papers = analyzer.classify_papers(papers)
    
    # Generate report
    report = analyzer.generate_summary_report(classified_papers)
    print("\n" + report)
    
    # Save results
    if output_file:
        # Save classification results
        output_data = {
            "summary": {
                "total_papers": len(papers),
                "num_categories": len(classified_papers),
                "categories": list(classified_papers.keys())
            },
            "classified_papers": classified_papers
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ Analysis results saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Save failed: {e}")
    
    # Also save original paper data (including task descriptions)
    try:
        original_with_tasks = papers_file.replace('.json', '_with_tasks.json')
        with open(original_with_tasks, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"✅ Paper data with task descriptions saved to: {original_with_tasks}")
    except Exception as e:
        print(f"⚠️  Failed to save paper data with task descriptions: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ArXiv Paper AI Analysis Tool')
    parser.add_argument('--input', '-i', required=True,
                        help='Input JSON file containing papers')
    parser.add_argument('--output', '-o',
                        help='Output analysis result file')
    parser.add_argument('--model', '-m', default='gpt-4',
                        help='Name of the LLM model')
    
    args = parser.parse_args()
    
    output_file = args.output
    if not output_file:
        output_file = args.input.replace('.json', '_analyzed.json')
    
    analyze(args.input, output_file, args.model)

