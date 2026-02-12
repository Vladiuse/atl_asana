import requests

from .models import BotMessageLog, BotMessageLogStatus


class TelegramSenderService:
    def __init__(self, telegram_token: str):
        self.token = telegram_token
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, recipient_id: str, text: str) -> BotMessageLog:
        log = BotMessageLog.objects.create(recipient_id=recipient_id, text=text)
        payload = {"chat_id": recipient_id, "text": text, "parse_mode": "HTML"}
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            if response.ok:
                log.status = BotMessageLogStatus.SUCCESS
            else:
                log.status = BotMessageLogStatus.ERROR
                log.error_text = str(response.text)
        except requests.exceptions.RequestException as e:
            log.status = BotMessageLogStatus.ERROR
            log.error_text = str(e)
        log.save()
        return log
