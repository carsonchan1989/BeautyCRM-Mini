import re

def extract_sections():
    with open('database_records.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取C001客户的沟通记录和服务记录
    customer = 'C001'
    
    # 找到C001客户部分
    customer_section_match = re.search(rf'## 客户:.*?\({customer}\).*?(?=## 客户:|$)', content, re.DOTALL)
    if not customer_section_match:
        print(f"未找到客户 {customer} 的部分")
        return
    
    customer_section = customer_section_match.group(0)
    
    # 从客户部分提取沟通记录
    comm_section_match = re.search(r'### 沟通记录.*?(?=###|$)', customer_section, re.DOTALL)
    if comm_section_match:
        print(f"===== 客户 {customer} 的沟通记录 =====")
        print(comm_section_match.group(0))
    else:
        print(f"未找到客户 {customer} 的沟通记录")
    
    # 从客户部分提取服务记录
    service_section_match = re.search(r'### 服务记录.*?(?=###|$)', customer_section, re.DOTALL)
    if service_section_match:
        print(f"\n===== 客户 {customer} 的服务记录 =====")
        print(service_section_match.group(0))
    else:
        print(f"未找到客户 {customer} 的服务记录")

if __name__ == "__main__":
    extract_sections()