@'
import json, os, base64, urllib.request, urllib.error
from datetime import datetime

def save_article_to_github(article_data):
    token = os.environ.get("GITHUB_TOKEN","")
    repo = os.environ.get("GITHUB_REPO","")
    if not token or not repo:
        return {"success":False,"message":"GITHUB_TOKEN or GITHUB_REPO not set"}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/articles/article_{timestamp}.json"
    content = json.dumps(article_data,ensure_ascii=False,indent=2)
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    payload = {"message":f"add article: {article_data.get('title','')[:40]}","content":content_b64,"branch":"master"}
    req = urllib.request.Request(url,data=json.dumps(payload).encode("utf-8"),headers={"Authorization":f"token {token}","Content-Type":"application/json","Accept":"application/vnd.github.v3+json"},method="PUT")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return {"success":True,"message":"GitHubに保存しました","path":filename}
    except urllib.error.HTTPError as e:
        return {"success":False,"message":f"GitHub保存エラー: {e.read().decode('utf-8')[:200]}"}
    except Exception as e:
        return {"success":False,"message":f"エラー: {str(e)}"}

def load_articles_from_github():
    token = os.environ.get("GITHUB_TOKEN","")
    repo = os.environ.get("GITHUB_REPO","")
    if not token or not repo:
        return []
    url = f"https://api.github.com/repos/{repo}/contents/data/articles"
    req = urllib.request.Request(url,headers={"Authorization":f"token {token}","Accept":"application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            files = json.loads(r.read().decode("utf-8"))
        articles = []
        for f in sorted(files,key=lambda x:x["name"],reverse=True):
            if not f["name"].endswith(".json"):
                continue
            file_req = urllib.request.Request(f["download_url"],headers={"Authorization":f"token {token}"})
            with urllib.request.urlopen(file_req,timeout=30) as r:
                article = json.loads(r.read().decode("utf-8"))
                article["_filepath"] = f["name"]
                article["_github_path"] = f["path"]
                articles.append(article)
        return articles
    except Exception as e:
        print(f"GitHub記事取得エラー: {e}")
        return []
'@ | Set-Content -Path "github_storage.py" -Encoding UTF8