import requests
headers = {"Authorization": f"Bearer {HK_API_KEY}", "Content-Type": "application/json"}
payload = {"input": "test"}
response = requests.post("https://your-hk-ai-api-endpoint.com/generate", json=payload, headers=headers)
print(response.json())
