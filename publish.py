"""Publie sur Instagram (@beltchase.officiel) les posts de queue.json dont l'heure est passée.

Lancé toutes les 15 min par GitHub Actions (.github/workflows/publish.yml).
Seuls les posts au statut « approved » partent (Axel valide la semaine avant).
API officielle « Instagram API with Instagram Login » : aucun risque pour le compte.

Variables d'environnement : IG_TOKEN (jeton longue durée), REPO (owner/nom, pour les URL des images).
`python3 publish.py --dry` : montre ce qui partirait, sans rien publier.
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

API = 'https://graph.instagram.com'
QUEUE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'queue.json')
DRY = '--dry' in sys.argv


def call(method, path, **params):
    params['access_token'] = os.environ['IG_TOKEN']
    data = urllib.parse.urlencode(params).encode()
    url = f'{API}/{path}'
    req = urllib.request.Request(url + ('?' + data.decode() if method == 'GET' else ''), data=None if method == 'GET' else data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{method} {path}: {e.code} {e.read().decode()[:400]}') from None


def image_url(path):
    return f"https://raw.githubusercontent.com/{os.environ.get('REPO', 'Axel-Sys1/beltchase-social')}/main/{path}"


def publish(user_id, post):
    params = {'image_url': image_url(post['image'])}
    if post['type'] == 'story':
        params['media_type'] = 'STORIES'
    else:
        params['caption'] = post['caption']
    container = call('POST', f'{user_id}/media', **params)['id']
    for _ in range(30):  # l'image est téléchargée par Instagram : on attend qu'elle soit prête
        status = call('GET', container, fields='status_code').get('status_code')
        if status == 'FINISHED':
            break
        if status in ('ERROR', 'EXPIRED'):
            raise RuntimeError(f'conteneur {container} : {status}')
        time.sleep(5)
    return call('POST', f'{user_id}/media_publish', creation_id=container)['id']


def main():
    queue = json.load(open(QUEUE, encoding='utf-8'))
    now = datetime.now(timezone.utc)
    due = [p for p in queue if p['status'] == 'approved' and datetime.fromisoformat(p['at']) <= now]
    if not due:
        print('Rien à publier.')
        return
    if DRY:
        for p in due:
            print('Partirait :', p['id'], p['at'])
        return
    user_id = call('GET', 'me', fields='user_id,username')['user_id']
    failed = False
    for p in due:
        try:
            p['media_id'] = publish(user_id, p)
            p['status'] = 'posted'
            p['posted_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
            print('Publié :', p['id'], p['media_id'])
        except Exception as e:  # on note l'erreur et on réessaie au prochain passage (3 fois max)
            p['errors'] = p.get('errors', 0) + 1
            p['last_error'] = str(e)[:300]
            if p['errors'] >= 3:
                p['status'] = 'failed'
            failed = True
            print('Erreur :', p['id'], e)
    json.dump(queue, open(QUEUE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(QUEUE, 'a').write('\n')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
