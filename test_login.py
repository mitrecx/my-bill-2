import requests
import json

# 测试登录接口
url = "http://127.0.0.1:8000/api/v1/auth/login"
data = {
    "username": "testuser",
    "password": "password123"
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"Response Body: {response.text}")

if response.status_code == 200:
    try:
        json_response = response.json()
        print(f"JSON Response: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")