"""
文档处理核心模块
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

# PDF处理
import fitz  # PyMuPDF
import pdfplumber
import PyPDF2

# 文本处理
import requests
from bs4 import BeautifulSoup
import markdown

# 元数据解析
import bibtexparser
from doi2bib import crossref
import arxiv


@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: str = ""
    authors: List[str] = None
    year: int = None
    journal: str = ""
    doi: str = ""
    abstract: str = ""
    keywords: List[str] = None
    pages: str = ""
    volume: str = ""
    issue: str = ""
    publisher: str = ""
    language: str = "en"
    document_type: str = "unknown"  # pdf, html, txt, etc.
    file_path: str = ""
    file_size: int = 0
    checksum: str = ""
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []


@dataclass
class ProcessedDocument:
    """处理后的文档"""
    metadata: DocumentMetadata
    content: str = ""
    sections: Dict[str, str] = None
    images: List[Dict[str, Any]] = None
    tables: List[Dict[str, Any]] = None
    references: List[str] = None
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = {}
        if self.images is None:
            self.images = []
        if self.tables is None:
            self.tables = []
        if self.references is None:
            self.references = []


class BaseProcessor(ABC):
    """文档处理器基类"""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """检查是否能处理该文件"""
        pass
    
    @abstractmethod
    def extract_content(self, file_path: str) -> ProcessedDocument:
        """提取文档内容"""
        pass
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class PDFProcessor(BaseProcessor):
    """PDF文档处理器"""
    
    def can_process(self, file_path: str) -> bool:
        """检查是否为PDF文件"""
        return file_path.lower().endswith('.pdf')
    
    def extract_content(self, file_path: str) -> ProcessedDocument:
        """提取PDF内容"""
        metadata = self._extract_metadata(file_path)
        content, sections = self._extract_text_and_sections(file_path)
        images = self._extract_images(file_path)
        tables = self._extract_tables(file_path)
        references = self._extract_references(content)
        
        return ProcessedDocument(
            metadata=metadata,
            content=content,
            sections=sections,
            images=images,
            tables=tables,
            references=references
        )
    
    def _extract_metadata(self, file_path: str) -> DocumentMetadata:
        """提取PDF元数据"""
        metadata = DocumentMetadata(
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            document_type="pdf"
        )
        
        # 计算校验和
        metadata.checksum = self._calculate_checksum(file_path)
        
        try:
            # 使用PyMuPDF提取元数据
            doc = fitz.open(file_path)
            pdf_metadata = doc.metadata
            
            metadata.title = pdf_metadata.get('title', '').strip()
            metadata.authors = [author.strip() for author in pdf_metadata.get('author', '').split(';') if author.strip()]
            metadata.year = self._extract_year(pdf_metadata.get('creationDate', ''))
            metadata.journal = pdf_metadata.get('subject', '').strip()
            metadata.publisher = pdf_metadata.get('producer', '').strip()
            
            doc.close()
            
            # 尝试从DOI提取更多信息
            if metadata.doi or self._find_doi_in_content(file_path):
                self._enrich_metadata_from_doi(metadata)
                
        except Exception as e:
            print(f"PDF元数据提取失败: {e}")
        
        return metadata
    
    def _extract_text_and_sections(self, file_path: str) -> Tuple[str, Dict[str, str]]:
        """提取文本和章节"""
        content = ""
        sections = {}
        current_section = ""
        section_content = []
        
        try:
            # 使用pdfplumber提取文本（保留格式）
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
                        
                        # 简单的章节识别
                        lines = page_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if self._is_section_header(line):
                                if current_section and section_content:
                                    sections[current_section] = '\n'.join(section_content)
                                current_section = line
                                section_content = []
                            else:
                                section_content.append(line)
            
            # 添加最后一个章节
            if current_section and section_content:
                sections[current_section] = '\n'.join(section_content)
                
        except Exception as e:
            print(f"PDF文本提取失败: {e}")
            # 回退到PyMuPDF
            try:
                doc = fitz.open(file_path)
                content = ""
                for page in doc:
                    content += page.get_text()
                doc.close()
            except Exception as e2:
                print(f"备用PDF文本提取也失败: {e2}")
        
        return content, sections
    
    def _extract_images(self, file_path: str) -> List[Dict[str, Any]]:
        """提取图片信息"""
        images = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n - pix.alpha < 4:  # 确保不是CMYK
                            img_info = {
                                "page": page_num + 1,
                                "index": img_index,
                                "width": pix.width,
                                "height": pix.height,
                                "colorspace": pix.colorspace.name if pix.colorspace else "unknown"
                            }
                            images.append(img_info)
                        pix = None
                    except Exception as e:
                        print(f"图片信息提取失败: {e}")
            doc.close()
        except Exception as e:
            print(f"PDF图片提取失败: {e}")
        
        return images
    
    def _extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """提取表格信息"""
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_index, table in enumerate(page_tables):
                        if table and len(table) > 1:  # 至少有标题和一行数据
                            table_info = {
                                "page": page_num + 1,
                                "index": table_index,
                                "rows": len(table),
                                "cols": len(table[0]) if table else 0,
                                "data": table
                            }
                            tables.append(table_info)
        except Exception as e:
            print(f"PDF表格提取失败: {e}")
        
        return tables
    
    def _extract_references(self, content: str) -> List[str]:
        """提取参考文献"""
        references = []
        
        # 简单的参考文献识别模式
        ref_patterns = [
            r'\[(\d+)\]\s+([^\n]+)',  # [1] Author, Title, Journal
            r'(\d+\.\s+[A-Z][^.\n]+\. [^.\n]+\. [^.\n]+\. )',  # 1. Author. Title. Journal.
        ]
        
        for pattern in ref_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    ref = match[-1]  # 取最后一个元素（引用内容）
                else:
                    ref = match
                ref = ref.strip()
                if ref and len(ref) > 20:  # 过滤太短的匹配
                    references.append(ref)
        
        return references
    
    def _is_section_header(self, line: str) -> bool:
        """判断是否为章节标题"""
        # 简单的章节标题识别规则
        if not line:
            return False
        
        # 数字开头的章节（如 1. Introduction）
        if re.match(r'^\d+\.+\s+[A-Z]', line):
            return True
        
        # 常见章节名称
        common_sections = [
            'abstract', 'introduction', 'methods', 'results', 'discussion',
            'conclusion', 'references', 'acknowledgments', 'background',
            '摘要', '引言', '方法', '结果', '讨论', '结论', '参考文献'
        ]
        
        line_lower = line.lower()
        for section in common_sections:
            if section in line_lower and len(line) < 100:
                return True
        
        return False
    
    def _extract_year(self, date_str: str) -> Optional[int]:
        """从日期字符串中提取年份"""
        if not date_str:
            return None
        
        # 尝试匹配4位数字年份
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return int(year_match.group())
        
        return None
    
    def _find_doi_in_content(self, file_path: str) -> Optional[str]:
        """在文档内容中查找DOI"""
        try:
            doc = fitz.open(file_path)
            content = ""
            for page in doc:
                content += page.get_text()
            doc.close()
            
            # DOI正则表达式
            doi_pattern = r'(?:doi:|DOI:)?\s*(10\.\d+/[^\s]+)'
            matches = re.findall(doi_pattern, content, re.IGNORECASE)
            if matches:
                return matches[0]
        except Exception as e:
            print(f"DOI查找失败: {e}")
        
        return None
    
    def _enrich_metadata_from_doi(self, metadata: DocumentMetadata):
        """通过DOI丰富元数据"""
        if not metadata.doi:
            return
        
        try:
            # 使用CrossRef API获取元数据
            response = requests.get(f"https://api.crossref.org/works/{metadata.doi}")
            if response.status_code == 200:
                data = response.json()
                work = data.get('message', {})
                
                if not metadata.title and 'title' in work:
                    metadata.title = work['title'][0] if work['title'] else ""
                
                if not metadata.authors and 'author' in work:
                    metadata.authors = [f"{author.get('given', '')} {author.get('family', '')}".strip() 
                                      for author in work['author']]
                
                if not metadata.journal and 'container-title' in work:
                    metadata.journal = work['container-title'][0] if work['container-title'] else ""
                
                if not metadata.year and 'published-print' in work:
                    date_parts = work['published-print'].get('date-parts', [[]])[0]
                    if date_parts and len(date_parts) > 0:
                        metadata.year = date_parts[0]
                
                if 'abstract' in work:
                    metadata.abstract = work['abstract']
                    
        except Exception as e:
            print(f"DOI元数据获取失败: {e}")


class HTMLProcessor(BaseProcessor):
    """HTML文档处理器"""
    
    def can_process(self, file_path: str) -> bool:
        """检查是否为HTML文件"""
        return file_path.lower().endswith(('.html', '.htm'))
    
    def extract_content(self, file_path: str) -> ProcessedDocument:
        """提取HTML内容"""
        metadata = DocumentMetadata(
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            document_type="html"
        )
        
        # 计算校验和
        metadata.checksum = self._calculate_checksum(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取元数据
            metadata.title = self._extract_title(soup)
            metadata.authors = self._extract_authors(soup)
            metadata.abstract = self._extract_abstract(soup)
            metadata.year = self._extract_year(soup)
            
            # 提取内容
            content = self._extract_text_content(soup)
            sections = self._extract_sections(soup)
            
            return ProcessedDocument(
                metadata=metadata,
                content=content,
                sections=sections
            )
            
        except Exception as e:
            print(f"HTML处理失败: {e}")
            return ProcessedDocument(metadata=metadata)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种标题标签
        title_selectors = ['h1', 'title', '.title', '#title', '[property="og:title"]']
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return ""
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """提取作者信息"""
        authors = []
        
        # 常见作者选择器
        author_selectors = [
            '.author', '.authors', '[rel="author"]', 
            '.byline', '.author-name', '.contributor'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                author_text = element.get_text().strip()
                if author_text and len(author_text) < 100:  # 过滤太长的文本
                    authors.append(author_text)
        
        return authors
    
    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """提取摘要"""
        abstract_selectors = [
            '.abstract', '#abstract', '[name="description"]',
            '.summary', '.description'
        ]
        
        for selector in abstract_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return ""
    
    def _extract_year(self, soup: BeautifulSoup) -> Optional[int]:
        """提取年份"""
        # 尝试从元数据中提取年份
        year_patterns = [
            '[name="citation_publication_date"]',
            '[name="citation_year"]',
            '[property="article:published_time"]',
            '.publication-date', '.year'
        ]
        
        for selector in year_patterns:
            element = soup.select_one(selector)
            if element:
                content = element.get('content') or element.get_text()
                year_match = re.search(r'\b(19|20)\d{2}\b', content)
                if year_match:
                    return int(year_match.group())
        
        return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """提取纯文本内容"""
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 获取主要内容区域
        content_selectors = [
            '.content', '.article-content', '.post-content',
            'main', 'article', '.entry-content'
        ]
        
        content_element = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content_element = element
                break
        
        if not content_element:
            content_element = soup
        
        return content_element.get_text(separator='\n', strip=True)
    
    def _extract_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取章节"""
        sections = {}
        
        # 查找所有标题
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            title = heading.get_text().strip()
            if title:
                # 获取标题后的内容直到下一个标题
                content = []
                next_element = heading.next_sibling
                
                while next_element:
                    if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    if hasattr(next_element, 'get_text'):
                        text = next_element.get_text().strip()
                        if text:
                            content.append(text)
                    next_element = next_element.next_sibling
                
                if content:
                    sections[title] = '\n'.join(content)
        
        return sections


