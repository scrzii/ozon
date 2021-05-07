import configparser
import math
from time import time

from selenium.webdriver.chrome.options import Options

from tgBot import TelegramBotCreator, MessageHandlerAbs, Options as BotOptions
from universalSeleniumParser.scheduler import SeleniumScheduler


class BotMessagesHandler(MessageHandlerAbs):
    @staticmethod
    def handle(user, update, bot_obj):
        if time() - user.data["last"] >= 86400:
            user.data["last"] = time()
            user.data["requests"] = bot_obj.data["pd"]

        user.need_update = True

        text = user.get().split(" ")
        if len(text) < 2 or not text[0].isnumeric():
            user.send("Неверный формат. Попробуйте еще раз. Например:\n1234567 Спальный мешок")
            return

        if user.data["process"]:
            user.send("Подождите, ваш прошлый запрос еще обрабатывается")
            return

        if user.data["requests"] == 0:
            user.send("На сегодня у вас не осталось запросов. " +
                      f"До пополнения: {math.ceil((86400 - int(time() + user.data['last'])) / 3600)} часов")
            return

        user.data["requests"] -= 1
        user.data["process"] = True
        bot_obj.parser.scheduler.add(user_id=user.id, parse_type=text[0], words=" ".join(text[1:]))
        user.send(f"Запрос отправлен. Дождись результата. Запросов осталось на сегодня: {user.data['requests']}")

    @staticmethod
    def new_user(user, bot_obj):
        user.data["requests"] = bot_obj.data["pd"]
        user.data["process"] = False
        user.data["last"] = time()
        user.need_update = True
        user.send("Привет, введи запрос в формате: <артикул_товара> <запрос>. Например:\n1234567 Спальный мешок\n" +
                  f"На сегодня у тебя есть еще {user.data['requests']} запросов.")


class Parser:
    def __init__(self, bot, windows_os):
        options = Options()
        options.add_argument("--no-sandbox")
        if not windows_os:
            pass

        options.add_experimental_option("prefs", {"profile.default_content_setting_values": {"images": 2}})
        self.bot = bot
        self.scheduler = SeleniumScheduler(self.__handler, options, windows_os)

    @staticmethod
    def get_article(product):
        a = product.find_elements_by_tag_name("a")
        try:
            href = a[0].get_attribute("href")
            print(href.split("/?")[0].split("-")[-1])
            return int(href.split("/?")[0].split("-")[-1])
        except:
            return 0

    def __handler(self, wd, user_id, parse_type, **data):
        article = parse_type
        request = data["words"].replace('"', "'")
        user_id = str(user_id)

        if user_id not in self.bot.get_users():
            self.bot.load_user(user_id)
        user = self.bot.get_users()[user_id]
        user.need_update = True

        page = 1
        while True:
            wd.get(f"https://www.ozon.ru/search/?from_global=true&text={request}&page={page}")
            products = wd.find_elements_by_css_selector("[class='a0c4']")
            if not products:
                user.data["process"] = False
                user.send(f"Товар {article} не найден по запросу {request}")
                return

            for index, product in enumerate(products):
                if int(self.get_article(product)) == int(article):
                    user.data["process"] = False
                    user.send(f"Продукт {article} найден на странице {page}. Позиция товара: {index}\n" +
                              f"{self.bot.data['end_text']}")
                    return

            page += 1

    def stop(self):
        self.scheduler.stop()


def main():
    config = configparser.ConfigParser()
    config.read("./config.ini")
    config = config["DEFAULT"]

    windows_os = int(config["windows_os"])
    access_token = config["access_token"]

    end_text_path = config["end_text_path"]
    text_file = open(end_text_path, "r")
    end_text = text_file.read()
    text_file.close()

    options = BotOptions()
    options.serializer_path = "./serialized_data"

    bot = TelegramBotCreator(access_token, BotMessagesHandler, options)
    bot.parser = Parser(bot, windows_os)
    bot.data["end_text"] = end_text
    bot.data["pd"] = int(config["requests_per_day"])

    bot.mainloop()
    bot.parser.stop()


if __name__ == "__main__":
    main()
