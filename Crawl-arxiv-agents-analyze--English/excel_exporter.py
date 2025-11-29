#!/usr/bin/env python3
"""
Excel Export Module
Export paper data and analysis results to an Excel file
"""

import json
from typing import List, Dict
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print(
        "Warning: openpyxl library not installed. "
        "Please run: pip install openpyxl"
    )
    openpyxl = None


class ExcelExporter:
    def __init__(self):
        """Initialize the Excel exporter"""
        if openpyxl is None:
            raise ImportError(
                "openpyxl library not installed. Please run: "
                "pip install openpyxl"
            )
        
        self.workbook = None
    
    def export_papers(
        self,
        papers: List[Dict],
        output_file: str,
        include_abstract: bool = True,
    ):
        """
        Export paper data to Excel
        
        Args:
            papers: List of papers
            output_file: Output file path
            include_abstract: Whether to include abstracts
        """
        print(f"\nStarting export of {len(papers)} papers to Excel...")
        
        # Create workbook
        self.workbook = openpyxl.Workbook()
        ws = self.workbook.active
        ws.title = "Papers"
        
        # Set header styles
        header_font = Font(bold=True, size=12, color="FFFFFF")
        header_fill = PatternFill(
            start_color="4472C4", end_color="4472C4", fill_type="solid"
        )
        header_alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        
        # Define columns - include required fields: title, abstract,
        # authors, affiliations, task description, category info
        headers = [
            "No.", "arXiv ID", "Title", "Abstract", "Authors", "Affiliations",
            "Categories", "Published", "Task Description",
            "Category", "PDF URL", "ArXiv URL"
        ]
        
        # Write header
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Write data rows
        for row_idx, paper in enumerate(papers, 2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1)
            ws.cell(row=row_idx, column=2, value=paper.get('arxiv_id', 'N/A'))
            ws.cell(row=row_idx, column=3, value=paper.get('title', 'N/A'))
            
            # Abstract
            abstract = paper.get('abstract_cn') or paper.get('abstract', 'N/A')
            ws.cell(row=row_idx, column=4, value=abstract)
            
            # Authors
            authors = paper.get('authors', [])
            authors_str = ', '.join(authors) if authors else 'N/A'
            ws.cell(row=row_idx, column=5, value=authors_str)
            
            # Affiliations
            affiliations = paper.get('affiliations', [])
            affiliations_str = (
                '; '.join([a for a in affiliations if a and a.strip()])
                if affiliations else 'N/A'
            )
            ws.cell(row=row_idx, column=6, value=affiliations_str)
            
            # Categories
            categories = paper.get('categories', [])
            categories_str = ', '.join(categories) if categories else 'N/A'
            ws.cell(row=row_idx, column=7, value=categories_str)
            
            # Published date
            ws.cell(row=row_idx, column=8, value=paper.get('published', 'N/A'))
            
            # Task description
            ws.cell(
                row=row_idx, column=9,
                value=paper.get('task_description', 'N/A')
            )
            
            # Category (classification/clustering result)
            ws.cell(row=row_idx, column=10, value=paper.get('category', 'N/A'))
            
            # Links
            ws.cell(row=row_idx, column=11, value=paper.get('pdf_url', 'N/A'))
            arxiv_url = paper.get('arxiv_url') or paper.get('page_url', 'N/A')
            ws.cell(row=row_idx, column=12, value=arxiv_url)
        
        # Auto-adjust column widths
        self._adjust_column_widths(ws, headers)
        
        # 保存文件
        try:
            self.workbook.save(output_file)
            print(f"✅ Successfully exported to: {output_file}")
        except Exception as e:
            print(f"❌ Save failed: {e}")
    
    def export_classified_papers(
        self,
        classified_papers: Dict[str, List[Dict]],
        output_file: str,
    ):
        """
        Export classified paper data (one sheet per category)
        
        Args:
            classified_papers: Dictionary of classified papers
            output_file: Output file path
        """
        print("\nStarting export of classified papers to Excel...")
        
        # Create workbook
        self.workbook = openpyxl.Workbook()
        self.workbook.remove(self.workbook.active)  # Remove default sheet
        
        # Create summary worksheet
        summary_ws = self.workbook.create_sheet("Summary")
        self._create_summary_sheet(summary_ws, classified_papers)
        
        # Create a worksheet for each category
        for category, papers in classified_papers.items():
            # Excel worksheet name limit
            sheet_name = category[:31] if len(category) > 31 else category
            
            ws = self.workbook.create_sheet(sheet_name)
            self._fill_category_sheet(ws, papers, category)
        
        # Save file
        try:
            self.workbook.save(output_file)
            print(f"✅ Successfully exported to: {output_file}")
            print(f"   - Includes {len(classified_papers)} category sheets")
            total_count = sum(len(p) for p in classified_papers.values())
            print(f"   - Total {total_count} papers")
        except Exception as e:
            print(f"❌ Save failed: {e}")
    
    def _create_summary_sheet(
        self, ws, classified_papers: Dict[str, List[Dict]]
    ):
        """Create the summary worksheet"""
        # Title
        ws['A1'] = "Paper Classification Overview"
        ws['A1'].font = Font(bold=True, size=16)
        ws.merge_cells('A1:D1')
        
        # Statistics
        ws['A3'] = "Total Papers"
        ws['B3'] = sum(len(papers) for papers in classified_papers.values())
        
        ws['A4'] = "Number of Categories"
        ws['B4'] = len(classified_papers)
        
        ws['A5'] = "Generated At"
        ws['B5'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Category details header
        ws['A7'] = "Category Name"
        ws['B7'] = "Paper Count"
        ws['C7'] = "Percentage"
        
        # Set header styles
        for cell in [ws['A7'], ws['B7'], ws['C7']]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(
                start_color="4472C4", end_color="4472C4", fill_type="solid"
            )
            cell.font = Font(bold=True, color="FFFFFF")
        
        # Fill category data
        total_papers = sum(
            len(papers) for papers in classified_papers.values()
        )
        row = 8
        for category, papers in sorted(
            classified_papers.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        ):
            ws.cell(row=row, column=1, value=category)
            ws.cell(row=row, column=2, value=len(papers))
            ws.cell(row=row, column=3, value=f"{len(papers)/total_papers*100:.1f}%")
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
    
    def _fill_category_sheet(self, ws, papers: List[Dict], category: str):
        """Fill the category worksheet"""
        # Title
        ws['A1'] = f"Category: {category}"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:H1')
        
        # Header - include required fields: title, abstract, authors,
        # affiliations, task description, classification info
        headers = [
            "No.", "arXiv ID", "Title", "Abstract", "Authors",
            "Affiliations", "Task Description", "Published", "ArXiv URL"
        ]
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="4472C4", end_color="4472C4", fill_type="solid"
        )
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # Data rows
        for row_idx, paper in enumerate(papers, 3):
            ws.cell(row=row_idx, column=1, value=row_idx - 2)
            ws.cell(row=row_idx, column=2, value=paper.get('arxiv_id', 'N/A'))
            ws.cell(row=row_idx, column=3, value=paper.get('title', 'N/A'))
            
            # Abstract
            abstract = paper.get('abstract_cn') or paper.get('abstract', 'N/A')
            ws.cell(row=row_idx, column=4, value=abstract)
            
            # Authors
            authors = paper.get('authors', [])
            authors_str = ', '.join(authors) if authors else 'N/A'
            ws.cell(row=row_idx, column=5, value=authors_str)
            
            # Affiliations
            affiliations = paper.get('affiliations', [])
            affiliations_str = (
                '; '.join([a for a in affiliations if a and a.strip()])
                if affiliations else 'N/A'
            )
            ws.cell(row=row_idx, column=6, value=affiliations_str)
            
            # Task description
            ws.cell(
                row=row_idx,
                column=7,
                value=paper.get('task_description', 'N/A')
            )
            
            # Published date
            ws.cell(row=row_idx, column=8, value=paper.get('published', 'N/A'))
            
            # ArXiv URL
            arxiv_url = paper.get('arxiv_url') or paper.get('page_url', 'N/A')
            ws.cell(row=row_idx, column=9, value=arxiv_url)
        
        # Adjust width
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 60
        ws.column_dimensions['E'].width = 30
        ws.column_dimensions['F'].width = 40
        ws.column_dimensions['G'].width = 40
        ws.column_dimensions['H'].width = 15
        ws.column_dimensions['I'].width = 50
    
    def _adjust_column_widths(self, ws, headers):
        """Auto-adjust column widths"""
        column_widths = {
            "No.": 8,
            "arXiv ID": 15,
            "Title": 50,
            "Abstract": 60,
            "Authors": 30,
            "Affiliations": 40,
            "Categories": 20,
            "Published": 15,
            "Task Description": 40,
            "Category": 20,
            "PDF URL": 40,
            "ArXiv URL": 50
        }
        
        for col, header in enumerate(headers, 1):
            if header in column_widths:
                ws.column_dimensions[
                    get_column_letter(col)
                ].width = column_widths[header]


