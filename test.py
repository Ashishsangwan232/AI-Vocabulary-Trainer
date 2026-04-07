import requests

url = "http://127.0.0.1:5000/get_word"

data = {
    "accuracy": 0.7,
    "avg_time": 4,
    "attempts": 2,
    "streak": 3
}

response = requests.post(url, json=data)

print(response.json())