import re

from fastapi.testclient import TestClient

from app.main import app


def test_ui_redirect_and_local_assets():
    with TestClient(app) as client:
        redirect = client.get('/ui', follow_redirects=False)
        assert redirect.status_code == 307
        assert redirect.headers['location'].endswith('/ui/')
        page = client.get('/ui/')
        assert page.status_code == 200
        assert 'text/html' in page.headers['content-type']
        assets = re.findall(r'(?:src|href)="(/ui/assets/[^\"]+)"', page.text)
        assert any(path.endswith('.js') for path in assets)
        assert any(path.endswith('.css') for path in assets)
        for path in assets:
            asset = client.get(path)
            assert asset.status_code == 200
            assert asset.content
        assert client.get('/ui/App.vue').status_code == 404


def test_ui_missing_asset_does_not_return_html_shell():
    with TestClient(app) as client:
        assert client.get('/ui/missing.js').status_code == 404
        assert client.get('/health').json() == {'status': 'ok'}
        assert client.get('/openapi.json').status_code == 200
