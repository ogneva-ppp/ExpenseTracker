"""Firebase Authentication + Realtime Database via REST, without admin credentials."""
import json
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def request_json(url, method='GET', payload=None, timeout=15):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, method=method,
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        raise RuntimeError('Firebase HTTP {}: {}'.format(exc.code, exc.read().decode('utf-8')[:250])) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError('Нет соединения с Firebase: {}'.format(exc)) from exc


def check_database_url(url):
    parsed = urlparse(url.strip())
    if parsed.scheme != 'https' or not parsed.hostname or not (
        parsed.hostname.endswith('.firebaseio.com') or parsed.hostname.endswith('.firebasedatabase.app')
    ) or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError('Укажите HTTPS URL Firebase Realtime Database без пути')
    return url.strip().rstrip('/')


def login(api_key, email, password):
    if not all((api_key.strip(), email.strip(), password)):
        raise ValueError('Заполните API key, email и пароль')
    url = 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?'+urlencode({'key': api_key.strip()})
    result = request_json(url, 'POST', {'email': email.strip(), 'password': password, 'returnSecureToken': True})
    return result['localId'], result['idToken']


def cloud_url(database_url, uid, token):
    return '{}/users/{}/transactions.json?{}'.format(
        check_database_url(database_url), quote(uid, safe=''), urlencode({'auth': token}))


def upload(database_url, uid, token, rows):
    # PUT intentionally replaces the current user's cloud snapshot.
    return request_json(cloud_url(database_url, uid, token), 'PUT', rows)


def download(database_url, uid, token):
    result = request_json(cloud_url(database_url, uid, token))
    return [] if result is None else result
