import os
import tempfile
from django.test import TestCase, RequestFactory, override_settings
from core.urls import ranged_media_serve


class RangedMediaServeTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self._media_dir = tempfile.mkdtemp()
        self._settings_override = override_settings(MEDIA_ROOT=self._media_dir)
        self._settings_override.enable()
        self.addCleanup(self._settings_override.disable)
        self.content = b'0123456789abcdef'
        self.rel_path = 'test_video.mp4'
        with open(os.path.join(self._media_dir, self.rel_path), 'wb') as f:
            f.write(self.content)

    def test_full_file_response(self):
        request = self.factory.get(f'/media/{self.rel_path}')
        response = ranged_media_serve(request, self.rel_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        self.assertEqual(b''.join(response.streaming_content), self.content)

    def test_range_request_partial_content(self):
        request = self.factory.get(f'/media/{self.rel_path}', HTTP_RANGE='bytes=0-4')
        response = ranged_media_serve(request, self.rel_path)
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Content-Range'], f'bytes 0-4/{len(self.content)}')
        self.assertEqual(response.content, self.content[:5])

    def test_range_open_ended(self):
        request = self.factory.get(f'/media/{self.rel_path}', HTTP_RANGE='bytes=10-')
        response = ranged_media_serve(request, self.rel_path)
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, self.content[10:])

    def test_invalid_range_header(self):
        request = self.factory.get(f'/media/{self.rel_path}', HTTP_RANGE='invalid')
        response = ranged_media_serve(request, self.rel_path)
        self.assertEqual(response.status_code, 400)

    def test_file_not_found(self):
        request = self.factory.get('/media/missing.mp4')
        with self.assertRaises(Exception):
            ranged_media_serve(request, 'missing.mp4')

    def test_path_traversal_blocked(self):
        request = self.factory.get('/media/../core/settings.py')
        with self.assertRaises(Exception):
            ranged_media_serve(request, '../core/settings.py')

    def test_unknown_extension_octet_stream(self):
        rel = 'data.bin'
        with open(os.path.join(self._media_dir, rel), 'wb') as f:
            f.write(b'binary')
        request = self.factory.get(f'/media/{rel}')
        response = ranged_media_serve(request, rel)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/octet-stream', response['Content-Type'])
