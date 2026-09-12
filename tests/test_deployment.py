import subprocess
import io
from unittest.mock import Mock

import pytest

from scripts import deploy

IMAGE = 'ghcr.io/iftimie/takeaway_challenge@sha256:' + 'a' * 64


def test_cloudwatch_credentials_use_stdin_and_not_command_arguments(monkeypatch):
    monkeypatch.setenv('ENABLE_CLOUDWATCH', '1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'test-access-key')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test-secret-key')
    run = Mock()
    monkeypatch.setattr(deploy.subprocess, 'run', run)
    health = io.BytesIO(b'{"status":"ok"}')
    health.status = 200
    ui = io.BytesIO(b'<html>Takeaway</html>')
    ui.status = 200
    monkeypatch.setattr(deploy.urllib.request, 'urlopen', Mock(side_effect=[health, ui]))
    deploy.deploy('qa', '127.0.0.1', IMAGE, 'key', 'known')
    credential_call = run.call_args_list[1]
    assert 'aws_secret_access_key=test-secret-key' in credential_call.kwargs['input']
    for call in run.call_args_list:
        assert 'test-secret-key' not in ' '.join(call.args[0])
        assert 'test-access-key' not in ' '.join(call.args[0])


@pytest.mark.parametrize('environment', ['qa', 'prod'])
def test_deployment_uses_selected_environment_and_exact_digest(monkeypatch, environment):
    run = Mock()
    monkeypatch.setattr(deploy.subprocess, 'run', run)
    health = io.BytesIO(b'{"status":"ok"}')
    health.status = 200
    ui = io.BytesIO(b'<html>Takeaway</html>')
    ui.status = 200
    monkeypatch.setattr(deploy.urllib.request, 'urlopen', Mock(side_effect=[health, ui]))
    deploy.deploy(environment, '127.0.0.1', IMAGE, 'key', 'known')
    ssh = run.call_args_list[1].args[0]
    assert f'HostKeyAlias=takeaway-{environment}' in ssh
    assert ssh[-1] == f'cd /opt/takeaway && bash deploy.sh {IMAGE} {environment}'


def test_invalid_environment_does_not_connect(monkeypatch):
    run = Mock()
    monkeypatch.setattr(deploy.subprocess, 'run', run)
    with pytest.raises(ValueError):
        deploy.deploy('invalid', '127.0.0.1', IMAGE, 'key', 'known')
    run.assert_not_called()


@pytest.mark.parametrize('ip,image', [
    ('not-an-ip', IMAGE),
    ('127.0.0.1', 'ghcr.io/iftimie/takeaway_challenge:latest'),
])
def test_invalid_deployment_input_does_not_connect(monkeypatch, ip, image):
    run = Mock()
    monkeypatch.setattr(deploy.subprocess, 'run', run)
    with pytest.raises(ValueError):
        deploy.deploy("qa", ip, image, 'key', 'known')
    run.assert_not_called()


def test_failed_remote_deployment_stops_before_smoke_checks(monkeypatch):
    monkeypatch.setattr(deploy.subprocess, 'run', Mock(side_effect=[
        None, subprocess.CalledProcessError(1, 'ssh'),
    ]))
    request = Mock()
    monkeypatch.setattr(deploy.urllib.request, 'urlopen', request)
    with pytest.raises(subprocess.CalledProcessError):
        deploy.deploy('qa', '127.0.0.1', IMAGE, 'key', 'known')
    request.assert_not_called()


def test_unreachable_app_fails_deployment(monkeypatch):
    monkeypatch.setattr(deploy.subprocess, 'run', Mock())
    monkeypatch.setattr(deploy.time, 'sleep', Mock())
    monkeypatch.setattr(deploy.urllib.request, 'urlopen',
                        Mock(side_effect=deploy.urllib.error.URLError('unavailable')))
    with pytest.raises(deploy.urllib.error.URLError):
        deploy.deploy('qa', '127.0.0.1', IMAGE, 'key', 'known')


def test_wrong_health_payload_fails_deployment(monkeypatch):
    monkeypatch.setattr(deploy.subprocess, 'run', Mock())
    response = io.BytesIO(b'{"status":"wrong"}')
    response.status = 200
    monkeypatch.setattr(deploy.urllib.request, 'urlopen', Mock(return_value=response))
    with pytest.raises(ValueError, match='Unexpected smoke response'):
        deploy.deploy('qa', '127.0.0.1', IMAGE, 'key', 'known')
