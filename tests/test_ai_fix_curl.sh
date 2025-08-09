#!/bin/bash

# 测试AI分类修复的curl脚本

BASE_URL="http://127.0.0.1:8000/api/v1"

echo "=== 登录获取token ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}')

echo "登录响应: $LOGIN_RESPONSE"

# 提取token
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'access_token' in data:
        print(data['access_token'])
    elif 'data' in data and 'access_token' in data['data']:
        print(data['data']['access_token'])
    else:
        print('TOKEN_NOT_FOUND')
except:
    print('PARSE_ERROR')
")

if [ "$TOKEN" = "TOKEN_NOT_FOUND" ] || [ "$TOKEN" = "PARSE_ERROR" ]; then
    echo "无法获取token，退出"
    exit 1
fi

echo "Token: $TOKEN"

echo ""
echo "=== 测试单个AI分类 (账单13330) ==="
curl -s -X POST "$BASE_URL/bills/13330/ai-classify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 完成 ==="