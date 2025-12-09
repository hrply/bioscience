"""
PDF处理工具 - 解析和提取PDF内容
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

try:
    import PyPDF2
    import pdfplumber
    PYPDF2_AVAILABLE = True
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFProcessor:
    """PDF处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 检查可用的PDF库
        self.available_libraries = []
        if PYMUPDF_AVAILABLE:
            self.available_libraries.append("pymupdf")
        if PDFPLUMBER_AVAILABLE:
            self.available_libraries.append("pdfplumber")
        if PYPDF2_AVAILABLE:
            self.available_libraries.append("pypdf2")
        
        if not self.available_libraries:
            self.logger.warning("No PDF processing libraries available")
    
    def is_available(self) -> bool:
        """检查PDF处理功能是否可用"""
        return len(self.available_libraries) > 0
    
    def extract_text(self, pdf_path: str, library: str = None) -> str:
        """
        从PDF提取文本
        优先使用PyMuPDF，其次pdfplumber，最后PyPDF2
        """
        if not self.is_available():
            raise RuntimeError("No PDF processing libraries available")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # 选择使用的库
        if library is None:
            library = self.available_libraries[0]  # 使用第一个可用的库
        
        try:
            if library == "pymupdf" and PYMUPDF_AVAILABLE:
                return self._extract_with_pymupdf(pdf_path)
            elif library == "pdfplumber" and PDFPLUMBER_AVAILABLE:
                return self._extract_with_pdfplumber(pdf_path)
            elif library == "pypdf2" and PYPDF2_AVAILABLE:
                return self._extract_with_pypdf2(pdf_path)
            else:
                raise ValueError(f"Library {library} not available")
        
        except Exception as e:
            self.logger.error(f"Error extracting text with {library}: {e}")
            # 尝试使用其他库
            for alt_library in self.available_libraries:
                if alt_library != library:
                    try:
                        self.logger.info(f"Trying alternative library: {alt_library}")
                        return self.extract_text(pdf_path, alt_library)
                    except Exception as alt_e:
                        self.logger.error(f"Alternative library {alt_library} also failed: {alt_e}")
            
            raise RuntimeError(f"All PDF libraries failed to extract text from {pdf_path}")
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> str:
        """使用PyMuPDF提取文本"""
        text = ""
        
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
        
        return text
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """使用pdfplumber提取文本"""
        text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        return text
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """使用PyPDF2提取文本"""
        text = ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        return text
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """提取PDF元数据"""
        if not self.is_available():
            raise RuntimeError("No PDF processing libraries available")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        metadata = {}
        
        try:
            # 使用PyMuPDF提取元数据（最全面）
            if PYMUPDF_AVAILABLE:
                with fitz.open(pdf_path) as doc:
                    metadata.update(doc.metadata)
                    metadata["page_count"] = len(doc)
                    
                    # 添加文件信息
                    file_stat = pdf_path.stat()
                    metadata["file_size"] = file_stat.st_size
                    metadata["created_time"] = file_stat.st_ctime
                    metadata["modified_time"] = file_stat.st_mtime
            
            return metadata
        
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def extract_pages(self, pdf_path: str, start_page: int = 0, end_page: int = None) -> List[str]:
        """提取指定页面范围的文本"""
        if not self.is_available():
            raise RuntimeError("No PDF processing libraries available")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pages = []
        
        try:
            if PYMUPDF_AVAILABLE:
                with fitz.open(pdf_path) as doc:
                    if end_page is None:
                        end_page = len(doc)
                    
                    for page_num in range(start_page, min(end_page, len(doc))):
                        page = doc.load_page(page_num)
                        pages.append(page.get_text())
            
            return pages
        
        except Exception as e:
            self.logger.error(f"Error extracting pages: {e}")
            raise
    
    def extract_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """提取PDF中的表格"""
        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError("pdfplumber library required for table extraction")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
            
            return tables
        
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            return []
    
    def extract_images(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """提取PDF中的图片"""
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF library required for image extraction")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        image_paths = []
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    image_list = page.get_images(full=True)
                    
                    for img_index, img in enumerate(image_list):
                        # 获取图片数据
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # 确保是RGB或灰度图
                            if output_dir:
                                img_path = output_dir / f"page_{page_num+1}_img_{img_index+1}.png"
                                pix.save(str(img_path))
                                image_paths.append(str(img_path))
                            else:
                                # 如果没有指定输出目录，返回base64编码的图片
                                import base64
                                import io
                                
                                img_data = io.BytesIO()
                                pix.save(img_data, "png")
                                img_base64 = base64.b64encode(img_data.getvalue()).decode()
                                image_paths.append(f"data:image/png;base64,{img_base64}")
                        
                        pix = None  # 释放内存
        
            return image_paths
        
        except Exception as e:
            self.logger.error(f"Error extracting images: {e}")
            return []
    
    def search_text(self, pdf_path: str, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """在PDF中搜索文本"""
        if not self.is_available():
            raise RuntimeError("No PDF processing libraries available")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        matches = []
        
        try:
            if PYMUPDF_AVAILABLE:
                with fitz.open(pdf_path) as doc:
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        text = page.get_text()
                        
                        # 搜索文本
                        if not case_sensitive:
                            search_text = text.lower()
                            search_query = query.lower()
                        else:
                            search_text = text
                            search_query = query
                        
                        start = 0
                        while True:
                            pos = search_text.find(search_query, start)
                            if pos == -1:
                                break
                            
                            matches.append({
                                "page": page_num + 1,
                                "position": pos,
                                "context": self._get_context(text, pos, len(query)),
                                "match": query
                            })
                            
                            start = pos + 1
            
            return matches
        
        except Exception as e:
            self.logger.error(f"Error searching text: {e}")
            return []
    
    def _get_context(self, text: str, position: int, length: int, context_size: int = 50) -> str:
        """获取匹配文本的上下文"""
        start = max(0, position - context_size)
        end = min(len(text), position + length + context_size)
        
        context = text[start:end]
        
        # 添加省略号
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context
    
    def get_page_count(self, pdf_path: str) -> int:
        """获取PDF页数"""
        if not self.is_available():
            raise RuntimeError("No PDF processing libraries available")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            if PYMUPDF_AVAILABLE:
                with fitz.open(pdf_path) as doc:
                    return len(doc)
            elif PYPDF2_AVAILABLE:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return len(pdf_reader.pages)
        
        except Exception as e:
            self.logger.error(f"Error getting page count: {e}")
            return 0
    
    def is_valid_pdf(self, pdf_path: str) -> bool:
        """检查PDF文件是否有效"""
        if not self.is_available():
            return False
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return False
        
        try:
            if PYMUPDF_AVAILABLE:
                with fitz.open(pdf_path) as doc:
                    # 尝试访问第一页
                    if len(doc) > 0:
                        doc.load_page(0)
                    return True
            elif PYPDF2_AVAILABLE:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    # 尝试访问第一页
                    if len(pdf_reader.pages) > 0:
                        pdf_reader.pages[0]
                    return True
        
        except Exception as e:
            self.logger.error(f"PDF validation error: {e}")
            return False
        
        return False
    
    def extract_structured_content(self, pdf_path: str) -> Dict[str, Any]:
        """提取结构化内容（标题、段落、表格等）"""
        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError("pdfplumber library required for structured content extraction")
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        structured_content = {
            "titles": [],
            "paragraphs": [],
            "tables": [],
            "metadata": {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 提取文本
                    text = page.extract_text() or ""
                    
                    # 提取标题（简单的启发式方法）
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) < 100:  # 标题通常较短
                            # 检查是否可能是标题（全部大写、首字母大写等）
                            if (line.isupper() or 
                                (line[0].isupper() and not line.endswith('.')) or
                                re.match(r'^[A-Z\d\s\-:]+$', line)):
                                
                                structured_content["titles"].append({
                                    "page": page_num + 1,
                                    "text": line,
                                    "level": self._estimate_title_level(line)
                                })
                            elif len(line) > 20:  # 可能是段落
                                structured_content["paragraphs"].append({
                                    "page": page_num + 1,
                                    "text": line
                                })
                    
                    # 提取表格
                    tables = page.extract_tables()
                    for table in tables:
                        structured_content["tables"].append({
                            "page": page_num + 1,
                            "data": table
                        })
            
            # 提取元数据
            structured_content["metadata"] = self.extract_metadata(pdf_path)
            
            return structured_content
        
        except Exception as e:
            self.logger.error(f"Error extracting structured content: {e}")
            return structured_content
    
    def _estimate_title_level(self, title: str) -> int:
        """估算标题级别"""
        # 简单的启发式方法
        if len(title) < 30 and title.isupper():
            return 1  # 一级标题
        elif len(title) < 50:
            return 2  # 二级标题
        else:
            return 3  # 三级标题


# 全局PDF处理器实例
_global_pdf_processor = None


def get_pdf_processor() -> PDFProcessor:
    """获取全局PDF处理器实例"""
    global _global_pdf_processor
    if _global_pdf_processor is None:
        _global_pdf_processor = PDFProcessor()
    return _global_pdf_processor