import os
import requests

class Line:
    def __init__(self, msg):
        url = "https://notify-api.line.me/api/notify"
        payload = f"message={msg}"
        headers = {
            'Authorization': f"Bearer {os.getenv('API_LINE_NOTIFICATION')}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # BugDWScwhYvjVc5EyRi5sa28LmJxE2G5NIJsrs6vEV7
        print(payload.encode('utf-8'))
        print(payload)
        response = requests.request(
            "POST", url, headers=headers, data=payload.encode('utf-8'))

        print(f"line status => {response}")
        if response.status_code == 200:
            return True

        return False