def scan_markdown_file():
    with open('database_records.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 打印文件大小和部分内容
    print(f"文件大小: {len(content)} 字节")
    print("\n文件前500个字符:")
    print(content[:500])
    
    # 查找关键词
    keywords = ["沟通", "communication", "交流", "联系", "电话", "短信", "微信"]
    for keyword in keywords:
        count = content.count(keyword)
        if count > 0:
            print(f"\n关键词 '{keyword}' 出现了 {count} 次")
            # 显示上下文
            start = content.find(keyword)
            if start >= 0:
                context_start = max(0, start - 50)
                context_end = min(len(content), start + 50)
                print(f"上下文: ...{content[context_start:context_end]}...")

if __name__ == "__main__":
    scan_markdown_file()