#!/usr/bin/env python3
"""
PDF处理模块
负责下载ArXiv论文PDF并提取全文内容
"""

import os
import requests
import PyPDF2
import pdfplumber
from typing import Optional, Dict
import time
from pathlib import Path
import re


class PDFProcessor:
    def __init__(self, cache_dir: str = "pdfs"):
        """
        初始化PDF处理器
        
        Args:
            cache_dir: PDF缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 设置请求头，模拟浏览器
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_pdf(self, arxiv_id: str, pdf_url: str = None) -> Optional[Path]:
        """
        下载ArXiv论文PDF
        
        Args:
            arxiv_id: ArXiv ID（可能包含"arXiv:"前缀）
            pdf_url: PDF URL（可选，如果不提供则自动构建）
        
        Returns:
            PDF文件路径，如果下载失败返回None
        """
        # 清理arxiv_id：移除"arXiv:"前缀和版本号
        clean_id = arxiv_id.replace('arXiv:', '').replace('arxiv:', '')
        clean_id = clean_id.split('v')[0] if 'v' in clean_id else clean_id
        clean_id = clean_id.strip()
        
        # 检查是否已缓存
        pdf_path = self.cache_dir / f"{clean_id}.pdf"
        if pdf_path.exists():
            print(f"  ✓ PDF已缓存: {pdf_path}")
            return pdf_path
        
        # 构建PDF URL
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        
        print(f"  📥 正在下载PDF: {pdf_url}")
        
        try:
            # 下载PDF
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # 保存到文件
            total_size = int(response.headers.get('content-length', 0))
            print(f"  文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            with open(pdf_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r  下载进度: {progress:.1f}%", end='', flush=True)
            
            print(f"\n  ✅ PDF下载成功: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"\n  ❌ PDF下载失败: {e}")
            if pdf_path.exists():
                pdf_path.unlink()  # 删除不完整的文件
            return None
    
    def extract_text_pypdf2(self, pdf_path: Path) -> Optional[str]:
        """
        使用PyPDF2提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            提取的文本内容
        """
        try:
            text_parts = []
            
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                
                print(f"  📄 PDF共 {num_pages} 页，正在提取文本...")
                
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        
                        if (i + 1) % 5 == 0:
                            print(f"  进度: {i + 1}/{num_pages} 页", end='\r', flush=True)
                    except Exception as e:
                        print(f"\n  ⚠️  第{i+1}页提取失败: {e}")
                        continue
                
                print(f"\n  ✅ 文本提取完成")
            
            full_text = "\n".join(text_parts)
            return full_text if full_text.strip() else None
            
        except Exception as e:
            print(f"  ❌ PyPDF2提取失败: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> Optional[str]:
        """
        使用pdfplumber提取PDF文本（备用方案，更准确）
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            提取的文本内容
        """
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                print(f"  📄 PDF共 {num_pages} 页，正在使用pdfplumber提取文本...")
                
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        
                        if (i + 1) % 5 == 0:
                            print(f"  进度: {i + 1}/{num_pages} 页", end='\r', flush=True)
                    except Exception as e:
                        print(f"\n  ⚠️  第{i+1}页提取失败: {e}")
                        continue
                
                print(f"\n  ✅ 文本提取完成")
            
            full_text = "\n".join(text_parts)
            return full_text if full_text.strip() else None
            
        except Exception as e:
            print(f"  ❌ pdfplumber提取失败: {e}")
            return None
    
    def extract_text(self, pdf_path: Path, method: str = "both") -> Optional[str]:
        """
        提取PDF文本（尝试多种方法）
        
        Args:
            pdf_path: PDF文件路径
            method: 提取方法 ("pypdf2", "pdfplumber", "both")
        
        Returns:
            提取的文本内容
        """
        if method == "pypdf2":
            return self.extract_text_pypdf2(pdf_path)
        elif method == "pdfplumber":
            return self.extract_text_pdfplumber(pdf_path)
        else:  # both
            # 先尝试PyPDF2（更快）
            text = self.extract_text_pypdf2(pdf_path)
            
            # 如果提取失败或文本太短，使用pdfplumber
            if not text or len(text) < 1000:
                print("  ⚠️  PyPDF2提取结果不理想，尝试pdfplumber...")
                text = self.extract_text_pdfplumber(pdf_path)
            
            return text
    
    def clean_text(self, text: str) -> str:
        """
        清理提取的文本
        
        Args:
            text: 原始文本
        
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除页眉页脚常见模式
        text = re.sub(r'\d+\s+arXiv:\d+\.\d+v\d+', '', text)
        
        # 移除多余的换行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def process_paper(self, arxiv_id: str, pdf_url: str = None) -> Dict[str, any]:
        """
        处理单篇论文：下载PDF并提取文本
        
        Args:
            arxiv_id: ArXiv ID
            pdf_url: PDF URL（可选）
        
        Returns:
            包含处理结果的字典
        """
        print(f"\n{'='*60}")
        print(f"📑 处理论文: {arxiv_id}")
        print(f"{'='*60}")
        
        result = {
            'arxiv_id': arxiv_id,
            'success': False,
            'pdf_path': None,
            'full_text': None,
            'text_length': 0,
            'error': None
        }
        
        try:
            # 下载PDF
            pdf_path = self.download_pdf(arxiv_id, pdf_url)
            if not pdf_path:
                result['error'] = "PDF下载失败"
                return result
            
            result['pdf_path'] = str(pdf_path)
            
            # 提取文本
            full_text = self.extract_text(pdf_path)
            if not full_text:
                result['error'] = "文本提取失败"
                return result
            
            # 清理文本
            cleaned_text = self.clean_text(full_text)
            
            result['full_text'] = cleaned_text
            result['text_length'] = len(cleaned_text)
            result['success'] = True
            
            print(f"\n✅ 处理完成!")
            print(f"  文本长度: {result['text_length']} 字符")
            print(f"  PDF路径: {result['pdf_path']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def get_cached_text(self, arxiv_id: str) -> Optional[str]:
        """
        获取缓存的PDF文本（如果存在）
        
        Args:
            arxiv_id: ArXiv ID
        
        Returns:
            缓存的文本内容，如果不存在返回None
        """
        clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        pdf_path = self.cache_dir / f"{clean_id}.pdf"
        
        if pdf_path.exists():
            print(f"  🔍 找到缓存的PDF: {pdf_path}")
            text = self.extract_text(pdf_path)
            return self.clean_text(text) if text else None
        
        return None
    
    def clear_cache(self, arxiv_id: str = None):
        """
        清理PDF缓存
        
        Args:
            arxiv_id: 如果指定，只删除该论文的PDF；否则清空整个缓存
        """
        if arxiv_id:
            clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
            pdf_path = self.cache_dir / f"{clean_id}.pdf"
            if pdf_path.exists():
                pdf_path.unlink()
                print(f"  ✅ 已删除缓存: {pdf_path}")
        else:
            for pdf_file in self.cache_dir.glob("*.pdf"):
                pdf_file.unlink()
            print(f"  ✅ 已清空PDF缓存目录")


def test_pdf_processor():
    """测试PDF处理器"""
    processor = PDFProcessor()
    
    # 测试一个真实的ArXiv论文
    test_arxiv_id = "2301.00234"  # 替换为实际的ArXiv ID
    
    result = processor.process_paper(test_arxiv_id)
    
    if result['success']:
        print("\n" + "="*60)
        print("📊 提取结果预览:")
        print("="*60)
        print(result['full_text'][:1000] + "...")
        print("\n...")
        print(result['full_text'][-500:])
    else:
        print(f"\n❌ 测试失败: {result['error']}")


if __name__ == "__main__":
    test_pdf_processor()
