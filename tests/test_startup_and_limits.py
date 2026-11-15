import json
import threading
import urllib.request
from http.server import HTTPServer

import pytest

from worker_health import HealthHandler
from app.services.ai import _validate_response, AIResponseValidationError, analyze_case
from unittest.mock import patch


def test_worker_http_health_is_readable_only_for_allowed_origin(monkeypatch):
    monkeypatch.setenv('ALLOWED_ORIGINS', 'https://demo.example')
    server = HTTPServer(('127.0.0.1', 0), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        preflight = urllib.request.Request(
            f'http://127.0.0.1:{server.server_port}/health', method='OPTIONS',
            headers={'Origin': 'https://demo.example',
                     'Access-Control-Request-Method': 'GET',
                     'Access-Control-Request-Headers': 'cache-control,pragma'},
        )
        with urllib.request.urlopen(preflight, timeout=2) as response:
            assert response.status == 204
            assert response.headers['Access-Control-Allow-Origin'] == 'https://demo.example'
            assert 'pragma' in response.headers['Access-Control-Allow-Headers']
        for origin, expected in [('https://demo.example', 'https://demo.example'), ('https://other.example', None)]:
            request = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/health', headers={'Origin': origin})
            with urllib.request.urlopen(request, timeout=2) as response:
                assert json.load(response) == {'http_service': 'awake'}
                assert response.headers.get('Access-Control-Allow-Origin') == expected
                assert response.headers['Vary'] == 'Origin'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_oversized_case_is_rejected_before_queue(client):
    response = client.post('/jobs/upload', data={'case_text': 'x' * 20001})
    assert response.status_code == 413
    client.mock_task.delay.assert_not_called()


def test_ai_rejects_oversize_without_sending_to_groq():
    with patch('app.services.ai.client.chat.completions.create') as create:
        with pytest.raises(AIResponseValidationError):
            analyze_case('x' * 20001)
        create.assert_not_called()


@pytest.mark.parametrize('value', [None, [], 'text', 1])
def test_ai_rejects_non_object(value):
    with pytest.raises(AIResponseValidationError):
        _validate_response(value)
