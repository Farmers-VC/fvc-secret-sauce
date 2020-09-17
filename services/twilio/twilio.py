import os

from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
AGENT_PHONE_NUMBERS = os.environ.get('AGENT_PHONE_NUMBERS')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')


class TwilioService:
    client = None

    def __init__(self):
        # Find these values at https://twilio.com/user/account
        account_sid = TWILIO_ACCOUNT_SID
        auth_token = TWILIO_AUTH_TOKEN
        self.phone_numbers = AGENT_PHONE_NUMBERS.split(',')
        self.client = Client(account_sid, auth_token)

    def send_message(self, message):
        for phone_number in self.phone_numbers:
            self.client.messages.create(to=phone_number, from_=TWILIO_FROM_NUMBER, body=message)
