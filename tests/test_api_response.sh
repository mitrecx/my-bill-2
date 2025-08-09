#!/bin/bash

# 获取token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")

echo "Token: $TOKEN"

# 测试创建分类规则
echo "Testing create classification rule..."
curl -X POST "http://localhost:8000/api/v1/classification-rules/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rule_text":"curl测试规则_'$(date +%s)'","source_type":"all","target_category":"交通出行","priority":1,"is_active":true}' | \
  python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"