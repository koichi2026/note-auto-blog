import json, os, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

ARTICLES_DIR = Path("data/articles")

def build_prompt(source_title, source_summary, category, source_url):
    category_hint = "技術・IT" if category == "tech" else "ビジネス・マーケティング"
    return f"""あなたはnote向けの高品質な記事を執筆する専門のライターです。以下のJSON形式のみで返答してください（コードブロック不要）：
{{"title":"記事タイトル30〜40文字","title_alternatives":["案2","案3"],"lead":"リード文150〜200文字","body":"本文Markdown形式## ###で構造化1500〜2500文字","summary":"まとめ200〜300文字","hashtags":["タグ1","タグ2","タグ3","タグ4","タグ5","タグ6","タグ7","タグ8","タグ9","タグ10"],"estimated_read_time":5,"category":"{category}"}}
【参考記事】タイトル:{source_title} 要約:{source_summary} カテゴリ:{category_hint} URL:{source_url}
参考記事を元に読者にとって価値のある独自の視点・解説・考察を加えた記事を書いてください。"""

def call_gemini_api(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}"
    payload = {"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.7,"maxOutputTokens":4000}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"❌ Gemini APIエラー {e.code}: {e.read().decode('utf-8')[:200]}")
        return None
    except Exception as e:
        print(f"❌ API呼び出しエラー: {e}")
        return None

def generate_article(source_title, source_summary, category, source_url, source_name):
    api_key = os.environ.get("GEMINI_API_KEY","")
    if not api_key:
        print("❌ GEMINI_API_KEY が設定されていません")
        return None
    print(f"✍️ 記事生成中: {source_title[:40]}...")
    raw_text = call_gemini_api(build_prompt(source_title, source_summary, category, source_url), api_key)
    if not raw_text:
        return None
    try:
        if "```json" in raw_text: json_str = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text: json_str = raw_text.split("```")[1].split("```")[0].strip()
        else: json_str = raw_text.strip()
        article_data = json.loads(json_str)
        article_data.update({"source_title":source_title,"source_url":source_url,"source_name":source_name,"generated_at":datetime.now().isoformat(),"status":"draft","ai_model":"gemini-2.0-flash-lite"})
        print(f"✅ 記事生成完了: {article_data.get('title','タイトル不明')}")
        return article_data
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析エラー: {e}\nレスポンス: {raw_text[:300]}")
        return None

def format_for_note(article_data):
    lines = [article_data.get("lead",""),"",article_data.get("body",""),"","## まとめ","",article_data.get("summary",""),""]
    hashtags = article_data.get("hashtags",[])
    if hashtags: lines.append(" ".join([f"#{t}" if not t.startswith("#") else t for t in hashtags]))
    return "\n".join(lines)

def save_article(article_data):
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = ARTICLES_DIR / f"article_{timestamp}.json"
    with open(filename,"w",encoding="utf-8") as f: json.dump(article_data,f,ensure_ascii=False,indent=2)
    print(f"💾 記事保存: {filename}")
    return filename

def load_articles(status_filter=None):
    if not ARTICLES_DIR.exists(): return []
    articles = []
    for filepath in sorted(ARTICLES_DIR.glob("article_*.json"),reverse=True):
        with open(filepath,"r",encoding="utf-8") as f:
            data = json.load(f)
            data["_filepath"] = str(filepath)
            if status_filter is None or data.get("status") == status_filter: articles.append(data)
    return articles

def update_article_status(filepath, status):
    with open(filepath,"r",encoding="utf-8") as f: data = json.load(f)
    data["status"] = status
    data["updated_at"] = datetime.now().isoformat()
    with open(filepath,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
