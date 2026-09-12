"""Deploy a published digest over verified SSH, then check the environment over public HTTP."""
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request


def deploy(environment, ip, image, key, known_hosts):
    if environment not in ("qa", "prod"):
        raise ValueError("Use qa or prod")
    ip = str(ipaddress.IPv4Address(ip))
    if not re.fullmatch(r'ghcr\.io/iftimie/takeaway_challenge@sha256:[a-f0-9]{64}', image):
        raise ValueError('Expected the immutable published takeaway image digest')
    root = Path(__file__).resolve().parents[1]
    options = ['-i', key, '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', f'HostKeyAlias=takeaway-{environment}',
               '-o', f'UserKnownHostsFile={known_hosts}', '-o', 'ConnectTimeout=15']
    target = f'deploy@{ip}'
    files = [str(root / 'deploy' / name) for name in
             ('compose.yaml', 'compose.logging.yaml', 'nginx.conf', 'deploy.sh')]
    subprocess.run(['scp', *options, *files, f'{target}:/opt/takeaway/'], check=True)
    if os.environ.get('ENABLE_CLOUDWATCH') == '1':
        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        if not access_key or not secret_key or any(c in access_key + secret_key for c in '\r\n'):
            raise ValueError('Invalid CloudWatch credentials')
        credentials = f'[default]\naws_access_key_id={access_key}\naws_secret_access_key={secret_key}\n'
        # Docker reads its root credentials file. Send values over SSH stdin only.
        command = ("docker run --rm -i -v /root/.aws:/aws alpine:3.23 "
                   "sh -c 'umask 077; cat > /aws/credentials' "
                   "&& touch /opt/takeaway/.cloudwatch-enabled")
        subprocess.run(['ssh', *options, target, command], input=credentials,
                       text=True, check=True)
    subprocess.run(['ssh', *options, target,
                    f'cd /opt/takeaway && bash deploy.sh {image} {environment}'], check=True)
    for path in ('/health', '/ui/'):
        for attempt in range(10):
            try:
                with urllib.request.urlopen(f'http://{ip}{path}', timeout=10) as response:
                    body = response.read(1024 * 1024)
                    if (response.status != 200
                            or (path == '/health' and json.loads(body) != {'status': 'ok'})
                            or (path == '/ui/' and b'<html' not in body.lower())):
                        raise ValueError(f'Unexpected smoke response for {path}')
                break
            except (urllib.error.URLError, TimeoutError):
                if attempt == 9:
                    raise
                time.sleep(3)
    print(f'{environment} smoke checks passed: http://{ip}/ui/ ({image})')


if __name__ == '__main__':
    if len(sys.argv) != 6:
        raise SystemExit('Usage: deploy.py ENVIRONMENT IP IMAGE SSH_KEY KNOWN_HOSTS')
    deploy(*sys.argv[1:])
