import time

from .tg_api_worker import Keyboard, ReplyKeyboard, InlineKeyboard, RemoveReplyKeyboard, Downloader, API
from .extensions import smet
from .tg_object_classes import Updater, User
from .bot_options import Options
from .serializer_class import Serializer, FileSerializer
from .message_handler_abs import MessageHandlerAbs, PostHandlerAbs


class TelegramBotCreator:
    def __init__(self, access_token: str, message_handler: type, options: Options=None):
        self.access_token = access_token
        self.message_handler = message_handler
        if not options:
            options = Options()
        self.options = options
        self.users = {}  # Don't store unnecessary users in RAM. Store them in updating process
        self.api = API(self.access_token)
        self.serializer = self.options.serializer_tool
        self.data = self.serializer.import_from("bot_data")

    def get_users(self):
        return self.users

    def load_user(self, user_id, user_source=None):
        if not user_source:
            user_source = {"id": str(user_id)}

        if user_id in self.users:  # User already in RAM
            return

        user_data = self.serializer.import_from(user_id)
        user = User(self.api, user_source, data=user_data)
        self.users[user_id] = user

    def update_user(self, user_id):
        if user_id in self.users:
            self.users[user_id].need_update = True

    def mainloop(self):
        time_started = time.time()
        api = self.api
        serializer = self.serializer
        offset = 0
        while True:
            current_time = time.time()
            timeout = self.options.timeout
            if timeout and current_time - time_started >= timeout:  # Checking timeout and breaking loop
                break

            response = api.get_updates(offset=offset)
            try:
                updates_raw = response["result"]  # Getting updates in dict format
            except KeyError:
                print(f"Update error: \n{response}")
                exit(1)
                return

            updates = list(map(Updater.auto_distribute, updates_raw))  # Getting updates in Update-class format
            for update in updates:
                if "from" in update.inner_source:  # We know who sent this update
                    # (updates in channels may be without sender)

                    # Handle if we know update's user only
                    user_source = update.inner_source["from"]
                    user_id = str(user_source["id"])
                    self.update_user(user_id)
                    new_user_flag = False

                    if user_id not in self.users:  # This member is not in RAM
                        if serializer.field_exists(user_id):  # User is in serialized data
                            self.load_user(user_id, user_source)
                        else:  # This is a new user
                            user = User(api, user_source)  # Creating new user
                            self.message_handler.new_user(user, self)  # New user event
                            new_user_flag = True
                            self.users[user_id] = user  # Adding new user to RAM

                    user = self.users[user_id]
                    if type(update) == Updater.Message:  # If type of update is message
                        user.update_text(update.text)  # Text of user's message

                    if not new_user_flag:
                        if type(update) == Updater.PreCheckoutQuery:
                            self.message_handler.pre_checkout(user, update, self)

                        elif type(update) == Updater.Payment:
                            self.message_handler.payment(user, update, self)

                        else:
                            self.message_handler.handle(user, update, self)
                        user.need_update = True
                else:
                    self.options.post_handler.handle(update, self)

                offset = int(update.update_id) + 1  # Updating offset for removing old updates (look at tg api)
            for user_id in self.users:
                user = self.users[user_id]
                if user.need_update:
                    serializer.export_to(user_id, user.data)
                    user.need_update = False

            self.serializer.export_to("bot_data", self.data)

            if self.options.loop_function:
                self.options.loop_function()
            time.sleep(self.options.check_interval)  # Wait before next check


def main():
    class MyMessageHandler(MessageHandlerAbs):
        @staticmethod
        def handle(user: User, update: Updater.Update, bot_obj: TelegramBotCreator):
            user.send(f"Вы написали: {user.current_message}. Ваш stage: {user.data['stage']}", RemoveReplyKeyboard())

        @staticmethod
        def new_user(user, bot_obj: TelegramBotCreator):
            user.data["stage"] = "default"

    access_token = "ACCESS_TOKEN"
    bot = TelegramBotCreator(access_token, MyMessageHandler)
    bot.mainloop()


if __name__ == "__main__":
    main()
