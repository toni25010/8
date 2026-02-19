from http.server import BaseHTTPRequestHandler
import urllib.parse
import feedparser
import json

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Разбираем параметры запроса
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rss_url = query.get('url', [None])[0]

        if not rss_url:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing url parameter'}).encode())
            return

        # Загружаем и парсим RSS
        feed = feedparser.parse(rss_url)
        items = []
        for entry in feed.entries[:20]:  # ограничим 20 новостями
            items.append({
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'pubDate': entry.get('published', ''),
                'description': entry.get('description', '')
            })

        # Отправляем ответ
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'items': items}).encode())

        return