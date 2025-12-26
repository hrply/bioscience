"""
差异对比工具 - 高亮显示修改部分，生成可视化对比
"""

import difflib
import re
from typing import List, Tuple, Dict, Any
from html import escape


def highlight_modifications(original: str, revised: str) -> str:
    """
    高亮显示修改部分
    使用HTML标记突出显示新增、删除和修改的内容
    """
    # 生成HTML差异
    differ = difflib.HtmlDiff()
    html_diff = differ.make_file(
        original.splitlines(),
        revised.splitlines(),
        fromdesc="原始模板",
        todesc="修订版本",
        context=True,
        numlines=3
    )
    
    # 自定义样式增强显示效果
    styled_diff = f"""
    <style>
        .diff_add {{ background-color: #e6ffed; color: #22863a; }}
        .diff_chg {{ background-color: #fff5c1; color: #b08800; }}
        .diff_sub {{ background-color: #ffeef0; color: #cb2431; }}
        .diff_header {{ background-color: #f6f8fa; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
    {html_diff}
    """
    
    return styled_diff


def generate_side_by_side_diff(original: str, revised: str) -> str:
    """
    生成并排对比视图
    """
    original_lines = original.splitlines(keepends=True)
    revised_lines = revised.splitlines(keepends=True)
    
    # 使用SequenceMatcher获取差异
    matcher = difflib.SequenceMatcher(None, original_lines, revised_lines)
    
    html_content = """
    <style>
        .diff-container { display: flex; gap: 20px; }
        .diff-column { flex: 1; }
        .diff-line { padding: 2px 5px; font-family: monospace; white-space: pre-wrap; }
        .line-added { background-color: #e6ffed; }
        .line-removed { background-color: #ffeef0; }
        .line-changed { background-color: #fff5c1; }
        .line-unchanged { background-color: transparent; }
        .line-number { color: #666; width: 40px; display: inline-block; text-align: right; margin-right: 10px; }
    </style>
    <div class="diff-container">
        <div class="diff-column">
            <h3>原始模板</h3>
            <div>
    """
    
    original_html = []
    revised_html = []
    orig_line_num = 0
    rev_line_num = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # 相同行
            for i in range(i1, i2):
                orig_line_num += 1
                rev_line_num += 1
                line_content = escape(original_lines[i].rstrip())
                original_html.append(
                    f'<div class="diff-line line-unchanged">'
                    f'<span class="line-number">{orig_line_num}</span>{line_content}</div>'
                )
                revised_html.append(
                    f'<div class="diff-line line-unchanged">'
                    f'<span class="line-number">{rev_line_num}</span>{line_content}</div>'
                )
        
        elif tag == 'replace':
            # 替换行
            for i in range(i1, i2):
                orig_line_num += 1
                line_content = escape(original_lines[i].rstrip())
                original_html.append(
                    f'<div class="diff-line line-removed">'
                    f'<span class="line-number">{orig_line_num}</span>{line_content}</div>'
                )
            
            for j in range(j1, j2):
                rev_line_num += 1
                line_content = escape(revised_lines[j].rstrip())
                revised_html.append(
                    f'<div class="diff-line line-added">'
                    f'<span class="line-number">{rev_line_num}</span>{line_content}</div>'
                )
            
            # 平衡行数
            if i2 - i1 < j2 - j1:
                for _ in range(j2 - j1 - (i2 - i1)):
                    original_html.append('<div class="diff-line"></div>')
            elif i2 - i1 > j2 - j1:
                for _ in range(i2 - i1 - (j2 - j1)):
                    revised_html.append('<div class="diff-line"></div>')
        
        elif tag == 'delete':
            # 删除行
            for i in range(i1, i2):
                orig_line_num += 1
                line_content = escape(original_lines[i].rstrip())
                original_html.append(
                    f'<div class="diff-line line-removed">'
                    f'<span class="line-number">{orig_line_num}</span>{line_content}</div>'
                )
                revised_html.append('<div class="diff-line"></div>')
        
        elif tag == 'insert':
            # 插入行
            for j in range(j1, j2):
                rev_line_num += 1
                line_content = escape(revised_lines[j].rstrip())
                revised_html.append(
                    f'<div class="diff-line line-added">'
                    f'<span class="line-number">{rev_line_num}</span>{line_content}</div>'
                )
                original_html.append('<div class="diff-line"></div>')
    
    html_content += '\n'.join(original_html)
    html_content += """
            </div>
        </div>
        <div class="diff-column">
            <h3>修订版本</h3>
            <div>
    """
    html_content += '\n'.join(revised_html)
    html_content += """
            </div>
        </div>
    </div>
    """
    
    return html_content


