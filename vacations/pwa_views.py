from pathlib import Path

from django.conf import settings
from django.http import FileResponse


def _pwa_file(filename: str):
    return Path(settings.BASE_DIR) / 'vacations' / 'static' / 'vacations' / 'pwa' / filename


def manifest(request):
    return FileResponse(open(_pwa_file('manifest.webmanifest'), 'rb'), content_type='application/manifest+json')


def service_worker(request):
    response = FileResponse(open(_pwa_file('service-worker.js'), 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response
