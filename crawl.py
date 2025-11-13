import argparse
import requests
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Optional
import urllib.parse
import os
from bs4 import BeautifulSoup
import re

class ArxivCrawler:
    def __init__(self):
        self.arxiv_web_url = "https://arxiv.org"
        self.session = requests.Session()
        # 设置完整的请求头，模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def crawl_by_date(self, category: str = "cs.CV", date: str = None, progress_callback=None) -> List[Dict]:
        """
        从指定日期的arXiv网页爬取论文（符合题目要求的catchup格式）
        
        题目要求URL格式: https://arxiv.org/catchup/cs.CV/2025-09-30?abs=True
        
        Args:
            category: 学科分类，格式如 'cs.CV', 'cs.AI', 'math.OC' 等
            date: 日期，格式 YYYY-MM-DD (如 '2025-09-30')
            progress_callback: 进度回调函数，接收参数 (current, total, arxiv_id, time_remaining)
        
        Returns:
            论文数据列表
        """
        if not date:
            # 如果没有指定日期，使用今天的日期
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 构建URL：https://arxiv.org/catchup/{category}/{date}?abs=True
        url = f"{self.arxiv_web_url}/catchup/{category}/{date}?abs=True"
        print(f"\n正在爬取网页: {url}")
        print(f"   分类: {category}")
        print(f"   日期: {date}")
        
        return self._crawl_from_url(url, category, progress_callback)
    
    def crawl_new_submissions(self, category: str = "cs", progress_callback=None) -> List[Dict]:
        """
        从arxiv网页爬取最新提交的论文（使用/list/{category}/new格式）
        
        Args:
            category: 类别，如 'cs', 'math', 'physics' 等
            progress_callback: 进度回调函数
        
        Returns:
            论文数据列表
        """
        url = f"{self.arxiv_web_url}/list/{category}/new"
        print(f"\n正在爬取网页: {url}")
        return self._crawl_from_url(url, category, progress_callback)
    
    def _crawl_from_url(self, url: str, category: str, progress_callback=None) -> List[Dict]:
        """
        从指定URL爬取论文（统一处理逻辑）
        
        Args:
            url: 要爬取的URL
            category: 类别（用于显示）
            progress_callback: 进度回调函数
        
        Returns:
            论文数据列表
        """
        papers = []
        
        try:
            # 添加延迟，避免触发反爬
            time.sleep(1)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 检测是否遇到reCAPTCHA
            if 'reCAPTCHA' in response.text or len(response.text) < 5000:
                print("⚠️  检测到 arXiv 反爬虫验证（reCAPTCHA）")
                print("   可能的解决方案：")
                print("   1. 等待几分钟后重试")
                print("   2. 更换网络环境或使用VPN")
                print("   3. 在浏览器中先访问 https://arxiv.org 完成验证")
                print("   4. 减少爬取频率")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. 爬取新提交论文 (New submissions)
            print("\n正在爬取 New submissions...")
            new_papers = self._parse_submission_section(soup, "new", category, progress_callback)
            papers.extend(new_papers)
            print(f"✓ 找到 {len(new_papers)} 篇 New submissions")
            
            # 2. 爬取交叉列表论文 (Cross submissions)
            print("\n正在爬取 Cross submissions...")
            cross_papers = self._parse_submission_section(soup, "cross", category, progress_callback)
            papers.extend(cross_papers)
            print(f"✓ 找到 {len(cross_papers)} 篇 Cross submissions")
            
            # 注意：不爬取 Replacements
            
            print(f"\n✅ 总共获取 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_submission_section(self, soup: BeautifulSoup, section_type: str, 
                                  category: str, progress_callback=None) -> List[Dict]:
        """
        解析网页中的提交部分（只获取标题和ID，详细信息从详情页获取）
        
        Args:
            soup: BeautifulSoup对象
            section_type: "new" (New submissions) 或 "cross" (Cross submissions)
            category: 类别
            progress_callback: 可选的进度回调函数，接收参数 (current, total, arxiv_id, time_remaining)
        
        Returns:
            论文数据列表
        """
        papers = []
        
        # 查找对应部分 - 通过标题来定位
        h3_title = None
        expected_count = None
        
        if section_type == "new":
            # 查找 "New submissions for ..." 标题
            for h3 in soup.find_all('h3'):
                h3_text = h3.get_text()
                if 'new submissions' in h3_text.lower():
                    h3_title = h3
                    # 尝试从标题中提取数量 (例如: "New submissions for Mon, 13 Jan 25 (58 entries)")
                    match = re.search(r'\((\d+)\s+entr', h3_text)
                    if match:
                        expected_count = int(match.group(1))
                    break
        else:  # cross
            # 查找 "Cross submissions" 标题
            for h3 in soup.find_all('h3'):
                h3_text = h3.get_text()
                if 'cross' in h3_text.lower() and 'submission' in h3_text.lower():
                    h3_title = h3
                    # 尝试从标题中提取数量
                    match = re.search(r'\((\d+)\s+entr', h3_text)
                    if match:
                        expected_count = int(match.group(1))
                    break
        
        if not h3_title:
            print(f"  ⚠️  未找到 {section_type} 部分的标题")
            # 打印调试信息
            print(f"  调试：页面上的 h3 标题：")
            h3_tags = soup.find_all('h3')
            for h3 in h3_tags[:10]:
                print(f"    - {h3.get_text(strip=True)}")
            return papers
        
        if expected_count:
            print(f"  标题显示应有 {expected_count} 篇论文")
        
        # 查找该标题下的所有 dl 元素（可能有多个）
        # 从h3标题开始，直到下一个h3标题之前的所有dl元素
        dt_tags = []
        dd_tags = []
        
        # 方法1: 查找h3之后的直接兄弟元素
        next_h3 = h3_title.find_next_sibling('h3')
        current = h3_title.find_next_sibling()
        
        while current and current != next_h3:
            # 直接收集 dt 和 dd 元素
            if current.name == 'dt':
                dt_tags.append(current)
            elif current.name == 'dd':
                dd_tags.append(current)
            # 查找dl容器中的元素
            elif current.name == 'dl':
                dt_tags.extend(current.find_all('dt'))
                dd_tags.extend(current.find_all('dd'))
            # 也检查嵌套在div等容器中的元素
            elif current.name in ['div', 'section']:
                for dl in current.find_all('dl'):
                    dt_tags.extend(dl.find_all('dt'))
                    dd_tags.extend(dl.find_all('dd'))
                # 直接的dt和dd
                for dt in current.find_all('dt', recursive=False):
                    dt_tags.append(dt)
                for dd in current.find_all('dd', recursive=False):
                    dd_tags.append(dd)
            current = current.find_next_sibling()
        
        # 方法2: 如果方法1没找到，尝试使用find_next查找所有dl
        if len(dt_tags) == 0:
            print(f"  ⚠️  使用兄弟元素未找到文章，尝试使用 find_next 方法...")
            # 从h3开始查找后续所有dl元素
            current_element = h3_title
            collected_dls = []
            
            # 收集所有在h3之后、next_h3之前的dl元素
            while True:
                dl = current_element.find_next('dl')
                if not dl:
                    break
                    
                # 如果找到了下一个h3，检查dl是否在它之前
                if next_h3:
                    # 使用字符串位置来判断顺序
                    h3_str = str(h3_title)
                    next_h3_str = str(next_h3)
                    dl_str = str(dl)
                    
                    page_html = str(soup)
                    h3_pos = page_html.find(h3_str)
                    dl_pos = page_html.find(dl_str, h3_pos)
                    next_h3_pos = page_html.find(next_h3_str, h3_pos + 1)
                    
                    if dl_pos > h3_pos and (next_h3_pos == -1 or dl_pos < next_h3_pos):
                        collected_dls.append(dl)
                    elif next_h3_pos != -1 and dl_pos >= next_h3_pos:
                        break
                else:
                    # 如果没有next_h3，就收集所有的dl
                    collected_dls.append(dl)
                
                current_element = dl
                
                # 限制最多收集5个dl，避免无限循环
                if len(collected_dls) >= 5:
                    break
            
            # 从收集到的dl中提取dt和dd
            for dl in collected_dls:
                dt_tags.extend(dl.find_all('dt'))
                dd_tags.extend(dl.find_all('dd'))
            
            print(f"  找到 {len(collected_dls)} 个 dl 元素")
        
        print(f"  实际找到 {len(dt_tags)} 篇论文")
        
        if expected_count and len(dt_tags) < expected_count:
            print(f"  ⚠️  警告：找到的论文数({len(dt_tags)})少于预期({expected_count})")
            print(f"  这可能是因为页面内容未完全加载或有隐藏内容")
        
        # 记录开始时间用于计算剩余时间
        start_time = time.time()
        
        for idx, (dt, dd) in enumerate(zip(dt_tags, dd_tags), 1):
            try:
                paper = {}
                
                # 获取arXiv ID
                arxiv_link = dt.find('a', title='Abstract')
                if arxiv_link:
                    arxiv_id = arxiv_link.text.strip()
                    paper['arxiv_id'] = arxiv_id
                    paper['page_url'] = f"{self.arxiv_web_url}/abs/{arxiv_id}"
                    paper['pdf_url'] = f"{self.arxiv_web_url}/pdf/{arxiv_id}.pdf"
                else:
                    continue  # 没有ID就跳过
                
                # 获取标题（从列表页）
                title_tag = dd.find('div', class_='list-title')
                if title_tag:
                    title = title_tag.text.replace('Title:', '').strip()
                    paper['title'] = title
                
                # 添加基本信息
                paper['published'] = datetime.now().strftime("%Y-%m-%d")
                paper['submission_type'] = 'New submission' if section_type == "new" else 'Cross-list'
                paper['category_main'] = category
                
                # 计算并显示预估剩余时间
                time_str = None
                estimated_remaining = None
                
                if idx > 1:  # 从第二篇开始计算
                    elapsed_time = time.time() - start_time
                    avg_time_per_paper = elapsed_time / (idx - 1)
                    remaining_papers = len(dt_tags) - idx + 1
                    estimated_remaining = avg_time_per_paper * remaining_papers
                    
                    # 格式化时间显示
                    if estimated_remaining < 60:
                        time_str = f"{estimated_remaining:.0f}秒"
                    elif estimated_remaining < 3600:
                        minutes = estimated_remaining / 60
                        time_str = f"{minutes:.1f}分钟"
                    else:
                        hours = estimated_remaining / 3600
                        time_str = f"{hours:.1f}小时"
                    
                    print(f"  [{idx}/{len(dt_tags)}] 正在获取论文详情: {arxiv_id} | 预估剩余时间: {time_str}")
                else:
                    print(f"  [{idx}/{len(dt_tags)}] 正在获取论文详情: {arxiv_id}")
                
                # 调用进度回调（如果提供）
                if progress_callback:
                    progress_callback(idx, len(dt_tags), arxiv_id, estimated_remaining)
                
                # 进入详情页获取完整信息
                detail_info = self._get_paper_detail(arxiv_id)
                if detail_info:
                    paper.update(detail_info)
                
                papers.append(paper)
                
            except Exception as e:
                print(f"  ✗ 解析论文失败: {e}")
                continue
        
        return papers
    
    def _get_paper_detail(self, arxiv_id: str) -> Dict:
        """
        从论文详情页获取完整信息（摘要、作者、单位等）
        
        Args:
            arxiv_id: arXiv ID
        
        Returns:
            论文详细信息字典
        """
        url = f"{self.arxiv_web_url}/abs/{arxiv_id}"
        detail = {}
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取摘要
            abstract_block = soup.find('blockquote', class_='abstract')
            if abstract_block:
                # 移除"Abstract:"标签
                abstract_text = abstract_block.get_text(strip=True)
                if abstract_text.startswith('Abstract:'):
                    abstract_text = abstract_text[9:].strip()
                detail['abstract'] = abstract_text
            
            # 获取作者和单位
            # 首先尝试从 meta 标签获取（最可靠）
            meta_authors = soup.find_all('meta', {'name': 'citation_author'})
            meta_institutions = soup.find_all('meta', {'name': 'citation_author_institution'})
            
            authors = []
            affiliations = []
            author_affiliations = []
            
            if meta_authors:
                # 从 meta 标签提取
                authors = [meta.get('content', '').strip() for meta in meta_authors]
                
                # 提取机构信息
                if meta_institutions:
                    affiliations = [meta.get('content', '').strip() for meta in meta_institutions]
                    # 确保affiliations长度与authors相同
                    while len(affiliations) < len(authors):
                        affiliations.append('')
                else:
                    affiliations = [''] * len(authors)
                
                # 构建详细信息
                for author, affiliation in zip(authors, affiliations):
                    author_affiliations.append({
                        'name': author,
                        'affiliation': affiliation if affiliation else ''
                    })
            else:
                # 备用方案：从页面 div 提取
                authors_div = soup.find('div', class_='authors')
                if authors_div:
                    for author_tag in authors_div.find_all('a'):
                        author_name = author_tag.text.strip()
                        authors.append(author_name)
                        affiliations.append('')
                        author_affiliations.append({
                            'name': author_name,
                            'affiliation': ''
                        })
            
            detail['authors'] = authors
            detail['affiliations'] = affiliations
            detail['author_affiliations'] = author_affiliations
            
            # 获取分类信息
            subjects_span = soup.find('span', class_='primary-subject')
            if subjects_span:
                detail['primary_category'] = subjects_span.text.strip()
            
            # 获取所有分类
            categories = []
            subjects_td = soup.find('td', class_='tablecell subjects')
            if subjects_td:
                for span in subjects_td.find_all('span'):
                    cat = span.text.strip()
                    if cat:
                        categories.append(cat)
            detail['categories'] = categories
            
            # 添加延迟避免请求过快
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  获取详情失败 ({arxiv_id}): {e}")
        
        return detail
