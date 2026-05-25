import requests
try:
    response = requests.get("https://mermaid.ink", timeout=5)
    print(f"API 可访问，状态码：{response.status_code}")
except Exception as e:
    print(f"网络连接问题：{e}")
