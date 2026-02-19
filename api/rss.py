from http.server import BaseHTTPRequestHandler
import urllib.parse
import feedparser
import json

class handler(BaseHTTPRequestHandler):
    
    # Вспомогательный метод для добавления CORS-заголовков
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    # Обработка preflight-запросов от браузера (нужно для CORS)
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rss_url = query.get('url', [None])[0]

        # 1. Проверка наличия URL
        if not rss_url:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing url parameter'}).encode('utf-8'))
            return

        try:
            # 2. Загружаем и парсим RSS
            feed = feedparser.parse(rss_url)
            
            # Если feedparser вернул фатальную ошибку (невалидный XML, 404 и т.д.)
            if feed.bozo and hasattr(feed, 'bozo_exception'):
                print(f"Внимание: ошибка парсинга {rss_url} - {feed.bozo_exception}")

            items = []
            for entry in feed.entries[:20]:
                # Ограничиваем описание, чтобы не перегружать ответ (экономим трафик)
                raw_desc = entry.get('description', '')
                short_desc = raw_desc[:500] + '...' if len(raw_desc) > 500 else raw_desc

                items.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'pubDate': entry.get('published', ''),
                    'description': short_desc
                })

            # 3. Успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self._send_cors_headers()
            
            # 4. КЭШИРОВАНИЕ НА СТОРОНЕ VERCEL (Критически важно для производительности)
            # s-maxage=300 (кэшируем на узлах Vercel на 5 минут)
            # stale-while-revalidate=600 (показываем старый кэш еще 10 минут, пока в фоне качается новый)
            self.send_header('Cache-Control', 's-maxage=300, stale-while-revalidate=600')
            self.end_headers()
            
            # Отправляем JSON, сохраняя кириллицу (ensure_ascii=False)
            self.wfile.write(json.dumps({'items': items}, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # 5. Глобальный перехватчик ошибок
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Server error: {str(e)}'}).encode('utf-8'))

