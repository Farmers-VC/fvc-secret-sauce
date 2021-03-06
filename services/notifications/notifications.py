import requests
from colored import fg, stylize
from twilio.rest import Client

from config import Config


class Notification:
    twilio_client = None

    def __init__(self, config: Config):
        # Find these values at https://twilio.com/user/account
        self.config = config
        self.phone_numbers = self.config.get("AGENT_PHONE_NUMBERS").split(",")
        self.twilio_client = Client(
            self.config.get("TWILIO_ACCOUNT_SID"), self.config.get("TWILIO_AUTH_TOKEN")
        )

    def send_twilio(self, message):
        if not self.config.kovan:
            for phone_number in self.phone_numbers:
                self.twilio_client.messages.create(
                    to=phone_number,
                    from_=self.config.get("TWILIO_FROM_NUMBER"),
                    body=message,
                )

    def send_slack_printing_tx(self, tx_hash_url: str, success: bool = False) -> None:
        slack_webhook = self.config.get("SLACK_PRINTING_TX_WEBHOOK")
        if success:
            message = f":money_with_wings::money_with_wings::money_with_wings:\nTransaction executed {tx_hash_url}"
            print(stylize(message, fg("green")))
        else:
            message = f":red_circle::red_circle::red_circle:\nTransaction was processed but failed {tx_hash_url}"
            print(stylize(message, fg("red")))
        requests.post(
            slack_webhook,
            json={"text": message},
        )

    def send_slack_arbitrage(self, message):
        # print(stylize(message, fg("light_blue")))
        slack_webhook = self.config.get("SLACK_ARBITRAGE_OPPORTUNITIES_WEBHOOK")
        requests.post(
            slack_webhook,
            json={"text": message},
        )

    def send_snipe_noobs(self, message):
        print(stylize(message, fg("light_blue")))
        slack_webhook = self.config.get("SLACK_SNIPE_WEBHOOK")
        requests.post(
            slack_webhook,
            json={"text": message},
        )

    def send_slack_errors(self, message):
        slack_webhook = self.config.get("SLACK_ERRORS_WEBHOOK")
        message = ":red_circle:\n" + message
        print(stylize(message, fg("red")))
        requests.post(
            slack_webhook,
            json={"text": message},
        )
