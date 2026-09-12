import subprocess
import io
from unittest.mock import Mock

import pytest

from scripts import deploy_qa

IMAGE = 'ghcr.io/iftimie/takeaway_challenge@sha256:' + 'a' * 64


@pytest.mark.parametrize('ip,image', [
    ('not-an-ip', IMAGE),
    ('127.0.0.1', 'ghcr.io/iftimie/takeaway_challenge:latest'),
])
def test_invalid_deployment_input_does_not_connect(monkeypatch, ip, image):
    run = Mock()
    monkeypatch.setattr(deploy_qa.subprocess, 'run', run)
    with pytest.raises(ValueError):
        deploy_qa.deploy(ip, image, 'key', 'known')
    run.assert_not_called()


def test_failed_remote_deployment_stops_before_smoke_checks(monkeypatch):
    monkeypatch.setattr(deploy_qa.subprocess, 'run', Mock(side_effect=[
        None, subprocess.CalledProcessError(1, 'ssh'),
    ]))
    request = Mock()
    monkeypatch.setattr(deploy_qa.urllib.request, 'urlopen', request)
    with pytest.raises(subprocess.CalledProcessError):
        deploy_qa.deploy('127.0.0.1', IMAGE, 'key', 'known')
    request.assert_not_called()


def test_unreachable_app_fails_deployment(monkeypatch):
    monkeypatch.setattr(deploy_qa.subprocess, 'run', Mock())
    monkeypatch.setattr(deploy_qa.time, 'sleep', Mock())
    monkeypatch.setattr(deploy_qa.urllib.request, 'urlopen',
                        Mock(side_effect=deploy_qa.urllib.error.URLError('unavailable')))
    with pytest.raises(deploy_qa.urllib.error.URLError):
        deploy_qa.deploy('127.0.0.1', IMAGE, 'key', 'known')


def test_wrong_health_payload_fails_deployment(monkeypatch):
    monkeypatch.setattr(deploy_qa.subprocess, 'run', Mock())
    response = io.BytesIO(b'{"status":"wrong"}')
    response.status = 200
    monkeypatch.setattr(deploy_qa.urllib.request, 'urlopen', Mock(return_value=response))
    with pytest.raises(ValueError, match='Unexpected smoke response'):
        deploy_qa.deploy('127.0.0.1', IMAGE, 'key', 'known')
