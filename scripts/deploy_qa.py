"""Deploy a published digest over verified SSH, then check QA over public HTTP."""
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request


def deploy(ip, image, key, known_hosts):
    ip = str(ipaddress.IPv4Address(ip))
    if not re.fullmatch(r'ghcr\.io/iftimie/takeaway_challenge@sha256:[a-f0-9]{64}', image):
        raise ValueError('Expected the immutable published takeaway image digest')
    root = Path(__file__).resolve().parents[1]
    options = ['-i', key, '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlias=takeaway-qa',
               '-o', f'UserKnownHostsFile={known_hosts}', '-o', 'ConnectTimeout=15']
    target = f'deploy@{ip}'
    files = [str(root / 'deploy' / name) for name in
             ('compose.yaml', 'nginx.conf', 'deploy.sh')]
    subprocess.run(['scp', *options, *files, f'{target}:/opt/takeaway/'], check=True)
    subprocess.run(['ssh', *options, target,
                    f'cd /opt/takeaway && bash deploy.sh {image}'], check=True)
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
    print(f'QA smoke checks passed: http://{ip}/ui/ ({image})')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit('Usage: deploy_qa.py IP IMAGE SSH_KEY KNOWN_HOSTS')
    deploy(*sys.argv[1:])
