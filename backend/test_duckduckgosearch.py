import requests

query = "What is the capital of France"

response = requests.get(
    "https://api.duckduckgo.com/",
    params={
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1
    },
    headers={"User-Agent": "Mozilla/5.0"}
)

print("Status Code:", response.status_code)
print("Response Content:", response.text)
