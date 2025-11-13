#!/usr/bin/env python3
"""
Excel导出模块
将论文数据和分析结果导出为Excel文件
"""

import json
from typing import List, Dict
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Warning: openpyxl库未安装。请运行: pip install openpyxl")
    openpyxl = None


class ExcelExporter:
    def __init__(self):
        """初始化Excel导出器"""
        if openpyxl is None:
            raise ImportError("openpyxl库未安装。请运行: pip install openpyxl")
        
        self.workbook = None
    
    def export_papers(self, papers: List[Dict], output_file: str, 
                     include_abstract: bool = True):
        """
        导出论文数据到Excel
        
        Args:
            papers: 论文列表
            output_file: 输出文件路径
            include_abstract: 是否包含摘要
        """
        print(f"\n开始导出 {len(papers)} 篇论文到Excel...")
        
        # 创建工作簿
        self.workbook = openpyxl.Workbook()
        ws = self.workbook.active
        ws.title = "Papers"
        
        # 设置标题样式
        header_font = Font(bold=True, size=12, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # 定义列 - 包含所有必需字段：标题、摘要、作者、作者单位、任务描述、分类信息
        headers = ["序号", "arXiv ID", "标题", "摘要", "作者", "作者单位", "分类", "发布日期", "任务描述", "类别", "PDF链接", "ArXiv链接"]
        
        # 写入标题行
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # 写入数据
        for row_idx, paper in enumerate(papers, 2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1)
            ws.cell(row=row_idx, column=2, value=paper.get('arxiv_id', 'N/A'))
            ws.cell(row=row_idx, column=3, value=paper.get('title', 'N/A'))
            
            # 摘要
            abstract = paper.get('abstract_cn') or paper.get('abstract', 'N/A')
            ws.cell(row=row_idx, column=4, value=abstract)
            
            # 作者列表
            authors = paper.get('authors', [])
            authors_str = ', '.join(authors) if authors else 'N/A'
            ws.cell(row=row_idx, column=5, value=authors_str)
            
            # 作者单位
            affiliations = paper.get('affiliations', [])
            affiliations_str = '; '.join([a for a in affiliations if a and a.strip()]) if affiliations else 'N/A'
            ws.cell(row=row_idx, column=6, value=affiliations_str)
            
            # 分类
            categories = paper.get('categories', [])
            categories_str = ', '.join(categories) if categories else 'N/A'
            ws.cell(row=row_idx, column=7, value=categories_str)
            
            # 发布日期
            ws.cell(row=row_idx, column=8, value=paper.get('published', 'N/A'))
            
            # 任务描述
            ws.cell(row=row_idx, column=9, value=paper.get('task_description', 'N/A'))
            
            # 类别（分类/聚类结果）
            ws.cell(row=row_idx, column=10, value=paper.get('category', 'N/A'))
            
            # 链接
            ws.cell(row=row_idx, column=11, value=paper.get('pdf_url', 'N/A'))
            arxiv_url = paper.get('arxiv_url') or paper.get('page_url', 'N/A')
            ws.cell(row=row_idx, column=12, value=arxiv_url)
        
        # 自动调整列宽
        self._adjust_column_widths(ws, headers)
        
        # 保存文件
        try:
            self.workbook.save(output_file)
            print(f"✅ 成功导出到: {output_file}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def export_classified_papers(self, classified_papers: Dict[str, List[Dict]], 
                                output_file: str):
        """
        导出分类后的论文数据（每个类别一个工作表）
        
        Args:
            classified_papers: 分类后的论文字典
            output_file: 输出文件路径
        """
        print(f"\n开始导出分类论文数据到Excel...")
        
        # 创建工作簿
        self.workbook = openpyxl.Workbook()
        self.workbook.remove(self.workbook.active)  # 删除默认工作表
        
        # 创建总览工作表
        summary_ws = self.workbook.create_sheet("总览")
        self._create_summary_sheet(summary_ws, classified_papers)
        
        # 为每个类别创建一个工作表
        for category, papers in classified_papers.items():
            # Excel工作表名称限制
            sheet_name = category[:31] if len(category) > 31 else category
            
            ws = self.workbook.create_sheet(sheet_name)
            self._fill_category_sheet(ws, papers, category)
        
        # 保存文件
        try:
            self.workbook.save(output_file)
            print(f"✅ 成功导出到: {output_file}")
            print(f"   - 包含 {len(classified_papers)} 个类别工作表")
            print(f"   - 共 {sum(len(p) for p in classified_papers.values())} 篇论文")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def _create_summary_sheet(self, ws, classified_papers: Dict[str, List[Dict]]):
        """创建总览工作表"""
        # 标题
        ws['A1'] = "论文分类总览"
        ws['A1'].font = Font(bold=True, size=16)
        ws.merge_cells('A1:D1')
        
        # 统计信息
        ws['A3'] = "总论文数"
        ws['B3'] = sum(len(papers) for papers in classified_papers.values())
        
        ws['A4'] = "类别数量"
        ws['B4'] = len(classified_papers)
        
        ws['A5'] = "生成时间"
        ws['B5'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 类别详情表头
        ws['A7'] = "类别名称"
        ws['B7'] = "论文数量"
        ws['C7'] = "占比"
        
        # 设置表头样式
        for cell in [ws['A7'], ws['B7'], ws['C7']]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        
        # 填充类别数据
        total_papers = sum(len(papers) for papers in classified_papers.values())
        row = 8
        for category, papers in sorted(classified_papers.items(), key=lambda x: len(x[1]), reverse=True):
            ws.cell(row=row, column=1, value=category)
            ws.cell(row=row, column=2, value=len(papers))
            ws.cell(row=row, column=3, value=f"{len(papers)/total_papers*100:.1f}%")
            row += 1
        
        # 调整列宽
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
    
    def _fill_category_sheet(self, ws, papers: List[Dict], category: str):
        """填充类别工作表"""
        # 标题
        ws['A1'] = f"类别: {category}"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:H1')
        
        # 表头 - 包含所有必需字段：标题、摘要、作者、作者单位、任务描述、分类信息
        headers = ["序号", "arXiv ID", "标题", "摘要", "作者", "作者单位", "任务描述", "发布日期", "ArXiv链接"]
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # 数据
        for row_idx, paper in enumerate(papers, 3):
            ws.cell(row=row_idx, column=1, value=row_idx - 2)
            ws.cell(row=row_idx, column=2, value=paper.get('arxiv_id', 'N/A'))
            ws.cell(row=row_idx, column=3, value=paper.get('title', 'N/A'))
            
            # 摘要
            abstract = paper.get('abstract_cn') or paper.get('abstract', 'N/A')
            ws.cell(row=row_idx, column=4, value=abstract)
            
            # 作者
            authors = paper.get('authors', [])
            authors_str = ', '.join(authors) if authors else 'N/A'
            ws.cell(row=row_idx, column=5, value=authors_str)
            
            # 作者单位
            affiliations = paper.get('affiliations', [])
            affiliations_str = '; '.join([a for a in affiliations if a and a.strip()]) if affiliations else 'N/A'
            ws.cell(row=row_idx, column=6, value=affiliations_str)
            
            # 任务描述
            ws.cell(row=row_idx, column=7, value=paper.get('task_description', 'N/A'))
            
            # 发布日期
            ws.cell(row=row_idx, column=8, value=paper.get('published', 'N/A'))
            
            # ArXiv链接
            arxiv_url = paper.get('arxiv_url') or paper.get('page_url', 'N/A')
            ws.cell(row=row_idx, column=9, value=arxiv_url)
        
        # 调整列宽
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
        """自动调整列宽"""
        column_widths = {
            "序号": 8,
            "arXiv ID": 15,
            "标题": 50,
            "摘要": 60,
            "作者": 30,
            "作者单位": 40,
            "分类": 20,
            "发布日期": 15,
            "任务描述": 40,
            "类别": 20,
            "PDF链接": 40,
            "ArXiv链接": 50
        }
        
        for col, header in enumerate(headers, 1):
            if header in column_widths:
                ws.column_dimensions[get_column_letter(col)].width = column_widths[header]


def export_to_excel(input_file: str, output_file: str = None, 
                   classified: bool = False):
    """
    导出论文数据到Excel
    
    Args:
        input_file: 输入JSON文件
        output_file: 输出Excel文件路径
        classified: 是否为分类数据
    """
    if openpyxl is None:
        print("❌ 需要安装 openpyxl 库: pip install openpyxl")
        return
    
    if not output_file:
        output_file = input_file.replace('.json', '.xlsx')
    
    print(f"\n{'='*60}")
    print("📊 开始导出到Excel")
    print(f"{'='*60}\n")
    
    # 读取数据
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 成功加载数据文件")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 创建导出器
    exporter = ExcelExporter()
    
    # 判断数据类型并导出
    if classified or isinstance(data, dict) and 'classified_papers' in data:
        # 分类数据
        if 'classified_papers' in data:
            classified_papers = data['classified_papers']
        else:
            classified_papers = data
        
        exporter.export_classified_papers(classified_papers, output_file)
    else:
        # 普通论文列表
        if isinstance(data, list):
            papers = data
        elif isinstance(data, dict) and 'papers' in data:
            papers = data['papers']
        else:
            print("❌ 无法识别的数据格式")
            return
        
        exporter.export_papers(papers, output_file)
    
    print(f"\n{'='*60}")
    print("✅ Excel导出完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='导出论文数据到Excel')
    parser.add_argument('--input', '-i', required=True, help='输入JSON文件')
    parser.add_argument('--output', '-o', help='输出Excel文件路径')
    parser.add_argument('--classified', action='store_true', help='是否为分类数据')
    
    args = parser.parse_args()
    
    export_to_excel(args.input, args.output, args.classified)

