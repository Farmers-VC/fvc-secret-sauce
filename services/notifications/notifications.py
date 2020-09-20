import os

import requests
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
AGENT_PHONE_NUMBERS = os.environ.get("AGENT_PHONE_NUMBERS")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
SLACK_WEBHOOK_URI = os.environ.get("SLACK_WEBHOOK_URI")
SLACK_WEBHOOK_URI_KOVAN = os.environ.get("SLACK_WEBHOOK_URI_KOVAN")


class Notification:
    twilio_client = None

    def __init__(self, kovan: bool = False):
        # Find these values at https://twilio.com/user/account
        self.phone_numbers = AGENT_PHONE_NUMBERS.split(",")
        self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.kovan = kovan

    def send_all_message(self, message):
        self.send_twilio(message)
        self.send_slack(message)

    def send_twilio(self, message):
        if not self.kovan:
            for phone_number in self.phone_numbers:
                self.twilio_client.messages.create(
                    to=phone_number, from_=TWILIO_FROM_NUMBER, body=message
                )

    def send_slack(self, message):
        slack_webhook = SLACK_WEBHOOK_URI_KOVAN if self.kovan else SLACK_WEBHOOK_URI

        requests.post(
            slack_webhook,
            json={"text": message},
        )