import urllib.request
import urllib.error

url = 'https://funwitharts-production.up.railway.app/api/products/'
req = urllib.request.Request(url, headers={'Origin': 'https://fun-with-arts.vercel.app'})

try:
    res = urllib.request.urlopen(req)
    print("Status:", res.status)
    print("CORS Header:", res.getheader('Access-Control-Allow-Origin'))
    print(res.read().decode('utf-8')[:200])
except urllib.error.HTTPError as e:
    print("Error:", e.status)
    print(e.read().decode('utf-8'))
