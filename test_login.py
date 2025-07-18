import requests
import json

url = 'http://localhost:8088/api/login'
headers = {'Content-Type': 'application/json'}
login_data = {'username': 'admin', 'password': 'admin'}

try:
    response = requests.post(url, headers=headers, data=json.dumps(login_data), timeout=5)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except Exception as e:
    print(f"请求失败: {str(e)}")