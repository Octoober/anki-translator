import requests


class AnkiClient:
    def __init__(self, anki_connect_url: str):
        self.anki_connect_url = anki_connect_url

    def invoke(self, action: str, **params):
        """Отправляет запрос к Anki Connect API"""
        payload = {
            "action": action,
            "params": params,
            "version": 6,  # Версия Anki Connect. Я не уверен, нужно ли ее прописывать, но пусть будет.
        }
        response = requests.post(self.anki_connect_url, json=payload, timeout=10)

        response.raise_for_status()

        json_data = response.json()

        if json_data.get("error"):
            raise Exception(f"Anki Error: {json_data['error']}")

        return json_data.get("result")
