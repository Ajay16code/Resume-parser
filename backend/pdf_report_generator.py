"""
PDF Report Generator for Dataset Analysis
Generates comprehensive analysis reports in PDF format
"""

import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT


class DatasetAnalysisReportGenerator:
    """Generate detailed PDF analysis reports for datasets"""
    
    def __init__(self, csv_path: str):
        """
        Initialize report generator
        
        Args:
            csv_path: Path to CSV dataset
        """
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1F4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2E5C8A'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=16
        ))
        
        self.styles.add(ParagraphStyle(
            name='GoodPoint',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#228B22'),
            leftIndent=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='BadPoint',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#DC143C'),
            leftIndent=20
        ))
    
    def analyze_dataset(self) -> dict:
        """
        Perform comprehensive dataset analysis
        
        Returns:
            Dictionary containing analysis metrics
        """
        analysis = {
            'total_records': len(self.df),
            'columns': list(self.df.columns),
            'data_types': self.df.dtypes.to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'label_distribution': self.df['label'].value_counts().to_dict() if 'label' in self.df.columns else {},
            'text_stats': self._analyze_text_columns(),
            'class_balance': self._calculate_class_balance(),
            'data_quality': self._assess_data_quality()
        }
        return analysis
    
    def _analyze_text_columns(self) -> dict:
        """Analyze text columns statistics"""
        text_stats = {}
        text_cols = self.df.select_dtypes(include=['object']).columns
        
        for col in text_cols:
            text_stats[col] = {
                'avg_length': self.df[col].str.len().mean(),
                'min_length': self.df[col].str.len().min(),
                'max_length': self.df[col].str.len().max(),
                'avg_words': self.df[col].str.split().str.len().mean(),
            }
        return text_stats
    
    def _calculate_class_balance(self) -> dict:
        """Calculate class balance metrics"""
        if 'label' not in self.df.columns:
            return {}
        
        value_counts = self.df['label'].value_counts()
        total = len(self.df)
        
        return {
            'class_distribution': {
                str(k): {'count': int(v), 'percentage': round(v/total*100, 2)}
                for k, v in value_counts.items()
            },
            'imbalance_ratio': round(value_counts.max() / value_counts.min(), 2) if len(value_counts) > 1 else 1.0
        }
    
    def _assess_data_quality(self) -> dict:
        """Assess overall data quality"""
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_cells = self.df.isnull().sum().sum()
        completeness = round((1 - missing_cells/total_cells) * 100, 2)
        
        return {
            'completeness_percentage': completeness,
            'missing_cells': int(missing_cells),
            'total_cells': int(total_cells),
            'quality_grade': self._get_quality_grade(completeness)
        }
    
    def _get_quality_grade(self, completeness: float) -> str:
        """Determine data quality grade"""
        if completeness >= 95:
            return "Excellent"
        elif completeness >= 85:
            return "Good"
        elif completeness >= 70:
            return "Fair"
        else:
            return "Poor"
    
    def generate_pdf(self) -> bytes:
        """
        Generate complete PDF report
        
        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Dataset Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        metadata = [
            [f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            [f"Dataset: sample_dataset.csv"],
            [f"Total Records: {len(self.df)}"]
        ]
        metadata_table = Table(metadata, colWidths=[6*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F0F0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 1. Executive Summary
        story.append(self._build_executive_summary())
        story.append(Spacer(1, 0.2*inch))
        
        # 2. Dataset Overview
        story.append(self._build_dataset_overview())
        story.append(Spacer(1, 0.2*inch))
        
        # 3. Data Quality Assessment
        story.append(self._build_quality_assessment())
        story.append(Spacer(1, 0.2*inch))
        
        # 4. Detailed Analysis
        story.append(self._build_detailed_analysis())
        story.append(Spacer(1, 0.2*inch))
        
        # 5. Storage Format Analysis
        story.append(self._build_storage_format_analysis())
        story.append(Spacer(1, 0.2*inch))
        
        # 6. Methodology
        story.append(self._build_methodology())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _build_executive_summary(self) -> KeepTogether:
        """Build executive summary section"""
        analysis = self.analyze_dataset()
        
        content = [
            Paragraph("1. Executive Summary", self.styles['CustomHeading']),
            Paragraph(
                f"This report provides a comprehensive analysis of the resume-job matching dataset. "
                f"The dataset contains <b>{analysis['total_records']} records</b> with "
                f"<b>{len(analysis['columns'])} columns</b>. The data quality assessment indicates "
                f"<b>{analysis['data_quality']['quality_grade']}</b> grade with "
                f"<b>{analysis['data_quality']['completeness_percentage']}%</b> completeness. "
                f"The dataset is designed for training machine learning models to match resumes with job descriptions.",
                self.styles['CustomBody']
            ),
            Spacer(1, 0.15*inch)
        ]
        return KeepTogether(content)
    
    def _build_dataset_overview(self) -> KeepTogether:
        """Build dataset overview section"""
        analysis = self.analyze_dataset()
        
        content = [
            Paragraph("2. Dataset Overview", self.styles['CustomHeading']),
        ]
        
        # Column Information
        col_data = [['Column Name', 'Data Type', 'Missing Values']]
        for col in analysis['columns']:
            col_data.append([
                col,
                str(analysis['data_types'][col]),
                str(analysis['missing_values'].get(col, 0))
            ])
        
        col_table = Table(col_data, colWidths=[2*inch, 2*inch, 2*inch])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5C8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        content.append(col_table)
        content.append(Spacer(1, 0.15*inch))
        
        # Class Distribution
        if analysis['class_balance']:
            content.append(Paragraph("<b>Class Distribution:</b>", self.styles['CustomBody']))
            class_data = [['Class', 'Count', 'Percentage']]
            for cls, info in analysis['class_balance']['class_distribution'].items():
                class_data.append([cls, str(info['count']), f"{info['percentage']}%"])
            
            class_table = Table(class_data, colWidths=[2*inch, 2*inch, 2*inch])
            class_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5C8A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            content.append(class_table)
            content.append(Spacer(1, 0.1*inch))
        
        return KeepTogether(content)
    
    def _build_quality_assessment(self) -> KeepTogether:
        """Build data quality assessment section"""
        analysis = self.analyze_dataset()
        quality = analysis['data_quality']
        
        content = [
            Paragraph("3. Data Quality Assessment", self.styles['CustomHeading']),
            Paragraph(
                f"<b>Quality Grade:</b> {quality['quality_grade']}<br/>"
                f"<b>Completeness:</b> {quality['completeness_percentage']}%<br/>"
                f"<b>Missing Cells:</b> {quality['missing_cells']} out of {quality['total_cells']}<br/>",
                self.styles['CustomBody']
            ),
            Spacer(1, 0.1*inch)
        ]
        
        return KeepTogether(content)
    
    def _build_detailed_analysis(self) -> KeepTogether:
        """Build detailed analysis section"""
        analysis = self.analyze_dataset()
        text_stats = analysis['text_stats']
        
        content = [
            Paragraph("4. Detailed Text Analysis", self.styles['CustomHeading']),
        ]
        
        for col, stats in text_stats.items():
            content.append(Paragraph(f"<b>{col}:</b>", self.styles['CustomBody']))
            stats_text = (
                f"• Average Length: {stats['avg_length']:.0f} characters<br/>"
                f"• Min Length: {stats['min_length']:.0f} characters<br/>"
                f"• Max Length: {stats['max_length']:.0f} characters<br/>"
                f"• Average Words: {stats['avg_words']:.0f} words<br/>"
            )
            content.append(Paragraph(stats_text, self.styles['CustomBody']))
            content.append(Spacer(1, 0.1*inch))
        
        return KeepTogether(content)
    
    def _build_storage_format_analysis(self) -> KeepTogether:
        """Build storage format analysis (PDF vs CSV vs Parquet)"""
        content = [
            Paragraph("5. Storage Format Analysis: CSV vs PDF vs Parquet", self.styles['CustomHeading']),
            Spacer(1, 0.1*inch)
        ]
        
        # CSV Analysis
        content.append(Paragraph("<b>CSV (Comma-Separated Values) - Current Format:</b>", self.styles['CustomBody']))
        
        good_csv = [
            "✓ Human-readable and easy to view in text editors",
            "✓ Universally compatible across all platforms and tools",
            "✓ Small file size for text-based data storage",
            "✓ Easy to parse and process with any programming language",
            "✓ Good for data exchange between different systems",
            "✓ Efficient for streaming and incremental reads"
        ]
        
        for point in good_csv:
            content.append(Paragraph(point, self.styles['GoodPoint']))
        
        content.append(Spacer(1, 0.08*inch))
        
        bad_csv = [
            "✗ No native support for complex data types or hierarchies",
            "✗ Delimiter conflicts when data contains commas",
            "✗ No built-in compression - larger files than binary formats",
            "✗ Slower performance for very large datasets (millions of rows)",
            "✗ No support for formatting or metadata preservation",
            "✗ Requires full rebuild to add columns or modify structure"
        ]
        
        for point in bad_csv:
            content.append(Paragraph(point, self.styles['BadPoint']))
        
        content.append(Spacer(1, 0.15*inch))
        
        # PDF Analysis
        content.append(Paragraph("<b>PDF - Report Format (NOT for data storage):</b>", self.styles['CustomBody']))
        
        good_pdf = [
            "✓ Professional, stable, formatted documents",
            "✓ Preserves layout and typography consistently",
            "✓ Excellent for distribution and sharing",
            "✓ Supports multimedia (images, links, fonts)"
        ]
        
        for point in good_pdf:
            content.append(Paragraph(point, self.styles['GoodPoint']))
        
        content.append(Spacer(1, 0.08*inch))
        
        bad_pdf = [
            "✗ NOT suitable for data storage or analysis",
            "✗ Very difficult to extract and parse structured data from",
            "✗ Large file sizes compared to text formats",
            "✗ Cannot efficiently query or filter data",
            "✗ Data modification requires regeneration",
            "✗ Not designed for machine learning workflows"
        ]
        
        for point in bad_pdf:
            content.append(Paragraph(point, self.styles['BadPoint']))
        
        content.append(Spacer(1, 0.15*inch))
        
        # Parquet Analysis
        content.append(Paragraph("<b>Parquet - Recommended for Production:</b>", self.styles['CustomBody']))
        
        good_parquet = [
            "✓ Columnar format optimized for analytics",
            "✓ Excellent compression (50-80% size reduction)",
            "✓ Fast read/write performance, especially for analytics",
            "✓ Native support for complex data types",
            "✓ Supports predicate pushdown for efficient filtering",
            "✓ Industry standard in big data and ML ecosystems"
        ]
        
        for point in good_parquet:
            content.append(Paragraph(point, self.styles['GoodPoint']))
        
        content.append(Spacer(1, 0.08*inch))
        
        bad_parquet = [
            "✗ Not human-readable in text editors",
            "✗ Slightly steeper learning curve",
            "✗ Requires specialized libraries to read",
            "✗ Less suitable for data exchange with non-technical users"
        ]
        
        for point in bad_parquet:
            content.append(Paragraph(point, self.styles['BadPoint']))
        
        content.append(Spacer(1, 0.1*inch))
        
        # Recommendation
        content.append(Paragraph("<b>Recommendation:</b>", self.styles['CustomBody']))
        recommendation = (
            "For this resume-job matching dataset: <br/>"
            "• <b>CSV:</b> Keep for data import/export and sharing with non-technical stakeholders<br/>"
            "• <b>PDF:</b> Use for reports, analysis documentation, and stakeholder presentations (current approach)<br/>"
            "• <b>Parquet:</b> Recommended for production ML pipelines and large-scale data processing<br/>"
        )
        content.append(Paragraph(recommendation, self.styles['CustomBody']))
        
        return KeepTogether(content)
    
    def _build_methodology(self) -> KeepTogether:
        """Build methodology section"""
        content = [
            Paragraph("6. Analysis Methodology", self.styles['CustomHeading']),
            Paragraph(
                "<b>Data Collection & Preparation:</b><br/>"
                "The dataset was loaded from CSV format and validated for completeness. "
                "All columns were analyzed for data types, missing values, and statistical properties.",
                self.styles['CustomBody']
            ),
            Spacer(1, 0.1*inch),
            
            Paragraph(
                "<b>Text Analysis:</b><br/>"
                "For text columns (resume_text and job_description), we calculated:<br/>"
                "• Average character length and word count<br/>"
                "• Minimum and maximum text lengths<br/>"
                "• Distribution analysis<br/>",
                self.styles['CustomBody']
            ),
            Spacer(1, 0.1*inch),
            
            Paragraph(
                "<b>Quality Metrics:</b><br/>"
                "Data quality was assessed using:<br/>"
                "• Completeness: (Total Cells - Missing Cells) / Total Cells × 100<br/>"
                "• Class Balance: Ratio of majority class to minority class<br/>"
                "• Missing Value Analysis: Identification of null/empty cells<br/>",
                self.styles['CustomBody']
            ),
            Spacer(1, 0.1*inch),
            
            Paragraph(
                "<b>Format Comparison:</b><br/>"
                "Storage formats were evaluated based on use cases: data storage, analytics, "
                "performance, compatibility, and ease of use. Each format was rated for production ML workflows.",
                self.styles['CustomBody']
            ),
        ]
        
        return KeepTogether(content)
