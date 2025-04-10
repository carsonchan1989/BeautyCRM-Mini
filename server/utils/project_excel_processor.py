"""
项目Excel数据处理工具
用于清洗和导入项目Excel数据
"""

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('project_excel_processor')

class ProjectExcelProcessor:
    """项目Excel数据处理器"""
    
    # 定义项目Excel表头映射
    COLUMN_MAPPING = {
        '项目名称': 'name',
        '项目类别': 'category',
        '项目功效': 'effects',
        '原理描述': 'description',
        '疗程价格': 'price',
        '次数': 'sessions',
        '项目时长': 'duration',
        '所需材料': 'materials',
        '注意事项': 'notes'
    }
    
    # 定义必填字段
    REQUIRED_FIELDS = ['项目名称', '项目类别', '疗程价格', '次数']
    
    def __init__(self, file_path: str):
        """
        初始化处理器
        
        Args:
            file_path: Excel文件路径
        """
        self.file_path = file_path
        self.df = None
        self.processed_data = []
        self.errors = []
        
    def load_excel(self) -> bool:
        """
        加载Excel文件
        
        Returns:
            bool: 是否成功加载
        """
        try:
            self.df = pd.read_excel(self.file_path)
            return True
        except Exception as e:
            self.errors.append(f"加载Excel文件失败: {str(e)}")
            logger.error(f"加载Excel文件失败: {str(e)}")
            return False
    
    def validate_headers(self) -> Tuple[bool, List[str]]:
        """
        验证表头是否符合要求
        
        Returns:
            bool: 是否验证通过
            List[str]: 缺失的必填字段列表
        """
        if self.df is None:
            return False, ["文件未加载"]
        
        columns = self.df.columns
        missing_required = [field for field in self.REQUIRED_FIELDS if field not in columns]
        
        if missing_required:
            self.errors.append(f"Excel缺少必填字段: {', '.join(missing_required)}")
            logger.error(f"Excel缺少必填字段: {', '.join(missing_required)}")
            return False, missing_required
        
        return True, []
    
    def clean_data(self) -> List[Dict[str, Any]]:
        """
        清洗Excel数据
        
        Returns:
            List[Dict[str, Any]]: 清洗后的数据列表
        """
        if self.df is None:
            return []
        
        valid, missing_fields = self.validate_headers()
        if not valid:
            return []
        
        cleaned_data = []
        
        # 处理每一行数据
        for idx, row in self.df.iterrows():
            try:
                # 检查必填字段是否有值
                if any(pd.isna(row[field]) for field in self.REQUIRED_FIELDS):
                    self.errors.append(f"第{idx+2}行: 存在必填字段为空")
                    logger.warning(f"第{idx+2}行: 存在必填字段为空")
                    continue
                
                # 创建项目数据字典
                project_data = {}
                
                # 映射字段
                for excel_col, db_col in self.COLUMN_MAPPING.items():
                    if excel_col in self.df.columns:
                        value = row[excel_col]
                        
                        # 处理不同类型的数据
                        if pd.isna(value):
                            project_data[db_col] = None
                        elif db_col == 'price':
                            # 确保价格是浮点数
                            try:
                                project_data[db_col] = float(value)
                            except:
                                project_data[db_col] = 0.0
                                self.errors.append(f"第{idx+2}行: 价格格式错误，已设为0")
                        elif db_col == 'sessions':
                            # 确保次数是整数
                            try:
                                project_data[db_col] = int(value)
                            except:
                                project_data[db_col] = 1
                                self.errors.append(f"第{idx+2}行: 次数格式错误，已设为1")
                        elif db_col == 'duration':
                            # 处理时长字段，提取数字
                            if isinstance(value, str) and '分钟' in value:
                                try:
                                    project_data[db_col] = int(value.replace('分钟', '').strip())
                                except:
                                    project_data[db_col] = 60
                            elif isinstance(value, (int, float)):
                                project_data[db_col] = int(value)
                            else:
                                project_data[db_col] = 60
                        else:
                            # 其他字段保持原样
                            project_data[db_col] = value
                
                # 添加状态字段
                project_data['status'] = 'active'
                
                cleaned_data.append(project_data)
                
            except Exception as e:
                self.errors.append(f"第{idx+2}行: 处理出错 - {str(e)}")
                logger.error(f"第{idx+2}行: 处理出错 - {str(e)}")
        
        self.processed_data = cleaned_data
        return cleaned_data
    
    def get_preview_data(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取预览数据
        
        Args:
            limit: 预览数据条数
            
        Returns:
            Dict[str, Any]: 预览数据和统计信息
        """
        if not self.processed_data:
            self.clean_data()
        
        return {
            'total': len(self.processed_data),
            'preview': self.processed_data[:limit],
            'errors': self.errors,
            'categories': self._get_categories(),
            'price_range': self._get_price_range()
        }
    
    def _get_categories(self) -> List[str]:
        """获取所有项目类别"""
        categories = set()
        for item in self.processed_data:
            if item.get('category'):
                categories.add(item['category'])
        return sorted(list(categories))
    
    def _get_price_range(self) -> Dict[str, float]:
        """获取价格范围"""
        if not self.processed_data:
            return {'min': 0, 'max': 0, 'avg': 0}
        
        prices = [item['price'] for item in self.processed_data if item.get('price') is not None]
        if not prices:
            return {'min': 0, 'max': 0, 'avg': 0}
        
        return {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / len(prices)
        }
        
    def get_all_data(self) -> List[Dict[str, Any]]:
        """
        获取所有清洗后的数据
        
        Returns:
            List[Dict[str, Any]]: 清洗后的数据列表
        """
        if not self.processed_data:
            self.clean_data()
        
        return self.processed_data
    
    def get_errors(self) -> List[str]:
        """
        获取处理过程中的错误信息
        
        Returns:
            List[str]: 错误信息列表
        """
        return self.errors 