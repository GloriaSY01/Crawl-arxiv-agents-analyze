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
        # Set full request headers to mimic a real browser
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
        """Crawl arXiv papers from a specified date (catchup format)

        Expected URL format: https://arxiv.org/catchup/cs.CV/2025-09-30?abs=True

        Args:
            category: subject category like 'cs.CV', 'cs.AI', 'math.OC'
            date: date string in YYYY-MM-DD (e.g. '2025-09-30')
            progress_callback: optional callback (current, total, arxiv_id, time_remaining)

        Returns:
            List of paper data
        """
        if not date:
            # If no date specified, use today's date
            date = datetime.now().strftime("%Y-%m-%d")
        # Check cache: see if 'papers' folder already has data for this date
        
        cached_data = self._check_cache(category, date)
        if cached_data:
            print(f"\n✅ Found cached data (date: {date}), skipping crawl")
            print(f"   Cache file contains {len(cached_data)} papers")
            return cached_data
        
        # Build URL: https://arxiv.org/catchup/{category}/{date}?abs=True
        url = f"{self.arxiv_web_url}/catchup/{category}/{date}?abs=True"
        print(f"\nCrawling URL: {url}")
        print(f"   Category: {category}")
        print(f"   Date: {date}")
        
        return self._crawl_from_url(url, category, progress_callback)
    
    def crawl_new_submissions(self, category: str = "cs", progress_callback=None) -> List[Dict]:
        """Crawl the latest submissions from arXiv (using /list/{category}/new)

        Args:
            category: category like 'cs', 'math', 'physics'
            progress_callback: optional progress callback

        Returns:
            List of paper data
        """
        url = f"{self.arxiv_web_url}/list/{category}/new"
        print(f"\nCrawling URL: {url}")
        return self._crawl_from_url(url, category, progress_callback)
    
    def _crawl_from_url(self, url: str, category: str, progress_callback=None) -> List[Dict]:
        """Crawl papers from the specified URL (common logic)

        Args:
            url: URL to crawl
            category: category (for display)
            progress_callback: optional progress callback

        Returns:
            List of paper data
        """
        papers = []
        
        try:
            # Add a delay to avoid anti-scraping triggers
            time.sleep(1)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Detect possible reCAPTCHA anti-scraping
            if 'reCAPTCHA' in response.text or len(response.text) < 5000:
                print("⚠️  Detected arXiv anti-bot verification (reCAPTCHA)")
                print("   Possible remedies:")
                print("   1. Wait a few minutes and retry")
                print("   2. Change network or use a VPN")
                print("   3. Visit https://arxiv.org in a browser and complete verification")
                print("   4. Reduce crawl frequency")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Crawl new submissions
            print("\nCrawling New submissions...")
            new_papers = self._parse_submission_section(soup, "new", category, progress_callback)
            papers.extend(new_papers)
            print(f"✓ Found {len(new_papers)} New submissions")
            
            # 2. Crawl cross-list submissions
            print("\nCrawling Cross submissions...")
            cross_papers = self._parse_submission_section(soup, "cross", category, progress_callback)
            papers.extend(cross_papers)
            print(f"✓ Found {len(cross_papers)} Cross submissions")
            
            print(f"\n✅ Total collected {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"❌ Crawl failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_submission_section(self, soup: BeautifulSoup, section_type: str, 
                                  category: str, progress_callback=None) -> List[Dict]:
        """Parse a submission section from the page (collect title and ID)

        Details are fetched from the paper detail page.

        Args:
            soup: BeautifulSoup object
            section_type: "new" or "cross"
            category: category string
            progress_callback: optional callback (current, total, arxiv_id, time_remaining)

        Returns:
            List of paper dicts
        """
        papers = []
        
        # Locate the corresponding section by title
        h3_title = None
        expected_count = None
        
        if section_type == "new":
            # Locate the "New submissions for ..." title
            for h3 in soup.find_all('h3'):
                h3_text = h3.get_text()
                if 'new submissions' in h3_text.lower():
                    h3_title = h3
                    # Try to extract the count from the title
                    match = re.search(r'\((\d+)\s+entr', h3_text)
                    if match:
                        expected_count = int(match.group(1))
                    break
        else:  # cross
            # Locate the "Cross submissions" title
            for h3 in soup.find_all('h3'):
                h3_text = h3.get_text()
                if 'cross' in h3_text.lower() and 'submission' in h3_text.lower():
                    h3_title = h3
                    # Try to extract the count from the title
                    match = re.search(r'\((\d+)\s+entr', h3_text)
                    if match:
                        expected_count = int(match.group(1))
                    break
        
        if not h3_title:
            print(f"  ⚠️  Could not find title for {section_type} section")
            # Print debug information
            print(f"  Debug: h3 titles on the page:")
            h3_tags = soup.find_all('h3')
            for h3 in h3_tags[:10]:
                print(f"    - {h3.get_text(strip=True)}")
            return papers
        
        if expected_count:
            print(f"  Title indicates there should be {expected_count} papers")
        
        # Locate all dl elements under the title (there may be multiple)
        # From the h3 title, find all dl elements until the next h3 title
        dt_tags = []
        dd_tags = []
        
        # Method 1: Find direct sibling elements after h3
        next_h3 = h3_title.find_next_sibling('h3')
        current = h3_title.find_next_sibling()
        
        while current and current != next_h3:
            # Directly collect dt and dd elements
            if current.name == 'dt':
                dt_tags.append(current)
            elif current.name == 'dd':
                dd_tags.append(current)
            # Check elements inside dl containers
            elif current.name == 'dl':
                dt_tags.extend(current.find_all('dt'))
                dd_tags.extend(current.find_all('dd'))
            # Also check elements nested inside div or section containers
            elif current.name in ['div', 'section']:
                for dl in current.find_all('dl'):
                    dt_tags.extend(dl.find_all('dt'))
                    dd_tags.extend(dl.find_all('dd'))
                # Direct dt and dd elements
                for dt in current.find_all('dt', recursive=False):
                    dt_tags.append(dt)
                for dd in current.find_all('dd', recursive=False):
                    dd_tags.append(dd)
            current = current.find_next_sibling()
        
        # Method 2: If Method 1 finds nothing, try using find_next to locate all dl elements
        if len(dt_tags) == 0:
            print(f"  ⚠️  No articles found via sibling traversal; trying find_next method...")
            # Start from h3 and find all subsequent dl elements
            current_element = h3_title
            collected_dls = []
            
            # Collect all dl elements after h3 and before next_h3
            while True:
                dl = current_element.find_next('dl')
                if not dl:
                    break
                    
                # If next_h3 is found, check if dl is before it
                if next_h3:
                    # Use string positions to determine order
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
                    # If no next_h3, collect all dl elements
                    collected_dls.append(dl)
                
                current_element = dl
                
                # Limit to collecting at most 5 dl elements to avoid infinite loops
                if len(collected_dls) >= 5:
                    break
            
            # Extract dt and dd from collected dl elements
            for dl in collected_dls:
                dt_tags.extend(dl.find_all('dt'))
                dd_tags.extend(dl.find_all('dd'))
            
            print(f"  Found {len(collected_dls)} dl elements")
        
        print(f"  Actually found {len(dt_tags)} papers")
        
        if expected_count and len(dt_tags) < expected_count:
            print(f"  ⚠️  Warning: found {len(dt_tags)} papers which is less than expected ({expected_count})")
            print(f"  This may be due to incomplete page content or hidden elements")
        
        # Record the start time to calculate remaining time
        start_time = time.time()
        
        for idx, (dt, dd) in enumerate(zip(dt_tags, dd_tags), 1):
            try:
                paper = {}
                
                # Get arXiv ID
                arxiv_link = dt.find('a', title='Abstract')
                if arxiv_link:
                    arxiv_id = arxiv_link.text.strip()
                    paper['arxiv_id'] = arxiv_id
                    paper['page_url'] = f"{self.arxiv_web_url}/abs/{arxiv_id}"
                    paper['pdf_url'] = f"{self.arxiv_web_url}/pdf/{arxiv_id}.pdf"
                else:
                    continue  # Skip if no ID
                
                # Get title (from the list page)
                title_tag = dd.find('div', class_='list-title')
                if title_tag:
                    title = title_tag.text.replace('Title:', '').strip()
                    paper['title'] = title
                
                # Add basic information
                paper['published'] = datetime.now().strftime("%Y-%m-%d")
                paper['submission_type'] = 'New submission' if section_type == "new" else 'Cross-list'
                paper['category_main'] = category
                
                # Calculate and display estimated remaining time
                time_str = None
                estimated_remaining = None
                
                if idx > 1:  # Calculate from the second paper onwards
                    elapsed_time = time.time() - start_time
                    avg_time_per_paper = elapsed_time / (idx - 1)
                    remaining_papers = len(dt_tags) - idx + 1
                    estimated_remaining = avg_time_per_paper * remaining_papers
                    
                    # Format time string
                    if estimated_remaining < 60:
                        time_str = f"{estimated_remaining:.0f}s"
                    elif estimated_remaining < 3600:
                        minutes = estimated_remaining / 60
                        time_str = f"{minutes:.1f}m"
                    else:
                        hours = estimated_remaining / 3600
                        time_str = f"{hours:.1f}h"
                    
                    print(f"  [{idx}/{len(dt_tags)}] Fetching details: {arxiv_id} | ETA: {time_str}")
                else:
                    print(f"  [{idx}/{len(dt_tags)}] Fetching details: {arxiv_id}")
                
                # Call progress callback (if provided)
                if progress_callback:
                    progress_callback(idx, len(dt_tags), arxiv_id, estimated_remaining)
                
                # Visit detail page to get full info
                detail_info = self._get_paper_detail(arxiv_id)
                if detail_info:
                    paper.update(detail_info)
                
                papers.append(paper)
                
            except Exception as e:
                print(f"  ✗ Failed to parse paper: {e}")
                continue
        
        return papers
    
    def _get_paper_detail(self, arxiv_id: str) -> Dict:
        """Get full paper details from its detail page (abstract, authors, affiliations)

        Args:
            arxiv_id: arXiv ID
        
        Returns:
            dict of paper details
        """
        url = f"{self.arxiv_web_url}/abs/{arxiv_id}"
        detail = {}
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract abstract
            abstract_block = soup.find('blockquote', class_='abstract')
            if abstract_block:
                abstract_text = abstract_block.get_text(strip=True)
                if abstract_text.startswith('Abstract:'):
                    abstract_text = abstract_text[9:].strip()
                detail['abstract'] = abstract_text
            
            # Extract authors and affiliations
            # Try meta tags first (most reliable)
            meta_authors = soup.find_all('meta', {'name': 'citation_author'})
            meta_institutions = soup.find_all('meta', {'name': 'citation_author_institution'})
            
            authors = []
            affiliations = []
            author_affiliations = []
            
            if meta_authors:
                # Extract from meta tags
                authors = [meta.get('content', '').strip() for meta in meta_authors]
                
                # Extract institution information
                if meta_institutions:
                    affiliations = [meta.get('content', '').strip() for meta in meta_institutions]
                    # Ensure affiliations length matches authors
                    while len(affiliations) < len(authors):
                        affiliations.append('')
                else:
                    affiliations = [''] * len(authors)
                
                # Build detailed information
                for author, affiliation in zip(authors, affiliations):
                    author_affiliations.append({
                        'name': author,
                        'affiliation': affiliation if affiliation else ''
                    })
            else:
                # Fallback: extract from page div
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
            
            # Extract primary subject/category
            subjects_span = soup.find('span', class_='primary-subject')
            if subjects_span:
                detail['primary_category'] = subjects_span.text.strip()
            
            # Extract all categories
            categories = []
            subjects_td = soup.find('td', class_='tablecell subjects')
            if subjects_td:
                for span in subjects_td.find_all('span'):
                    cat = span.text.strip()
                    if cat:
                        categories.append(cat)
            detail['categories'] = categories
            
            # Add a delay to avoid making requests too quickly
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Failed to fetch details ({arxiv_id}): {e}")

        return detail

    def _check_cache(self, category: str, date: str) -> Optional[List[Dict]]:
        """Check 'papers' folder for cached data for the given date

        Args:
            category: subject category
            date: date string YYYY-MM-DD (target crawl date)

        Returns:
            List of papers if cache found, otherwise None
        """
        papers_dir = "papers"
        if not os.path.exists(papers_dir):
            return None
        
        # Normalize date format: convert YYYY-MM-DD to YYYYMMDD for comparison
        date_normalized = date.replace('-', '')
        
        try:
            # Iterate through all JSON files in the papers folder
            for filename in os.listdir(papers_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(papers_dir, filename)
                
                # Read the JSON file
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check the data format: it could be a list or a dictionary
                papers = None
                target_date = None  # The date user requested to crawl
                crawl_category = None
                
                if isinstance(data, dict):
                    # New format: {metadata: {...}, papers: [...]} 
                    metadata = data.get('metadata', {})
                    # Use target_date (the date user requested) for matching
                    target_date = metadata.get('target_date', '')
                    crawl_category = metadata.get('category', '')
                    papers = data.get('papers', [])
                elif isinstance(data, list):
                    # Old format: directly a list of papers
                    papers = data
                    # Try to extract target date from filename
                    # New filename format: crawled_{target_date}_{timestamp}.json
                    # e.g., crawled_20250918_20251129_172551.json
                    import re
                    # Match pattern: crawled_{target_date}_{crawl_timestamp}
                    match = re.search(r'crawled_(\d{8})_(\d{8}_\d{6})\.json', filename)
                    if match:
                        target_date = match.group(1)  # Target date
                    else:
                        # Old format without target date - skip
                        continue
                    # Get the category from the first paper
                    if papers and len(papers) > 0:
                        crawl_category = papers[0].get('category_main', '')
                
                # Normalize target_date for comparison
                if target_date:
                    target_date_normalized = target_date.replace('-', '')
                else:
                    continue
                
                # Match the target date and category
                if target_date_normalized == date_normalized:
                    if not category or category == crawl_category:
                        if papers:  # ensure data exists
                            print(f"   Found cache file: {filename}")
                            print(f"   Target date: {date}, Category: {category}")
                            return papers
        
        except Exception as e:
            print(f"  Error while checking cache: {e}")
            import traceback
            traceback.print_exc()
            
        return None