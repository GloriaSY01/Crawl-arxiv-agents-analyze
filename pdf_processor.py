#!/usr/bin/env python3
"""
PDF processing module
Responsible for downloading ArXiv paper PDFs and extracting full text
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
        Initialize PDF processor
        
        Args:
            cache_dir: PDF cache directory
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Set request headers to simulate a browser
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_pdf(self, arxiv_id: str, pdf_url: str = None) -> Optional[Path]:
        """
        Download ArXiv paper PDF
        
        Args:
            arxiv_id: ArXiv ID (may contain "arXiv:" prefix)
            pdf_url: PDF URL (optional; auto-constructed if not provided)
        
        Returns:
            PDF file path; returns None if download fails
        """
        # Clean arxiv_id: remove "arXiv:" prefix and version suffix
        clean_id = arxiv_id.replace('arXiv:', '').replace('arxiv:', '')
        clean_id = clean_id.split('v')[0] if 'v' in clean_id else clean_id
        clean_id = clean_id.strip()
        
        # Check cache
        pdf_path = self.cache_dir / f"{clean_id}.pdf"
        if pdf_path.exists():
            print(f"  ✓ PDF cached: {pdf_path}")
            return pdf_path
        
        # Build PDF URL
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        
        print(f"  📥 Downloading PDF: {pdf_url}")
        
        try:
            # Download PDF
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save to file
            total_size = int(response.headers.get('content-length', 0))
            print(f"  File size: {total_size / 1024 / 1024:.2f} MB")
            
            with open(pdf_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            msg = f"\r  Download progress: {progress:.1f}%"
                            print(msg, end='', flush=True)
            
            print(f"\n  ✅ PDF downloaded: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"\n  ❌ PDF download failed: {e}")
            if pdf_path.exists():
                pdf_path.unlink()  # Delete incomplete file
            return None
    
    def extract_text_pypdf2(self, pdf_path: Path) -> Optional[str]:
        """
        Extract PDF text using PyPDF2
        
        Args:
            pdf_path: PDF file path
        
        Returns:
            Extracted text content
        """
        try:
            text_parts = []
            
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                
                print(f"  📄 PDF has {num_pages} pages, extracting text...")
                
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        
                        if (i + 1) % 5 == 0:
                            prog = f"  Progress: {i + 1}/{num_pages} pages"
                            print(prog, end='\r', flush=True)
                    except Exception as e:
                        print(f"\n  ⚠️  Failed to extract page {i+1}: {e}")
                        continue
                
                print("\n  ✅ Text extraction complete")
            
            full_text = "\n".join(text_parts)
            return full_text if full_text.strip() else None
            
        except Exception as e:
            print(f"  ❌ PyPDF2 extraction failed: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> Optional[str]:
        """
        Extract PDF text using pdfplumber (fallback, often more accurate)
        
        Args:
            pdf_path: PDF file path
        
        Returns:
            Extracted text content
        """
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                msg = (
                    f"  📄 PDF has {num_pages} pages, "
                    "extracting with pdfplumber..."
                )
                print(msg)
                
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        
                        if (i + 1) % 5 == 0:
                            prog = f"  Progress: {i + 1}/{num_pages} pages"
                            print(prog, end='\r', flush=True)
                    except Exception as e:
                        print(f"\n  ⚠️  Failed to extract page {i+1}: {e}")
                        continue
                
                print("\n  ✅ Text extraction complete")
            
            full_text = "\n".join(text_parts)
            return full_text if full_text.strip() else None
            
        except Exception as e:
            print(f"  ❌ pdfplumber extraction failed: {e}")
            return None
    
    def extract_text(self, pdf_path: Path, method: str = "both") -> Optional[str]:
        """
        Extract PDF text (try multiple methods)
        
        Args:
            pdf_path: PDF file path
            method: Extraction method ("pypdf2", "pdfplumber", "both")
        
        Returns:
            Extracted text content
        """
        if method == "pypdf2":
            return self.extract_text_pypdf2(pdf_path)
        elif method == "pdfplumber":
            return self.extract_text_pdfplumber(pdf_path)
        else:  # both
            # Try PyPDF2 first (faster)
            text = self.extract_text_pypdf2(pdf_path)
            
            # If extraction fails or text is too short, use pdfplumber
            if not text or len(text) < 1000:
                print(
                    "  ⚠️  PyPDF2 extraction not ideal, trying pdfplumber..."
                )
                text = self.extract_text_pdfplumber(pdf_path)
            
            return text
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common header/footer patterns
        text = re.sub(r'\d+\s+arXiv:\d+\.\d+v\d+', '', text)
        
        # Normalize extra newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def process_paper(self, arxiv_id: str, pdf_url: str = None) -> Dict[str, any]:
        """
        Process a single paper: download PDF and extract text
        
        Args:
            arxiv_id: ArXiv ID
            pdf_url: PDF URL (optional)
        
        Returns:
            A dict containing processing results
        """
        print(f"\n{'='*60}")
        print(f"📑 Processing paper: {arxiv_id}")
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
            # Download PDF
            pdf_path = self.download_pdf(arxiv_id, pdf_url)
            if not pdf_path:
                result['error'] = "PDF download failed"
                return result
            
            result['pdf_path'] = str(pdf_path)
            
            # Extract text
            full_text = self.extract_text(pdf_path)
            if not full_text:
                result['error'] = "Text extraction failed"
                return result
            
            # Clean text
            cleaned_text = self.clean_text(full_text)
            
            result['full_text'] = cleaned_text
            result['text_length'] = len(cleaned_text)
            result['success'] = True
            
            print("\n✅ Processing complete!")
            print(f"  Text length: {result['text_length']} characters")
            print(f"  PDF path: {result['pdf_path']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def get_cached_text(self, arxiv_id: str) -> Optional[str]:
        """
        Get cached PDF text (if available)
        
        Args:
            arxiv_id: ArXiv ID
        
        Returns:
            Cached text content; returns None if not available
        """
        clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        pdf_path = self.cache_dir / f"{clean_id}.pdf"
        
        if pdf_path.exists():
            print(f"  🔍 Found cached PDF: {pdf_path}")
            text = self.extract_text(pdf_path)
            return self.clean_text(text) if text else None
        
        return None
    
    def clear_cache(self, arxiv_id: str = None):
        """
        Clear PDF cache
        
        Args:
            arxiv_id: If provided, delete only that paper's PDF;
                otherwise clear entire cache
        """
        if arxiv_id:
            clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
            pdf_path = self.cache_dir / f"{clean_id}.pdf"
            if pdf_path.exists():
                pdf_path.unlink()
                print(f"  ✅ Deleted cache: {pdf_path}")
        else:
            for pdf_file in self.cache_dir.glob("*.pdf"):
                pdf_file.unlink()
            print(f"  ✅ Cleared PDF cache directory")


def test_pdf_processor():
    """Test PDF processor"""
    processor = PDFProcessor()
    
    # Test a real ArXiv paper
    test_arxiv_id = "2301.00234"  # Replace with an actual ArXiv ID
    
    result = processor.process_paper(test_arxiv_id)
    
    if result['success']:
        print("\n" + "="*60)
        print("📊 Extraction preview:")
        print("="*60)
        print(result['full_text'][:1000] + "...")
        print("\n...")
        print(result['full_text'][-500:])
    else:
        print(f"\n❌ Test failed: {result['error']}")


if __name__ == "__main__":
    test_pdf_processor()
