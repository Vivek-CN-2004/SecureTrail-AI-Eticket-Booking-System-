import requests
try:
    r = requests.get("http://localhost:5000/login")
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(r.text)}")
    print(f"Snippet: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
