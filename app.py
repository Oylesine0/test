import base64
import requests
from flask import Flask, Response, render_template_string, request, abort
from urllib.parse import urljoin, quote

# --- Flask Uygulamasını Başlatma ---
app = Flask(__name__)

# --- Stabil Vavoo Çözümleyici ---
class VavooResolver:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MediaHubMX/2'
        })
    
    def get_auth_signature(self):
        headers = { "user-agent": "okhttp/4.11.0", "accept": "application/json", "content-type": "application/json; charset=utf-8" }
        data = {
            "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
            "reason": "app-blur", "locale": "de", "theme": "dark",
            "metadata": {
                "device": {"type": "Handset", "brand": "google", "model": "Nexus", "name": "21081111RG", "uniqueId": "d10e5d99ab665233"},
                "os": {"name": "android", "version": "7.1.2", "abis": ["arm64-v8a", "armeabi-v7a", "armeabi"], "host": "android"},
                "app": {"platform": "android", "version": "3.1.20", "buildId": "289515000", "engine": "hbc85", "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"], "installer": "app.revanced.manager.flutter"},
                "version": {"package": "tv.vavoo.app", "binary": "3.1.20", "js": "3.1.20"}
            }, "appFocusTime": 0, "playerActive": False, "playDuration": 0, "devMode": False, "hasAddon": True, "castConnected": False,
            "package": "tv.vavoo.app", "version": "3.1.20", "process": "app", "firstAppStart": 1743962904623, "lastAppStart": 1743962904623,
            "ipLocation": "", "adblockEnabled": True,
            "proxy": {"supported": ["ss", "openvpn"], "engine": "ss", "ssVersion": 1, "enabled": True, "autoServer": True, "id": "pl-waw"},
            "iap": {"supported": False}
        }
        try:
            resp = self.session.post("https://www.vavoo.tv/api/app/ping", json=data, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.json().get("addonSig")
        except Exception as e:
            print(f"Vavoo imza alınırken hata: {e}")
            return None

    def resolve_vavoo_link(self, link):
        signature = self.get_auth_signature()
        if not signature: return None
        headers = { "user-agent": "MediaHubMX/2", "accept": "application/json", "mediahubmx-signature": signature }
        data = { "language": "de", "region": "AT", "url": link, "clientVersion": "3.0.2" }
        try:
            resp = self.session.post("https://vavoo.to/mediahubmx-resolve.json", json=data, headers=headers, timeout=20)
            resp.raise_for_status()
            result = resp.json()
            if isinstance(result, list) and result: return result[0].get("url")
            elif isinstance(result, dict): return result.get("url")
            return None
        except Exception as e:
            print(f"Vavoo linki çözülürken hata: {e}")
            return None

# --- Web Arayüzü ---
@app.route('/')
def index():
    # Bu kısımda değişiklik yok
    html_template = """
    <!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>M3U8 Proxy Oluşturucu</title><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background-color:#f0f2f5}.container{background:white;padding:40px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);text-align:center;max-width:600px;width:90%}h1{color:#333}p{color:#666}input[type="text"]{width:100%;padding:12px;margin-top:20px;border:1px solid #ccc;border-radius:8px;font-size:16px;box-sizing:border-box}button{background-color:#007bff;color:white;padding:12px 20px;border:none;border-radius:8px;font-size:16px;cursor:pointer;margin-top:15px}button:hover{background-color:#0056b3}#result{margin-top:25px;word-wrap:break-word;background:#e9ecef;padding:10px;border-radius:8px}</style></head><body><div class="container"><h1>M3U8 Proxy Oluşturucu</h1><p>Oynatmak istediğiniz Vavoo veya direkt .m3u8 linkini yapıştırın.</p><input type="text" id="urlInput" placeholder="https://vavoo.to/..."><button onclick="generateProxyUrl()">Proxy Linki Oluştur</button><div id="result"></div></div><script>function generateProxyUrl(){const e=document.getElementById("urlInput").value.trim();if(!e){alert("Lütfen bir URL girin.");return}const t=btoa(e).replace(/\\+/g,"-").replace(/\\//g,"_").replace(/=/g,"");const o=`${window.location.origin}/play/${t}.m3u8`;document.getElementById("result").innerText=o}</script></body></html>
    """
    return render_template_string(html_template)

# --- Ana M3U8 Oynatma Uç Noktası ---
@app.route('/play/<encoded_url>.m3u8')
def play_m3u8(encoded_url):
    try:
        decoded_url = base64.b64decode(encoded_url.replace('-', '+').replace('_', '/') + '==').decode('utf-8')
    except Exception:
        abort(400, "Geçersiz URL kodu.")

    if 'vavoo.to' in decoded_url:
        resolver = VavooResolver()
        final_m3u8_url = resolver.resolve_vavoo_link(decoded_url)
        if not final_m3u8_url:
            abort(500, "Vavoo bağlantısı çözülemedi.")
    else:
        final_m3u8_url = decoded_url

    # --- YENİ EKLENEN KISIM ---
    # Artık video parçalarını indirirken kullanılacak başlıkları burada tanımlıyoruz.
    headers_for_stream = {
        'Referer': final_m3u8_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    try:
        # Ana M3U8 listesini bu başlıklarla indiriyoruz.
        response = requests.get(final_m3u8_url, headers=headers_for_stream, timeout=10)
        response.raise_for_status()
        
        original_content = response.text
        modified_lines = []
        
        # --- YENİ EKLENEN KISIM ---
        # Başlıkları URL'ye eklemek için kodluyoruz.
        encoded_headers = "&".join([f"h_{key}={quote(value)}" for key, value in headers_for_stream.items()])

        for line in original_content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                segment_url = urljoin(final_m3u8_url, line)
                encoded_segment = base64.urlsafe_b64encode(segment_url.encode('utf-8')).decode('utf-8').rstrip("=")
                
                # .ts linkine başlıkları da query parametresi olarak ekliyoruz.
                modified_lines.append(f"/ts/{encoded_segment}.ts?{encoded_headers}")
            else:
                modified_lines.append(line)
        
        modified_content = "\n".join(modified_lines)
        return Response(modified_content, mimetype='application/vnd.apple.mpegurl')

    except requests.RequestException as e:
        abort(502, f"Kaynak M3U8 dosyasına ulaşılamadı: {e}")


# --- .ts Video Segmentleri için Proxy ---
@app.route('/ts/<encoded_ts_url>.ts')
def proxy_ts(encoded_ts_url):
    try:
        ts_url = base64.b64decode(encoded_ts_url.replace('-', '+').replace('_', '/') + '==').decode('utf-8')
    except Exception:
        abort(400, "Geçersiz TS segment URL'si.")
    
    # --- YENİ EKLENEN KISIM ---
    # URL'den gelen başlıkları alıp bir sözlüğe (dictionary) çeviriyoruz.
    headers_to_forward = {}
    for key, value in request.args.items():
        if key.startswith('h_'):
            header_key = key[2:]
            headers_to_forward[header_key] = value

    try:
        # Video segmentini, artık doğru başlıklarla indiriyoruz.
        r = requests.get(ts_url, stream=True, headers=headers_to_forward, timeout=20)
        r.raise_for_status()
        return Response(r.iter_content(chunk_size=1024*1024), content_type=r.headers.get('Content-Type'))
    except requests.RequestException as e:
        abort(502, f"Video segmentine ulaşılamadı: {e}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7860)