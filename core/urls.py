import os
import re
import mimetypes

from django.contrib import admin
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest
from django.urls import include, path, re_path
from django.conf import settings
from django.utils._os import safe_join


def ranged_media_serve(request, path):
    try:
        full_path = safe_join(settings.MEDIA_ROOT, path)
    except SuspiciousFileOperation:
        raise Http404 from None

    if not os.path.exists(full_path):
        raise Http404

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    if content_type is None:
        content_type = 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '').strip()
    if range_header:
        match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not match:
            return HttpResponseBadRequest()
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) else file_size - 1
        last = min(last, file_size - 1)
        length = last - first + 1

        with open(full_path, 'rb') as f:
            f.seek(first)
            body = f.read(length)

        response = HttpResponse(body, status=206, content_type=content_type)
        response['Content-Range'] = f'bytes {first}-{last}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(length)
        return response

    response = FileResponse(open(full_path, 'rb'), content_type=content_type)
    response['Accept-Ranges'] = 'bytes'
    response['Content-Length'] = file_size
    return response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/rooms/', include('apps.rooms.urls')),
    path('api/chat/', include('plugins.chat.urls')),
    path('api/movies/', include('plugins.movies.urls')),
    path('api/sync/', include('plugins.sync.urls')),
    path('api/activity/', include('plugins.activity.urls')),
    path('api/social/', include('plugins.social.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', ranged_media_serve),
    ]