def export_to_excel(
    input_file: str,
    output_file: str = None,
    classified: bool = False,
):
    """
    Export paper data to Excel
    
    Args:
        input_file: Input JSON file
        output_file: Output Excel file path
        classified: Whether the data is classified
    """
    if openpyxl is None:
        print("❌ openpyxl must be installed: pip install openpyxl")
        return
    
    if not output_file:
        output_file = input_file.replace('.json', '.xlsx')
    
    print(f"\n{'='*60}")
    print("📊 Starting export to Excel")
    print(f"{'='*60}\n")
    
    # Read data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ Successfully loaded data file")
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return
    
    # Create exporter
    exporter = ExcelExporter()
    
    # Determine data type and export
    if classified or isinstance(data, dict) and 'classified_papers' in data:
        # Classified data
        if 'classified_papers' in data:
            classified_papers = data['classified_papers']
        else:
            classified_papers = data
        
        exporter.export_classified_papers(classified_papers, output_file)
    else:
        # Plain paper list
        if isinstance(data, list):
            papers = data
        elif isinstance(data, dict) and 'papers' in data:
            papers = data['papers']
        else:
            print("❌ Unrecognized data format")
            return
        
        exporter.export_papers(papers, output_file)
    
    print(f"\n{'='*60}")
    print("✅ Excel export complete")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export paper data to Excel')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    parser.add_argument('--output', '-o', help='Output Excel file path')
    parser.add_argument(
        '--classified', action='store_true',
        help='Whether the data is classified'
    )
    
    args = parser.parse_args()
    
    export_to_excel(args.input, args.output, args.classified)