class TextProcessor(BaseProcessor):
    """文本文档处理器"""
    
    def can_process(self, file_path: str) -> bool:
        """检查是否为文本文件"""
        return file_path.lower().endswith(('.txt', '.md'))
    
    def extract_content(self, file_path: str) -> ProcessedDocument:
        """提取文本内容"""
        metadata = DocumentMetadata(
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            document_type="txt" if file_path.lower().endswith('.txt') else "md"
        )
        
        # 计算校验和
        metadata.checksum = self._calculate_checksum(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果是Markdown文件，先转换为HTML再处理
            if file_path.lower().endswith('.md'):
                html_content = markdown.markdown(content)
                soup = BeautifulSoup(html_content, 'html.parser')
                
                metadata.title = self._extract_title_from_markdown(content, soup)
                metadata.authors = self._extract_authors_from_markdown(content)
                metadata.abstract = self._extract_abstract_from_markdown(content)
                
                # 提取章节
                sections = self._extract_sections_from_markdown(content)
            else:
                # 纯文本文件
                metadata.title = self._extract_title_from_text(content)
                sections = self._extract_sections_from_text(content)
            
            return ProcessedDocument(
                metadata=metadata,
                content=content,
                sections=sections
            )
            
        except Exception as e:
            print(f"文本处理失败: {e}")
            return ProcessedDocument(metadata=metadata)
    
    def _extract_title_from_markdown(self, content: str, soup: BeautifulSoup) -> str:
        """从Markdown中提取标题"""
        # 首先尝试从HTML中提取
        title_element = soup.find('h1')
        if title_element:
            return title_element.get_text().strip()
        
        # 然后尝试从Markdown中提取
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        
        return ""
    
    def _extract_title_from_text(self, content: str) -> str:
        """从纯文本中提取标题"""
        lines = content.split('\n')
        for line in lines[:10]:  # 只检查前10行
            line = line.strip()
            if line and len(line) < 100 and not line.endswith('.'):
                return line
        
        return ""
    
    def _extract_authors_from_markdown(self, content: str) -> List[str]:
        """从Markdown中提取作者"""
        authors = []
        lines = content.split('\n')
        
        for line in lines[:20]:  # 只检查前20行
            line = line.strip().lower()
            if 'author' in line or '作者' in line:
                # 简单的作者提取逻辑
                author_match = re.search(r'[:：]\s*([^,\n]+)', line)
                if author_match:
                    authors.append(author_match.group(1).strip())
        
        return authors
    
    def _extract_abstract_from_markdown(self, content: str) -> str:
        """从Markdown中提取摘要"""
        lines = content.split('\n')
        abstract_lines = []
        in_abstract = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if 'abstract' in line_lower or '摘要' in line_lower:
                in_abstract = True
                continue
            elif in_abstract and line.startswith('#'):
                break
            elif in_abstract and line.strip():
                abstract_lines.append(line.strip())
        
        return '\n'.join(abstract_lines)
    
    def _extract_sections_from_markdown(self, content: str) -> Dict[str, str]:
        """从Markdown中提取章节"""
        sections = {}
        lines = content.split('\n')
        current_section = ""
        section_content = []
        
        for line in lines:
            if line.startswith('#'):
                # 保存上一个章节
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                
                # 开始新章节
                current_section = line.lstrip('# ').strip()
                section_content = []
            else:
                if current_section:
                    section_content.append(line)
        
        # 保存最后一个章节
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    def _extract_sections_from_text(self, content: str) -> Dict[str, str]:
        """从纯文本中提取章节"""
        sections = {}
        lines = content.split('\n')
        current_section = ""
        section_content = []
        
        for line in lines:
            line = line.strip()
            if self._is_likely_section_header(line):
                # 保存上一个章节
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                
                # 开始新章节
                current_section = line
                section_content = []
            else:
                if current_section or line:  # 如果还没有章节，任何非空行都开始一个章节
                    if not current_section:
                        current_section = "内容"
                    section_content.append(line)
        
        # 保存最后一个章节
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    def _is_likely_section_header(self, line: str) -> bool:
        """判断是否可能是章节标题"""
        if not line or len(line) > 100:
            return False
        
        # 全大写或首字母大写的短行
        if line.isupper() or (line[0].isupper() and line.count(' ') < 10):
            return True
        
        # 包含常见章节关键词
        section_keywords = [
            'introduction', 'methods', 'results', 'discussion', 'conclusion',
            '引言', '方法', '结果', '讨论', '结论'
        ]
        
        line_lower = line.lower()
        for keyword in section_keywords:
            if keyword in line_lower:
                return True
        
        return False


class DocumentProcessor:
    """文档处理器主类"""
    
    def __init__(self):
        self.processors = [
            PDFProcessor(),
            HTMLProcessor(),
            TextProcessor()
        ]
    
    def process(self, file_path: str) -> Optional[ProcessedDocument]:
        """处理文档"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        for processor in self.processors:
            if processor.can_process(file_path):
                try:
                    return processor.extract_content(file_path)
                except Exception as e:
                    print(f"处理器 {processor.__class__.__name__} 处理失败: {e}")
                    continue
        
        raise ValueError(f"不支持的文件类型: {file_path}")
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        formats = []
        for processor in self.processors:
            if isinstance(processor, PDFProcessor):
                formats.append("pdf")
            elif isinstance(processor, HTMLProcessor):
                formats.extend(["html", "htm"])
            elif isinstance(processor, TextProcessor):
                formats.extend(["txt", "md"])
        
        return formats


# 全局文档处理器实例
document_processor = DocumentProcessor()