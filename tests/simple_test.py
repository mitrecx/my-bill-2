#!/usr/bin/env python3

# 测试AI响应解析逻辑
content = """账单ID: 14797
分类ID: 11"""

print("原始AI响应:")
print(repr(content))

# 解析逻辑
category_id = None
lines = content.split('\n')

for line in lines:
    line = line.strip()
    print(f"处理行: {repr(line)}")
    
    if '分类ID:' in line:
        parts = line.split('分类ID:', 1)
        if len(parts) == 2:
            category_id_str = parts[1].strip()
            try:
                category_id = int(category_id_str)
                print(f"提取到分类ID: {category_id}")
                break
            except ValueError:
                continue

if category_id:
    print(f"✅ 成功解析分类ID: {category_id}")
else:
    print("❌ 解析失败")