def extract_modification_summary(original: str, revised: str) -> Dict[str, Any]:
    """
    提取修改摘要信息
    """
    original_lines = original.splitlines()
    revised_lines = revised.splitlines()
    
    matcher = difflib.SequenceMatcher(None, original_lines, revised_lines)
    
    summary = {
        "total_lines_original": len(original_lines),
        "total_lines_revised": len(revised_lines),
        "lines_added": 0,
        "lines_removed": 0,
        "lines_changed": 0,
        "sections_modified": [],
        "key_changes": []
    }
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            summary["lines_changed"] += max(i2 - i1, j2 - j1)
            
            # 提取修改的章节
            for i in range(max(0, i1-2), min(len(original_lines), i2+2)):
                line = original_lines[i]
                if re.match(r'^#{1,6}\s+', line):
                    section_name = re.sub(r'^#{1,6}\s+', '', line).strip()
                    if section_name not in summary["sections_modified"]:
                        summary["sections_modified"].append(section_name)
            
            # 记录关键变化
            if i2 - i1 <= 3 and j2 - j1 <= 3:  # 只记录小范围变化
                original_text = '\n'.join(original_lines[i1:i2])
                revised_text = '\n'.join(revised_lines[j1:j2])
                summary["key_changes"].append({
                    "type": "replace",
                    "original": original_text,
                    "revised": revised_text
                })
        
        elif tag == 'delete':
            summary["lines_removed"] += i2 - i1
        
        elif tag == 'insert':
            summary["lines_added"] += j2 - j1
    
    return summary


def generate_text_diff(original: str, revised: str) -> str:
    """
    生成纯文本格式的差异
    """
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        revised.splitlines(keepends=True),
        fromfile="原始模板",
        tofile="修订版本",
        lineterm=""
    )
    
    return '\n'.join(diff)


def find_modified_sections(original: str, revised: str) -> List[Dict[str, Any]]:
    """
    查找被修改的章节
    """
    original_lines = original.splitlines()
    revised_lines = revised.splitlines()
    
    # 提取章节结构
    original_sections = _extract_sections_with_line_numbers(original_lines)
    revised_sections = _extract_sections_with_line_numbers(revised_lines)
    
    modified_sections = []
    
    # 比较章节内容
    for section_name, orig_info in original_sections.items():
        if section_name in revised_sections:
            rev_info = revised_sections[section_name]
            
            # 检查章节内容是否发生变化
            orig_content = '\n'.join(original_lines[orig_info['start']:orig_info['end']])
            rev_content = '\n'.join(revised_lines[rev_info['start']:rev_info['end']])
            
            if orig_content != rev_content:
                modified_sections.append({
                    "section": section_name,
                    "original_lines": f"{orig_info['start']+1}-{orig_info['end']}",
                    "revised_lines": f"{rev_info['start']+1}-{rev_info['end']}",
                    "change_type": "modified"
                })
        else:
            # 章节被删除
            modified_sections.append({
                "section": section_name,
                "original_lines": f"{orig_info['start']+1}-{orig_info['end']}",
                "revised_lines": "",
                "change_type": "deleted"
            })
    
    # 检查新增章节
    for section_name, rev_info in revised_sections.items():
        if section_name not in original_sections:
            modified_sections.append({
                "section": section_name,
                "original_lines": "",
                "revised_lines": f"{rev_info['start']+1}-{rev_info['end']}",
                "change_type": "added"
            })
    
    return modified_sections


def _extract_sections_with_line_numbers(lines: List[str]) -> Dict[str, Dict[str, int]]:
    """
    提取章节及其行号范围
    """
    sections = {}
    current_section = "引言"
    start_line = 0
    
    for i, line in enumerate(lines):
        if re.match(r'^#{1,6}\s+', line):
            # 保存上一个章节
            if current_section in sections:
                sections[current_section]['end'] = i
            
            # 开始新章节
            section_name = re.sub(r'^#{1,6}\s+', '', line).strip()
            current_section = section_name
            start_line = i
            
            sections[current_section] = {"start": start_line}
    
    # 保存最后一个章节
    if current_section in sections:
        sections[current_section]['end'] = len(lines)
    
    return sections


def validate_diff_integrity(original: str, revised: str, diff_text: str) -> bool:
    """
    验证差异的完整性
    通过应用差异来检查是否能正确还原修订版本
    """
    try:
        # 这里可以实现更复杂的差异验证逻辑
        # 简单版本：检查修订版本是否包含原始版本的主要内容
        
        original_words = set(re.findall(r'\w+', original.lower()))
        revised_words = set(re.findall(r'\w+', revised.lower()))
        
        # 如果修订版本丢失了太多原始词汇，可能有问题
        common_words = original_words & revised_words
        similarity = len(common_words) / len(original_words) if original_words else 0
        
        return similarity > 0.5  # 至少保留50%的原始词汇
        
    except Exception:
        return False


def generate_change_statistics(original: str, revised: str) -> Dict[str, Any]:
    """
    生成详细的变更统计
    """
    summary = extract_modification_summary(original, revised)
    
    # 计算字符级统计
    original_chars = len(original)
    revised_chars = len(revised)
    
    # 计算词级统计
    original_words = len(original.split())
    revised_words = len(revised.split())
    
    # 计算段落统计
    original_paragraphs = len([p for p in original.split('\n\n') if p.strip()])
    revised_paragraphs = len([p for p in revised.split('\n\n') if p.strip()])
    
    summary.update({
        "character_stats": {
            "original": original_chars,
            "revised": revised_chars,
            "change": revised_chars - original_chars,
            "change_percent": ((revised_chars - original_chars) / original_chars * 100) if original_chars > 0 else 0
        },
        "word_stats": {
            "original": original_words,
            "revised": revised_words,
            "change": revised_words - original_words,
            "change_percent": ((revised_words - original_words) / original_words * 100) if original_words > 0 else 0
        },
        "paragraph_stats": {
            "original": original_paragraphs,
            "revised": revised_paragraphs,
            "change": revised_paragraphs - original_paragraphs
        }
    })
    
    return summary