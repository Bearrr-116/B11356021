import os

def reformat_law(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找標題行
    lines = content.split('\n')
    title = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line
            body_start = i + 1
            break
    
    # 把剩餘內容按空行切割成條文
    body = '\n'.join(lines[body_start:])
    articles = [a.strip() for a in body.split('\n\n') if a.strip()]
    
    result = [title, ""]
    for i, article in enumerate(articles, 1):
        # 跳過已有 ## 標題的行
        if article.startswith('##'):
            result.append(article)
        else:
            result.append(f"## 第 {i} 條\n{article}")
    
    new_content = '\n\n'.join(result)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"完成：{filepath}（共 {len(articles)} 條）")

if __name__ == "__main__":
    laws = [
        "docs/民法.md",
        "docs/消費者保護法.md",
        "docs/勞動基準法.md",
        "docs/刑法.md",
        "docs/民事訴訟法.md",
    ]
    
    for law in laws:
        if os.path.exists(law):
            reformat_law(law)
        else:
            print(f"找不到：{law}")