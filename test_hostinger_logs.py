import requests
from dotenv import load_dotenv



api_token = "R1N0xSauE0aj6GSf875F3lKPzjLA38R0rIF4wWeu6336c0f5"
order_id = "ORe4e47baf663988c4a2a5789e43d9"

url = (
    f"https://developers.hostinger.com"
    f"/api/mail/v1/orders/{order_id}/logs/outbound"
)

headers = {
    "Authorization": f"Bearer {api_token}",
    "Accept": "application/json",
}

params = {
    "page": 1,
    "per_page": 10,
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30,
)

print("STATUS:", response.status_code)
print()

try:
    data = response.json()
    print(data)
except Exception:
    print(response.text)
    
    
