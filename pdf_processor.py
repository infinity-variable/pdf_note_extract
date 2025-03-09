import fitz
import os

from typing import List, Dict, Tuple
from datetime import datetime

class PDFProcessor:
    def __init__(self):
        # 版本兼容处理（优化后）
        try:
            # 统一使用新版本属性访问方式
            self.highlight_type = fitz.Annot.Type.HIGHLIGHT
            self.underline_type = fitz.Annot.Type.UNDERLINE
            self.text_type = fitz.Annot.Type.TEXT
            print(f'使用新版本注释常量：高亮[{self.highlight_type}] 下划线[{self.underline_type}] 文本注释[{self.text_type}]')
            # 完整的注释类型映射表
            self.annot_type_names = {
                0: '文本',
                1: '链接',
                2: '自由文本',
                3: '线条',
                4: '方框',
                5: '标记',
                6: '图章',
                7: '涂鸦',
                8: '高亮',
                9: '下划线',
                10: '删除线',
                11: '表格',
                12: '部件',
                13: '签名',
                14: '多边形',
                15: '折线',
                16: '3D对象',
                17: '文件附件'
            }
            self.highlight_flags = (self.highlight_type, self.underline_type)
            self.freetext_type = self.text_type  # 自由文本单独处理
        except AttributeError:
            # 旧版本回退方案
            self.highlight_type = 8
            self.underline_type = 9
            self.text_type = 2  # 自由文本注释类型
            self.freetext_type = self.text_type  # 添加旧版本属性定义
            print(f'使用旧版本注释常量：高亮[{self.highlight_type}] 下划线[{self.underline_type}] 文本注释[{self.text_type}]')
            # 完整的注释类型映射表
            self.annot_type_names = {
                0: '文本',
                1: '链接',
                2: '自由文本',
                3: '线条',
                4: '方框',
                5: '标记',
                6: '图章',
                7: '涂鸦',
                8: '高亮',
                9: '下划线',
                10: '删除线',
                11: '表格',
                12: '部件',
                13: '签名',
                14: '多边形',
                15: '折线',
                16: '3D对象',
                17: '文件附件'
            }
        
        self.highlight_flags = (self.highlight_type, self.underline_type)
        self.freetext_type = self.text_type  # 统一属性初始化
        # 新版本已通过try块初始化 此处确保旧版本属性一致

        print(f'PyMuPDF版本: {fitz.__version__}')
        


    def extract_annotations(self, file_path: str) -> tuple[dict[int, list[tuple[str, str, str]]], dict[str, int]]:
        """
        提取PDF文件中的高亮和下划线注释
        :param file_path: PDF文件路径
        :return: 字典{页码: [(y坐标, 注释内容)]}
        """
        doc = None
        try:
            doc = fitz.open(file_path)
            if doc.is_encrypted:
                raise ValueError("加密文件无法读取")

            annotations = {}
            # 统一使用字符串键类型
            type_counts = {'highlight':0, 'underline':0, 'text':0}
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_annots = []
                
                # 更新坐标提取逻辑
                for annot in page.annots():
                    # 获取完整的注释类型信息
                    annot_code = int(annot.type[0])  # 显式转换为整数类型
                    annot_name = self.annot_type_names.get(annot_code, f'未知类型({annot_code})')
                    
                    # 只处理可提取文本的注释类型
                    # 合并统计逻辑到单个位置
                    # 修正类型判断逻辑
                    if annot_code == self.highlight_type:
                        type_key = 'highlight'
                    elif annot_code == self.underline_type:
                        type_key = 'underline'
                    elif annot_code == self.freetext_type:
                        type_key = 'text'
                    else:
                        continue  # 跳过不需要统计的类型
                    
                    if annot_code in self.highlight_flags or annot_code == self.freetext_type:
                        rect = annot.rect
                        content = self._get_annotation_text(page, annot, annot_code)
                        if content:
                            pdf_time = self._parse_pdf_datetime(annot.info.get('creationDate', ''))
                            timestamp = pdf_time if pdf_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            page_annots.append((rect.y0, rect.x0, rect.x1, timestamp, content, annot_name))
                    
                    # 统一在此处进行类型统计
                    if type_key in ['highlight', 'underline', 'text']:
                        type_counts[type_key] = type_counts.get(type_key, 0) + 1
                
                if page_annots:
                    # 按y坐标排序并去重
                    sorted_annots = sorted(
                        list({(y, x0, x1, t, c, a) for y, x0, x1, t, c, a in page_annots}),
                        key=lambda x: (x[0], x[1])
                    )
                    annotations[page_num + 1] = [(
                        c[3].strftime('%Y-%m-%d %H:%M:%S') if isinstance(c[3], datetime) else c[3],
                        c[4],
                        c[5]
                    ) for c in sorted_annots]
            
            return annotations, type_counts

        except fitz.FileDataError:
            raise RuntimeError("文件损坏或格式不支持")
        finally:
            if doc is not None:
                doc.close()

    def _parse_pdf_datetime(self, pdf_date: str) -> datetime:
        """
        解析PDF格式的日期字符串（符合PDF 1.3规范）
        格式示例：D:20240101000000+08'00'
        """
        if not pdf_date.startswith('D:'):
            return datetime.now()

        try:
            # 提取基础时间部分（移除D:前缀和时区部分）
            base_str = pdf_date[2:].split('+')[0].split('-')[0]
            fmt = '%Y%m%d%H%M%S'
            
            # 补齐可能缺少的时间部分
            padded = base_str.ljust(14, '0')
            return datetime.strptime(padded[:14], fmt)
        except (ValueError, IndexError) as e:
            print(f"日期解析失败[{pdf_date}]: {str(e)}")
            return datetime.now()

    def _get_annotation_text(self, page, annot, annot_type) -> str:
        try:
            if annot_type == self.freetext_type:
                # 直接获取文本注释内容
                return annot.info.get('content', '').replace('\n', ' ').strip()
            else:
                # 原有高亮/下划线的文本提取方式
                return page.get_text("text", clip=annot.rect).replace('\n', ' ').strip()
        except Exception as e:
            print(f"提取注释失败: {str(e)}")
            return ""


def create_markdown(output_dir: str, data: Dict[str, Tuple[Dict[int, List[Tuple[str, str, str]]], Dict[str, int]]]):
    """生成Markdown文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    for file_path, (annotations, counts) in data.items():
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        total_highlights = counts['highlight']
        total_underlines = counts['underline']
        total_notes = counts['text']
        output_path = os.path.join(output_dir, f"《{base_name}》.md")
        #output_path = os.path.join(output_dir, f"{base_name}_摘要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f'# {base_name} 读书笔记\n')
            # 生成全类型统计
            type_stats = ' | '.join([f'{k}{v}条' for k,v in counts.items() if v > 0])
            f.write(f'## 注释类型统计\n{type_stats}\n\n')
            f.write(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write(f'tag：[[书籍]]\n\n')            
            f.write(f"原始文件：{os.path.basename(file_path)}\n\n")
            for page, contents in annotations.items():
                f.write(f"## 第{page}页\n")
                for time, content, annot_type in contents:
                    if content.strip():
                        f.write(f'- [{time}] [{annot_type}] {content}\n')
                f.write('\n')