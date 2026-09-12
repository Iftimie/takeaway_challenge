"""Exercise D8 Compose with an isolated local database; remove it afterward.

Usage: python scripts/test_deployment.py IMAGE
Set DOCKER_CONTEXT=desktop-linux on Windows. Requires local port 8768 to be free.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import urllib.request


def main():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, APP_IMAGE=sys.argv[1], HTTP_PORT='8768', HTTP_BIND='127.0.0.1')
    with tempfile.TemporaryDirectory() as directory:
        settings = Path(directory) / '.env'
        settings.write_text('POSTGRES_DB=deployment_test\nPOSTGRES_USER=test\n'
                            f'POSTGRES_PASSWORD={secrets.token_hex(32)}\n'
                            f'JWT_SECRET={secrets.token_hex(32)}\n')
        command = ['docker', 'compose', '-p', 'takeaway-d8-test', '--env-file',
                   str(settings), '-f', str(root / 'deploy/compose.yaml')]

        def compose(*args):
            subprocess.run([*command, *args], env=env, check=True)

        def request(path, data=None):
            body = None if data is None else json.dumps(data).encode()
            req = urllib.request.Request('http://127.0.0.1:8768' + path, data=body,
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.load(response)

        try:
            compose('up', '-d', '--wait', 'db')
            compose('run', '--rm', '--no-deps', 'migrate')
            compose('up', '-d', '--no-deps', '--wait', 'app', 'nginx')
            request('/health')
            email = 'persistence@example.com'
            password = secrets.token_hex(16)
            request('/auth/register', {'email': email, 'password': password, 'name': 'Persistence'})
            # Re-run migrations and replace the app, retaining the database volume.
            compose('run', '--rm', '--no-deps', 'migrate')
            compose('up', '-d', '--no-deps', '--force-recreate', '--wait', 'app')
            compose('exec', '-T', 'nginx', 'nginx', '-s', 'reload')
            assert request('/auth/login', {'email': email, 'password': password})['access_token']
            print('PASS: fresh migrations, HTTP health, redeploy and persisted account login')
        finally:
            compose('down', '--volumes', '--remove-orphans')


if __name__ == '__main__':
    main()
