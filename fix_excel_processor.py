#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Excel处理器修复脚本 - 用于修复excel_processor.py中的语法错误
此脚本将创建一个新的excel_processor_fixed.py文件
"""

import os
import re

def fix_excel_processor():
    """修复excel_processor.py中的语法错误"""
    
    # 读取原始文件
    input_path = "server/utils/excel_processor.py"
    output_path = "server/utils/excel_processor_fixed.py"
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False
    
    # 修复缩进问题
    lines = content.split('\n')
    fixed_lines = []
    indentation_level = 0
    in_class = False
    in_function = False
    in_try_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 空行保持不变
        if not stripped:
            fixed_lines.append(line)
            continue
        
        # 处理缩进
        if stripped.startswith("class "):
            in_class = True
            indentation_level = 0
            fixed_lines.append(line)
        elif stripped.startswith("def "):
            in_function = True
            indentation_level = 1 if in_class else 0
            fixed_lines.append(" " * 4 * indentation_level + stripped)
        elif stripped.startswith("if ") and ":" in stripped:
            indentation_level += 1
            fixed_lines.append(" " * 4 * (indentation_level - 1) + stripped)
        elif stripped.startswith("else:") or stripped.startswith("elif "):
            fixed_lines.append(" " * 4 * (indentation_level - 1) + stripped)
        elif stripped.startswith("try:"):
            in_try_block = True
            indentation_level += 1
            fixed_lines.append(" " * 4 * (indentation_level - 1) + stripped)
        elif stripped.startswith("except ") or stripped.startswith("except:") or stripped.startswith("finally:"):
            in_try_block = False
            fixed_lines.append(" " * 4 * (indentation_level - 1) + stripped)
        elif stripped.startswith("for ") or stripped.startswith("while "):
            indentation_level += 1
            fixed_lines.append(" " * 4 * (indentation_level - 1) + stripped)
        elif stripped.startswith("return ") or stripped == "return":
            fixed_lines.append(" " * 4 * indentation_level + stripped)
        else:
            # 一般的代码行
            fixed_lines.append(" " * 4 * indentation_level + stripped)
    
    # 修复try-except结构
    content = "\n".join(fixed_lines)
    content = re.sub(r'try:(.*?)(?=except|finally|$)', 
                    lambda m: f'try:{m.group(1)}\n    except Exception as e:\n        print(f"Error: {{str(e)}}")', 
                    content, flags=re.DOTALL)
    
    # 修复非循环中的break和continue
    content = re.sub(r'([^循环中的])break', r'\1pass # 原来是break', content)
    content = re.sub(r'([^循环中的])continue', r'\1pass # 原来是continue', content)
    
    # 写入修复后的文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"成功修复文件，保存至: {output_path}")
        return True
    except Exception as e:
        print(f"写入文件失败: {e}")
        return False

def main():
    """主函数"""
    print("开始修复excel_processor.py文件...")
    if fix_excel_processor():
        print("""
修复完成！请执行以下步骤：
1. 检查新生成的excel_processor_fixed.py文件
2. 确认修复无误后，可以替换原文件：
   cp server/utils/excel_processor_fixed.py server/utils/excel_processor.py
3. 重启服务器以应用更改
        """)
    else:
        print("修复失败，请手动修复文件")

if __name__ == "__main__":
    main()