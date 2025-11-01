"""
数据处理服务
"""
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from sklearn.model_selection import train_test_split
import re


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.json', '.txt']
    
    def process_uploaded_data(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        处理上传的数据文件
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 (csv, xlsx, zip)
        
        Returns:
            处理结果字典
        """
        if file_type == 'zip':
            return self._process_zip_file(file_path)
        elif file_type in ['csv', 'xlsx']:
            return self._process_spreadsheet(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    def _process_zip_file(self, zip_path: str) -> Dict[str, Any]:
        """处理 ZIP 文件"""
        import zipfile
        
        extract_dir = os.path.splitext(zip_path)[0] + "_extracted"
        os.makedirs(extract_dir, exist_ok=True)
        
        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 查找文件
        csv_files = []
        assignment_files = []
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.csv'):
                    csv_files.append(file_path)
                elif file.endswith(('.txt', '.md', '.pdf', '.docx')):
                    assignment_files.append(file_path)
        
        if not csv_files:
            raise ValueError("未找到 CSV 评分文件")
        
        # 处理评分数据
        scoring_data = self._process_scoring_csv(csv_files[0])
        
        # 处理作业文件
        assignment_data = self._process_assignment_files(assignment_files)
        
        # 合并数据
        processed_data = self._merge_assignments_and_scores(
            assignment_data, scoring_data
        )
        
        return {
            "type": "zip",
            "csv_files_count": len(csv_files),
            "assignment_files_count": len(assignment_files),
            "total_records": len(processed_data),
            "processed_data": processed_data,
            "data_path": self._save_processed_data(processed_data, extract_dir)
        }
    
    def _process_spreadsheet(self, file_path: str) -> Dict[str, Any]:
        """处理电子表格文件"""
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # 基本数据清理
        df = df.dropna(subset=['student_id', 'assignment', 'score'] if 
                      all(col in df.columns for col in ['student_id', 'assignment', 'score'])
                      else [])
        
        # 转换为训练数据格式
        processed_data = self._convert_to_training_format(df)
        
        return {
            "type": "spreadsheet",
            "total_records": len(processed_data),
            "processed_data": processed_data,
            "data_path": self._save_processed_data(
                processed_data, 
                os.path.dirname(file_path)
            )
        }
    
    def _process_scoring_csv(self, csv_path: str) -> pd.DataFrame:
        """处理评分 CSV 文件"""
        df = pd.read_csv(csv_path)
        
        # 标准化列名
        column_mapping = {
            'student_id': ['student_id', 'Student ID', 'StudentID', 'ID'],
            'assignment': ['assignment', 'Assignment', 'task', 'Task'],
            'score': ['score', 'Score', 'grade', 'Grade', 'mark', 'Mark']
        }
        
        for standard_col, possible_cols in column_mapping.items():
            for col in df.columns:
                if col in possible_cols:
                    df = df.rename(columns={col: standard_col})
                    break
        
        # 验证必要列
        required_cols = ['student_id', 'assignment', 'score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"CSV 文件缺少必要列: {missing_cols}")
        
        # 数据清理
        df = df.dropna(subset=required_cols)
        df['score'] = pd.to_numeric(df['score'], errors='coerce')
        df = df.dropna(subset=['score'])
        
        return df
    
    def _process_assignment_files(self, file_paths: List[str]) -> Dict[str, str]:
        """处理作业文件"""
        assignments = {}
        
        for file_path in file_paths:
            try:
                # 从文件名提取学生ID和作业信息
                filename = os.path.basename(file_path)
                student_id, assignment_name = self._extract_info_from_filename(filename)
                
                # 读取文件内容
                content = self._read_file_content(file_path)
                
                if student_id and content:
                    key = f"{student_id}_{assignment_name}"
                    assignments[key] = {
                        "student_id": student_id,
                        "assignment": assignment_name,
                        "content": content,
                        "file_path": file_path
                    }
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
                continue
        
        return assignments
    
    def _extract_info_from_filename(self, filename: str) -> Tuple[str, str]:
        """从文件名提取学生ID和作业信息"""
        # 常见的文件名模式
        patterns = [
            r'(\d+)_(.+)\.', # 学号_作业名.扩展名
            r'(.+)_(\d+)\.', # 作业名_学号.扩展名
            r'(\d+)-(.+)\.', # 学号-作业名.扩展名
            r'(.+)-(\d+)\.', # 作业名-学号.扩展名
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                part1, part2 = match.groups()
                # 判断哪个是学号（通常是数字）
                if part1.isdigit():
                    return part1, part2
                elif part2.isdigit():
                    return part2, part1
        
        # 如果无法匹配，返回文件名作为作业名，空字符串作为学生ID
        assignment_name = os.path.splitext(filename)[0]
        return "", assignment_name
    
    def _read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            if file_path.endswith('.txt') or file_path.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.endswith('.pdf'):
                # 需要安装 PyPDF2 或 pdfplumber
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                        return text
                except ImportError:
                    return "[PDF文件需要安装 pdfplumber 库来解析]"
            elif file_path.endswith('.docx'):
                # 需要安装 python-docx
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return "\n".join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    return "[DOCX文件需要安装 python-docx 库来解析]"
            else:
                return ""
        except Exception as e:
            return f"[读取文件出错: {e}]"
    
    def _merge_assignments_and_scores(self, assignments: Dict, scores_df: pd.DataFrame) -> List[Dict]:
        """合并作业内容和评分数据"""
        merged_data = []
        
        for _, row in scores_df.iterrows():
            student_id = str(row['student_id'])
            assignment = str(row['assignment'])
            score = float(row['score'])
            
            # 查找对应的作业内容
            content = ""
            for key, assignment_data in assignments.items():
                if (assignment_data['student_id'] == student_id or 
                    assignment in assignment_data['assignment'] or
                    assignment_data['assignment'] in assignment):
                    content = assignment_data['content']
                    break
            
            merged_data.append({
                "student_id": student_id,
                "assignment": assignment,
                "content": content,
                "score": score,
                "label": self._score_to_label(score)
            })
        
        return merged_data
    
    def _convert_to_training_format(self, df: pd.DataFrame) -> List[Dict]:
        """转换为训练数据格式"""
        training_data = []
        
        for _, row in df.iterrows():
            # 基本信息
            data_point = {
                "student_id": str(row.get('student_id', '')),
                "assignment": str(row.get('assignment', '')),
                "score": float(row.get('score', 0)),
                "content": str(row.get('content', '')),
                "label": self._score_to_label(float(row.get('score', 0)))
            }
            
            # 添加其他可用列
            for col in df.columns:
                if col not in ['student_id', 'assignment', 'score', 'content']:
                    data_point[col] = str(row[col])
            
            training_data.append(data_point)
        
        return training_data
    
    def _score_to_label(self, score: float) -> str:
        """将分数转换为标签"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "pass"
        else:
            return "fail"
    
    def _save_processed_data(self, data: List[Dict], output_dir: str) -> str:
        """保存处理后的数据"""
        output_file = os.path.join(output_dir, "processed_data.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def create_training_dataset(self, data: List[Dict], test_size: float = 0.2, val_size: float = 0.1) -> Dict[str, Any]:
        """创建训练数据集"""
        if not data:
            raise ValueError("数据为空")
        
        # 准备特征和标签
        texts = []
        labels = []
        
        for item in data:
            # 构建输入文本
            input_text = self._format_input_text(item)
            texts.append(input_text)
            labels.append(item['label'])
        
        # 分割数据集
        X_temp, X_test, y_temp, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        if val_size > 0:
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=val_size/(1-test_size), random_state=42, stratify=y_temp
            )
        else:
            X_train, X_val, y_train, y_val = X_temp, [], y_temp, []
        
        return {
            "train": {"texts": X_train, "labels": y_train},
            "validation": {"texts": X_val, "labels": y_val},
            "test": {"texts": X_test, "labels": y_test},
            "label_mapping": self._create_label_mapping(labels),
            "statistics": self._calculate_dataset_statistics(texts, labels)
        }
    
    def _format_input_text(self, item: Dict) -> str:
        """格式化输入文本"""
        components = []
        
        if item.get('assignment'):
            components.append(f"作业: {item['assignment']}")
        
        if item.get('content'):
            components.append(f"内容: {item['content']}")
        
        return "\n".join(components)
    
    def _create_label_mapping(self, labels: List[str]) -> Dict[str, int]:
        """创建标签映射"""
        unique_labels = sorted(list(set(labels)))
        return {label: idx for idx, label in enumerate(unique_labels)}
    
    def _calculate_dataset_statistics(self, texts: List[str], labels: List[str]) -> Dict[str, Any]:
        """计算数据集统计信息"""
        text_lengths = [len(text) for text in texts]
        
        return {
            "total_samples": len(texts),
            "unique_labels": len(set(labels)),
            "label_distribution": {label: labels.count(label) for label in set(labels)},
            "text_length_stats": {
                "mean": np.mean(text_lengths),
                "median": np.median(text_lengths),
                "min": np.min(text_lengths),
                "max": np.max(text_lengths),
                "std": np.std(text_lengths)
            }
        }
