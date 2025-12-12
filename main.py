import os
import smtplib
import ads
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta

# ================= 配置区域 =================

# 1. 核心关键词 (AI 技术)
keywords_tech = [
    '"Deep learning"', 
    '"Neural network"', 
    '"Machine learning"', 
    '"Artificial intelligence"', 
    '"CNN"', 
    '"Object detection"'
]

# 2. 场景关键词 (行星/落石)
keywords_scene = [
    '"Moon"', 
    '"Lunar"', 
    '"Planetary"', 
    '"Rockfall"', 
    '"Boulder"', 
    '"Crater"', 
    '"Mars"'
]

# 3. 指定期刊的 Bibstem (ADS 标准缩写)
# Icarus, JGR-Planets, P&SS, EPSL, GRL, ISPRS, TGRS
target_journals = [
    "Icarus", 
    "JGRE",   # JGR Planets
    "P&SS",   # Planetary and Space Science
    "EPSL",   # Earth and Planetary Science Letters
    "GeoRL",  # Geophysical Research Letters
    "IsPRS",  # ISPRS Journal of Photogrammetry and Remote Sensing (注: ADS缩写有时变动，IsPRS较常用)
    "ITGRS"   # IEEE Transactions on Geoscience and Remote Sensing
]

# ===========================================

def get_date_range(days=7):
    """获取过去N天的日期范围，格式 YYYY-MM-DD"""
    today = date.today()
    start_date = today - timedelta(days=days)
    # ADS 格式: [YYYY-MM-DD TO YYYY-MM-DD]
    return f"[{start_date} TO {today}]"

def build_query():
    """构建符合 NASA ADS 语法的复杂查询语句"""
    tech_str = " OR ".join(keywords_tech)
    scene_str = " OR ".join(keywords_scene)
    journal_str = " OR ".join([f'bibstem:"{j}"' for j in target_journals])
    
    # 逻辑: (技术) AND (场景) AND (期刊) AND (日期范围)
    # 注意：title, abstract, keyword 统称为 content 或者分别指定。这里用全字段搜索更保险。
    q = f'({tech_str}) AND ({scene_str}) AND ({journal_str})'
    return q

def send_email(papers):
    if not papers:
        print("No papers found this week.")
        return

    sender = os.environ["SENDER_EMAIL"]
    password = os.environ["SENDER_PASSWORD"]
    receiver = os.environ["RECEIVER_EMAIL"]

    # 构建邮件 HTML 内容
    html_content = "<h2>🚀 本周 AI + 行星科学新论文推送</h2><hr>"
    for p in papers:
        # 获取作者（前3位）
        authors = p.author[:3]
        if len(p.author) > 3:
            authors.append("et al.")
        author_str = ", ".join(authors) if authors else "Unknown Author"
        
        # 获取链接 (优先用 arxiv 或 publisher)
        link = f"https://ui.adsabs.harvard.edu/abs/{p.bibcode}"
        
        html_content += f"""
        <div style="margin-bottom: 20px;">
            <h3 style="color: #2c3e50;"><a href="{link}">{p.title[0]}</a></h3>
            <p><strong>Published in:</strong> {p.pub} ({p.year})</p>
            <p><strong>Authors:</strong> {author_str}</p>
            <p style="color: #666; font-size: 0.9em;">{p.abstract[:500]}...</p>
            <a href="{link}" style="color: #3498db;">阅读原文</a>
        </div>
        <hr>
        """

    msg = MIMEMultipart()
    msg['Subject'] = f'Paper Bot: 发现了 {len(papers)} 篇新论文 ({date.today()})'
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # 使用 Gmail SMTP (端口 465 SSL)
        # 如果使用其他邮箱(QQ/163)，请改为对应 smtp 服务器地址和端口
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    # 配置 ADS Token
    ads.config.token = os.environ["ADS_TOKEN"]
    
    query_str = build_query()
    date_range = get_date_range(7) # 搜索过去7天
    
    print(f"Querying ADS: {query_str} \nDate: {date_range}")
    
    try:
        # 执行搜索
        # fq 参数用于过滤日期
        papers = list(ads.SearchQuery(
            q=query_str, 
            fq=f'pubdate:{date_range}',
            sort="date desc",
            rows=20, # 限制每次最多推20篇，防止邮箱爆炸
            fl=['title', 'author', 'abstract', 'pub', 'year', 'bibcode'] # 只获取这些字段
        ))
        
        print(f"Found {len(papers)} papers.")
        if len(papers) > 0:
            send_email(papers)
            
    except ads.exceptions.APIResponseError as e:
        print(f"ADS API Error: {e}")

if __name__ == "__main__":
    main()
