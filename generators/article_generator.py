import json, os
import anthropic
from datetime import datetime
from pathlib import Path

ARTICLES_DIR = Path("data/articles")

def build_prompt(source_title, source_summary, category, source_url):
    category_hint = "技術・IT" if category == "tech" else "ビジネス・マーケティング"
    return f"""あなたはnote向けの高品質な記事を執筆する専門のライターです。
【参考記事】タイトル:{source_title} 要約:{source_summary} カテゴリ:{category_hint}
参考記事を元に独自の視点で記事を書いてください。必ず以下のJSON形式のみで返答（コードブロック不要）:
{{"title":"タイトル30〜40文字","title_alternatives":["案2","案3"],"lead":"リード文150〜200文字","body":"本文Markdown形式## ###構造化1500〜2500文字","summary":"まとめ200〜300文字","hashtags":["タグ1","タグ2","タグ3","タグ4","タグ5","タグ6","タグ7","タグ8","タグ9","タグ10"],"estimated_read_time":5,"category":"{category}"}}"""

def generate_article(source_title, source_summary, category, source_url, source_name):
    api_key = os.environ.get("ANTHROPIC_API_KEY","")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が設定されていません")
        return None
    print(f"✍️ 記事生成中: {source_title[:40]}...")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role":"user","content":build_prompt(source_title,source_summary,category,source_url)}]
        )
        raw_text = message.content[0].text
        if "```json" in raw_text: json_str = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text: json_str = raw_text.split("```")[1].split("```")[0].strip()
        else: json_str = raw_text.strip()
        article_data = json.loads(json_str)
        article_data.update({"source_title":source_title,"source_url":source_url,"source_name":source_name,"generated_at":datetime.now().isoformat(),"status":"draft","ai_model":"claude-haiku-4-5"})
        print(f"✅ 記事生成完了: {article_data.get('title','')}")
        return article_data
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def format_for_note(article_data):
    lines = [article_data.get("lead",""),"",article_data.get("body",""),"","## まとめ","",article_data.get("summary",""),""]
    hashtags = article_data.get("hashtags",[])
    if hashtags: lines.append(" ".join([f"#{t}" if not t.startswith("#") else t for t in hashtags]))
    return "\n".join(lines)

def save_article(article_data):
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    filename = ARTICLES_DIR / f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename,"w",encoding="utf-8") as f: json.dump(article_data,f,ensure_ascii=False,indent=2)
    print(f"💾 記事保存: {filename}")
    return filename

def load_articles(status_filter=None):
    if not ARTICLES_DIR.exists(): return []
    articles = []
    for fp in sorted(ARTICLES_DIR.glob("article_*.json"),reverse=True):
        with open(fp,"r",encoding="utf-8") as f:
            data = json.load(f)
            data["_filepath"] = str(fp)
            if status_filter is None or data.get("status") == status_filter: articles.append(data)
    return articles

def update_article_status(filepath, status):
    with open(filepath,"r",encoding="utf-8") as f: data = json.load(f)
    data["status"] = status
    data["updated_at"] = datetime.now().isoformat()
    with open(filepath,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)