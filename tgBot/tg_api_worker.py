import requests
import json
import time


class Keyboard:
    """
    Abstract parent class for telegram keyboards realizes
    """
    class Button:  # Parent subclass for keyboard buttons
        def to_dict_object(self) -> dict:  # Override me
            pass

    class NewLine(Button):  # Class for keyboard key lines separating
        pass

    def __init__(self, button_list: list):  # This method must be overridden
        self.keyboard_data = []  # Button container
        self.keyboard_type = ""  # <---- THIS PARAMETER MUST BE IN OVERRIDE
        if button_list:  # Button list class constructor
            for button in button_list:
                self.add_button(button)

    def add_button(self, button: Button):  # This method must be overridden
        """
        This methods adds new button to your keyboard
        """
        self.keyboard_data.append(button)

    def __str__(self) -> str:  # This method needs to be overridden
        """
        This method converts Keyboard-object to string for using like telegram
        API parameter in methods requests (send_message for example)
        :return: result of converting
        """
        result_object = {self.keyboard_type: [[]]}
        button_list = result_object[self.keyboard_type]
        for button in self.keyboard_data:
            if button == self.NewLine:
                button_list.append([])  # Adding new line in keyboard
            else:
                button_str = button.to_dict_object()
                button_list[-1].append(button_str)
        return json.dumps(result_object)


class InlineKeyboard(Keyboard):
    """
    Inline keyboard (look at tg api documentation). Buttons under message
    """
    class InlineButton(Keyboard.Button):
        def __init__(self, text: str, callback_data: str):
            self.text = text
            self.callback_data = callback_data

        def to_dict_object(self):
            return {
                "text": self.text,
                "callback_data": self.callback_data
            }

    @staticmethod
    def make_inline_list(button_list: list) -> list:
        """
        This method convert user's list to keyboard object list
        :param button_list: list of str(button text)
        :return: list of Button objects
        """
        result_list = []
        for button in button_list:
            result_list.append(InlineKeyboard.InlineButton(*button))
        return result_list

    def __init__(self, button_list: list):
        super().__init__(button_list)
        self.keyboard_type = "inline_keyboard"


class ReplyKeyboard(Keyboard):
    """
    Reply keyboard (look at tg api documentation). Buttons under chat
    """
    class ReplyButton(Keyboard.Button):
        def __init__(self, text: str):
            self.text = text

        def to_dict_object(self):
            return {
                "text": self.text
            }

    @staticmethod
    def make_reply_list(button_list: list) -> list:
        """
        This method convert user's list to keyboard object list
        :param button_list: list of tuple(button text, button callback)
        :return: list of Button objects
        """
        result_list = []
        for button in button_list:
            result_list.append(ReplyKeyboard.ReplyButton(button))
        return result_list

    def __init__(self, button_list: list):
        super().__init__(button_list)
        self.keyboard_type = "keyboard"


class RemoveReplyKeyboard(Keyboard):
    def __init__(self):
        pass

    def __str__(self):
        return '{"remove_keyboard": true}'


class Downloader:
    """
    Class for downloading telegram files
    """
    def __init__(self, api_object):
        """
        Initializer of Downloader class
        :param bot_token: access token of your bot or API class object
        """
        self.access_token = api_object.access_token
        self.downloading_url = f"https://api.telegram.org/file/bot{self.access_token}/"

    def download(self, tg_file_path: str, filename: str, local_file_path: str="./"):
        file_url = self.downloading_url + tg_file_path  # URL for this file
        file_data = requests.get(url=file_url).content  # File content for saving
        if not local_file_path.endswith("/"):
            local_file_path += "/"
        file = open(local_file_path + filename, "wb")
        file.write(file_data)  # Writing content to file
        file.close()


class API:
    """
    Class for working with telegram bots API.
    You can add new telegram methods.
    """
    def __init__(self, access_token: str):
        self.access_token = access_token  # Access token of your bot
        self.api_url = f"https://api.telegram.org/bot{access_token}/"  # Common api url for all methods

    def api_request(self, method: str, request_data: dict) -> dict:
        """
        Abstract method for api requests
        :param method: name of telegram method
        :param request_data: variables for this method
        :return: result of api request
        """
        response = json.loads(requests.get(
            url=self.api_url + method,
            params=request_data).text
        )  # Response deserialization
        return response

    # Next methods is translating telegram methods to class methods
    # explicit parameters are used for convenience
    # kwargs parameters for other parameters
    # Methods return result of requests

    def get_updates(self, **kwargs) -> dict:
        return self.api_request(
            "getUpdates",
            kwargs
        )

    def send_message(self, **kwargs):
        return self.api_request(
            "sendMessage",
            kwargs
        )

    def answer_callback_query(self, **kwargs):
        return self.api_request(
            "answerCallbackQuery",
            kwargs
        )

    def copy_message(self, **kwargs):
        return self.api_request(
            "copyMessage",
            kwargs
        )

    def get_file(self, **kwargs):
        return self.api_request(
            "getFile",
            kwargs
        )

    def answer_pre_checkout_query(self, **kwargs):
        return self.api_request(
            "answerPreCheckoutQuery",
            kwargs
        )

    def send_invoice(self, **kwargs):
        return self.api_request(
            "sendInvoice",
            kwargs
        )


# Demonstration
def main():
    token = "ACCESS_TOKEN"
    tg = API(token)
    offset = 0
    inline = InlineKeyboard(InlineKeyboard.make_inline_list([("Click me", "clicked")]))
    reply = ReplyKeyboard(ReplyKeyboard.make_reply_list(["Click me"]))
    while True:
        updates = tg.get_updates(offset=offset)["result"]
        for update in updates:
            offset = int(update["update_id"]) + 1
            message = update
            if "callback_query" in update:
                kbd = reply
                message = message["callback_query"]
            else:
                kbd = inline
            chat_id = message["message"]["chat"]["id"]
            data = {
                "chat_id": chat_id,
                "text": "Вы переключили клавиатуру",
                "reply_markup": str(kbd)
            }
            tg.send_message(**data)
        time.sleep(2)


if __name__ == "__main__":
    main()
