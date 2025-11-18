#!/usr/bin/env python3
"""
ArXiv论文AI分析模块
使用LLM生成任务描述、分类和聚类论文
"""

import json
from typing import List, Dict
from collections import defaultdict
import re

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai库未安装。请运行: pip install openai")
    OpenAI = None


class PaperAnalyzer:
    def __init__(self, model_name: str = "gpt-4", 
                 base_url: str = None,
                 api_key: str = None):
        """
        初始化论文分析器
        
        Args:
            model_name: LLM模型名称
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
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=30.0  # 30秒超时
        )
    
    def generate_task_description(self, paper: Dict) -> str:
        """
        为单篇论文生成任务描述
        
        Args:
            paper: 论文数据字典
        
        Returns:
            任务描述字符串
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', paper.get('abstract_cn', ''))
        
        if not title and not abstract:
            return "无法生成任务描述：缺少标题和摘要"
        
        prompt = f"""请根据以下论文的标题和摘要，用一句简洁的话（不超过50字）描述这篇论文要解决的主要任务或问题。

标题: {title}

摘要: {abstract[:500]}

请直接输出任务描述，不需要其他解释。格式示例：
- "视频生成模型的合成数据质量提升"
- "基于强化学习的工具使用优化"
- "多模态大模型的上下文学习研究"
"""
        
        try:
            print(f"  [API调用] 正在请求LLM...", end='', flush=True)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长提炼论文的核心任务。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            print(" ✓", flush=True)
            
            task_description = response.choices[0].message.content.strip()
            # 移除可能的引号和前缀
            task_description = task_description.strip('"\'').replace('任务描述：', '').replace('任务描述:', '')
            task_description = task_description.strip('- ').strip()
            
            return task_description
            
        except Exception as e:
            print(f" ✗", flush=True)
            print(f"  [错误] 生成任务描述失败: {e}")
            import traceback
            traceback.print_exc()
            return "生成失败"
    
    def batch_generate_task_descriptions(self, papers: List[Dict], show_progress: bool = True, progress_callback=None) -> List[Dict]:
        """
        批量生成任务描述
        
        Args:
            papers: 论文列表
            show_progress: 是否显示进度
            progress_callback: 进度回调函数，接收参数 (current, total, paper_title)
        
        Returns:
            添加了任务描述的论文列表
        """
        print(f"\n开始为 {len(papers)} 篇论文生成任务描述...")
        
        success_count = 0
        fail_count = 0
        
        for i, paper in enumerate(papers, 1):
            paper_title = paper.get('title', f'论文 {i}')[:50]  # 截断标题用于显示
            
            try:
                # 更新进度
                if progress_callback:
                    progress_callback(i, len(papers), paper_title)
                
                if show_progress:
                    print(f"[{i}/{len(papers)}] 正在处理: {paper_title}...")
                
                # 生成任务描述
                task_desc = self.generate_task_description(paper)
                paper['task_description'] = task_desc
                
                if task_desc and task_desc != "生成失败":
                    success_count += 1
                    if show_progress:
                        print(f"  ✓ 成功: {task_desc[:50]}")
                else:
                    fail_count += 1
                    print(f"  ✗ 失败: 无法生成任务描述")
                    
            except Exception as e:
                fail_count += 1
                print(f"  ✗ 处理失败 ({paper_title}): {e}")
                paper['task_description'] = "生成失败"
                import traceback
                traceback.print_exc()
        
        print(f"\n✅ 任务描述生成完成！成功: {success_count}, 失败: {fail_count}")
        return papers
    
    def classify_papers(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """
        基于任务描述对论文进行分类
        
        Args:
            papers: 包含任务描述的论文列表
        
        Returns:
            分类结果字典 {类别名: 论文列表}
        """
        print(f"\n开始对 {len(papers)} 篇论文进行智能分类...")
        
        # 收集所有任务描述
        task_descriptions = []
        for paper in papers:
            task_desc = paper.get('task_description', '')
            if task_desc and task_desc != "生成失败":
                task_descriptions.append({
                    'index': papers.index(paper),
                    'title': paper.get('title', ''),
                    'task': task_desc
                })
        
        if not task_descriptions:
            print("没有可用的任务描述进行分类")
            return {"未分类": papers}
        
        # 使用LLM进行分类
        prompt = f"""请根据以下论文的任务描述，将它们分成若干个相似的主题类别。

论文列表：
{chr(10).join([f"{i+1}. {td['task']}" for i, td in enumerate(task_descriptions)])}

要求：
1. 识别主要的研究主题/任务类型
2. 给每个类别起一个简洁的名称（不超过15字）
3. 将相似任务的论文归为同一类
4. 每篇论文只归属一个类别
5. 输出格式为JSON，例如：
{{
  "视频生成": [1, 3, 5],
  "强化学习": [2, 7],
  "多模态学习": [4, 6, 8]
}}

请直接输出JSON格式的分类结果，不要其他解释。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的论文分类专家。请严格按照JSON格式输出结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group()
            
            classification = json.loads(result_text)
            
            # 将索引转换为论文对象
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
            
            print(f"✅ 分类完成！共 {len(classified_papers)} 个类别")
            for category, paper_list in classified_papers.items():
                print(f"  - {category}: {len(paper_list)} 篇")
            
            return classified_papers
            
        except Exception as e:
            print(f"分类失败: {e}")
            # 降级方案：基于关键词简单分类
            return self._simple_classify(papers)
    
    def _simple_classify(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """
        简单的基于关键词的分类（降级方案）
        
        Args:
            papers: 论文列表
        
        Returns:
            分类结果
        """
        print("使用简单分类方法...")
        
        # 定义关键词映射
        keyword_map = {
            "视频生成": ["video", "synthesis", "generation"],
            "强化学习": ["reinforcement", "rl", "agent", "policy"],
            "多模态学习": ["multimodal", "vision", "language", "vlm"],
            "工具使用": ["tool", "function", "api", "calling"],
            "大语言模型": ["llm", "language model", "gpt", "bert", "transformer"],
            "计算机视觉": ["image", "detection", "segmentation", "classification"],
            "自然语言处理": ["nlp", "text", "translation", "summarization"]
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
                paper_copy['category'] = "其他"
                classified["其他"].append(paper_copy)
        
        return dict(classified)
    
    def cluster_papers_by_similarity(self, papers: List[Dict], num_clusters: int = 5) -> Dict[str, List[Dict]]:
        """
        基于相似度聚类论文
        
        Args:
            papers: 论文列表
            num_clusters: 聚类数量
        
        Returns:
            聚类结果
        """
        print(f"\n开始聚类分析，目标聚类数: {num_clusters}...")
        
        # 使用分类功能作为聚类的基础
        # 实际的聚类可以使用embedding + k-means，但这里简化处理
        classified = self.classify_papers(papers)
        
        # 如果类别数量超过目标聚类数，合并相似类别
        if len(classified) > num_clusters:
            print(f"类别数 ({len(classified)}) 超过目标聚类数 ({num_clusters})，进行合并...")
            # 这里简化处理，取前num_clusters个最大的类别
            sorted_categories = sorted(classified.items(), key=lambda x: len(x[1]), reverse=True)
            result = {}
            for i, (cat, papers_list) in enumerate(sorted_categories[:num_clusters]):
                result[f"聚类{i+1}-{cat}"] = papers_list
            
            # 将剩余的放入"其他"类别
            if len(sorted_categories) > num_clusters:
                other_papers = []
                for cat, papers_list in sorted_categories[num_clusters:]:
                    for p in papers_list:
                        p['category'] = "其他"
                    other_papers.extend(papers_list)
                if other_papers:
                    result["其他"] = other_papers
            
            return result
        
        # 确保所有论文都有category字段
        for category, papers_list in classified.items():
            for paper in papers_list:
                if 'category' not in paper:
                    paper['category'] = category
        
        return classified
    
    def generate_summary_report(self, classified_papers: Dict[str, List[Dict]]) -> str:
        """
        生成分类总结报告
        
        Args:
            classified_papers: 分类后的论文
        
        Returns:
            总结报告文本
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 论文分类分析报告")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        total_papers = sum(len(papers) for papers in classified_papers.values())
        report_lines.append(f"总论文数: {total_papers} 篇")
        report_lines.append(f"分类数量: {len(classified_papers)} 个")
        report_lines.append("")
        
        for category, papers in classified_papers.items():
            report_lines.append(f"\n{'='*60}")
            report_lines.append(f"📁 类别: {category} ({len(papers)} 篇)")
            report_lines.append(f"{'='*60}")
            
            for i, paper in enumerate(papers, 1):
                report_lines.append(f"\n{i}. {paper.get('title', '无标题')}")
                report_lines.append(f"   arXiv ID: {paper.get('arxiv_id', 'N/A')}")
                report_lines.append(f"   任务描述: {paper.get('task_description', '无')}")
                if paper.get('authors'):
                    authors_str = ', '.join(paper['authors'][:3])
                    if len(paper['authors']) > 3:
                        authors_str += f" 等 {len(paper['authors'])} 位作者"
                    report_lines.append(f"   作者: {authors_str}")
        
        report_lines.append("\n" + "=" * 60)
        report_lines.append("报告生成完成")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


def analyze(papers_file: str, output_file: str = None, model_name: str = "gpt-4",
            base_url: str = None,
            api_key: str = None):
    """
    分析论文并生成报告
    
    Args:
        papers_file: 输入论文JSON文件
        output_file: 输出文件路径
        model_name: 使用的模型名称
        base_url: API基础URL
        api_key: API密钥
    """
    if base_url is None:
        raise ValueError("base_url 参数不能为 None，请提供 API 基础 URL")
    if api_key is None:
        raise ValueError("api_key 参数不能为 None，请提供 API 密钥")
    print(f"\n{'='*60}")
    print("🤖 开始论文AI分析")
    print(f"{'='*60}\n")
    
    # 读取论文数据
    try:
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"✅ 成功加载 {len(papers)} 篇论文")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 创建分析器
    analyzer = PaperAnalyzer(model_name=model_name, base_url=base_url, api_key=api_key)
    
    # 生成任务描述
    papers = analyzer.batch_generate_task_descriptions(papers)
    
    # 分类论文
    classified_papers = analyzer.classify_papers(papers)
    
    # 生成报告
    report = analyzer.generate_summary_report(classified_papers)
    print("\n" + report)
    
    # 保存结果
    if output_file:
        # 保存分类结果
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
            print(f"\n✅ 分析结果已保存到: {output_file}")
        except Exception as e:
            print(f"\n❌ 保存失败: {e}")
    
    # 同时保存原始论文数据（包含任务描述）
    try:
        original_with_tasks = papers_file.replace('.json', '_with_tasks.json')
        with open(original_with_tasks, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"✅ 带任务描述的论文数据已保存到: {original_with_tasks}")
    except Exception as e:
        print(f"⚠️  保存带任务描述的数据失败: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ArXiv论文AI分析工具')
    parser.add_argument('--input', '-i', required=True, help='输入论文JSON文件')
    parser.add_argument('--output', '-o', help='输出分析结果文件')
    parser.add_argument('--model', '-m', default='gpt-4', help='LLM模型名称')
    
    args = parser.parse_args()
    
    output_file = args.output
    if not output_file:
        output_file = args.input.replace('.json', '_analyzed.json')
    
    analyze(args.input, output_file, args.model)

