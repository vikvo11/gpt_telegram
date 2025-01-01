# gpt_telegram
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt


https://api.telegram.org/bot{token}/getUpdates

GET http://127.0.0.1:5005/api/costs/day?year=2025&month=01&day=05
GET http://127.0.0.1:5005/api/costs/month?year=2025&month=01
GET http://127.0.0.1:5005/api/costs/year?year=2025

curl -X GET \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     "http://localhost:5005/api/costs/month?year=2024&month=1"


curl -X POST \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     -H "Content-Type: application/json" \
     -d '{"year":"2024"}' \
     "http://localhost:5005/api/costs/year"

curl -X POST \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     -H "Content-Type: application/json" \
     -d '{"year":"2024","month":"01"}' \
     "http://localhost:5005/api/costs/month"


curl -X POST \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     -H "Content-Type: application/json" \
     -d '{"year":"2024","month":"01"}' \
     "http://localhost:5005/webhooks/"



### api limit
GET /limits

Возвращает все записи из limit_dict. Включая ту, у которой title = "общий"

curl -X GET \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     "http://localhost:5005/api/limits"


POST /limits
{
  "title": "Groceries",
  "limit_value": 5000
}

Добавить/изменить лимит (например, Groceries = 5000):
curl -X POST \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     -H "Content-Type: application/json" \
     -d '{"title":"Groceries","limit_value":5000}' \
     "http://localhost:5005/api/limits"

Изменить общий лимит (например, хотим поставить общий = 10000):
curl -X POST \
     -H "X-API-KEY: MY_SUPER_SECRET_KEY_123" \
     -H "Content-Type: application/json" \
     -d '{"title":"общий","limit_value":131907}' \
     "http://localhost:5005/api/limits"
