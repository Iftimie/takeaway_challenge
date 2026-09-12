"""Disposable browser database only; never reads the application .env."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update({
    'POSTGRES_DB': 'takeaway_browser_test', 'POSTGRES_USER': 'browser_test',
    'POSTGRES_PASSWORD': 'browser_test_only', 'POSTGRES_HOST': '127.0.0.1',
    'POSTGRES_PORT': '55432',
})

from sqlalchemy import delete, text
from sqlalchemy.orm import Session
from app.db import get_engine
from app.models import Restaurant


def compose(*args):
    subprocess.run(['docker', '--context', 'desktop-linux', 'compose', '-p',
                    'takeaway-browser-tests', '-f', str(ROOT / 'compose.browser-tests.yaml'),
                    *args], cwd=ROOT, check=True)


def fixtures(seed):
    # The fixed endpoint and identity check prevent cleanup of the normal DB.
    with Session(get_engine()) as session:
        if (session.scalar(text('SELECT current_database()')) != 'takeaway_browser_test'
                or session.scalar(text('SELECT current_user')) != 'browser_test'):
            raise RuntimeError('Refusing fixture changes outside the browser test database')
        session.execute(delete(Restaurant))
        if seed:
            session.add_all([Restaurant(name=f'Browser Restaurant {i}', address=f'Test Street {i}')
                             for i in range(1, 4)])
        session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'seed', 'clean', 'stop'])
    action = parser.parse_args().action
    if action == 'prepare':
        try:
            compose('up', '-d', '--wait')
            subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT, check=True)
        except BaseException:
            compose('down')
            raise
    elif action == 'stop':
        compose('down')
    else:
        fixtures(action == 'seed')
