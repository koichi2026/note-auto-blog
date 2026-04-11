import sys, os, json, urllib.request
sys.path.insert(0,'.')
os.environ['GITHUB_TOKEN']=os.environ.get('GITHUB_TOKEN','')
os.environ['GITHUB_REPO']='koichi2026/note-auto-blog'

token = os.environ['GITHUB_TOKEN']
repo = os.environ['GITHUB_REPO']

url = f'https://api.github.com/repos/{repo}/contents/data/articles'
req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'})
with urllib.request.urlopen(req) as r:
    files = json.loads(r.read().decode('utf-8'))

for f in files:
    if not f['name'].endswith('.json'):
        continue
    del_url = f['url']
    msg = 'delete ' + f['name']
    payload = json.dumps({'message': msg, 'sha': f['sha'], 'branch': 'master'}).encode('utf-8')
    del_req = urllib.request.Request(del_url, data=payload, headers={'Authorization': f'token {token}', 'Content-Type': 'application/json'}, method='DELETE')
    try:
        with urllib.request.urlopen(del_req) as r:
            print('削除: ' + f['name'])
    except Exception as e:
        print('エラー: ' + f['name'] + ' - ' + str(e))

print('完了')