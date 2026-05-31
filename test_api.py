import urllib.request
import urllib.error
import json

url = 'https://funwitharts-production.up.railway.app/api/products/'
req = urllib.request.Request(url, headers={'Origin': 'https://fun-with-arts.vercel.app'})

try:
    res = urllib.request.urlopen(req)
    print("API Status:", res.status)
    data = json.loads(res.read().decode('utf-8'))
    products = data.get('results', data) if isinstance(data, dict) else data
    for p in products[:3]:
        img_url = p.get('image_url')
        print(f"\nProduct: {p.get('name')}")
        print(f"  - URL: {img_url}")
        if img_url:
            try:
                img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                img_res = urllib.request.urlopen(img_req)
                print(f"  - Status: {img_res.status} (SUCCESS)")
            except urllib.error.HTTPError as img_err:
                print(f"  - Status: {img_err.status} (FAILED)")
                print(img_err.read().decode('utf-8')[:200])
            except Exception as e:
                print(f"  - Error checking URL: {e}")
except urllib.error.HTTPError as e:
    print("API Error:", e.status)
    print(e.read().decode('utf-8'))


