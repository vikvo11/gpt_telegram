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
     "http://localhost:5005/webhooks"