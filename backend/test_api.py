import urllib.request
import json
import urllib.error

req = urllib.request.Request(
    'http://localhost:8000/api/chat/',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({'message': 'hello', 'session_id': 'test'}).encode()
)

try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Error code:", e.code)
    print("Error body:", e.read().decode())
