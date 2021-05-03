import threading

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .serializer_class import FileSerializer


class SeleniumScheduler:
    def __init__(self, handler, options: Options=None, windows_os=0, cookies=[]):
        if options:  # Launching webdriver with/without options
            if windows_os:
                self.wd = webdriver.Chrome(options=options)
            else:
                self.wd = webdriver.Chrome("./chromedriver", options=options)
        else:
            if windows_os:
                self.wd = webdriver.Chrome()
            else:
                self.wd = webdriver.Chrome("./chromedriver")

        for cookie in cookies:
            self.wd.add_cookie(cookie)

        self.serializer = FileSerializer("./serialized_data/")
        self.queue = self.serializer.import_from("schedule")  # 2 priorities
        self.active = True  # Look at __del__
        self.handler = handler  # Main handler of requests
        self.changed = False  # Flag for serializer
        self.thread = threading.Thread(target=self.__mainloop)  # Handling queues of user's functions in single thread
        self.thread.start()  # Launching single thread

    def stop(self):
        self.active = False  # For closing webdriver. In __mainloop webdriver will close

    def __handle(self, queue: list):
        if queue:  # Queue is not empty -> handle first element
            args = queue[0]["args"]
            kwargs = queue[0]["kwargs"]
            self.handler(self.wd, *args, **kwargs)
            queue.pop(0)
            self.changed = True

    def __mainloop(self):
        while self.active:  # Working until __del__ is not called
            if self.changed:
                self.serializer.export_to("schedule", self.queue)
                self.changed = False

            que = []
            if self.queue["high"]:
                que = self.queue["high"]
            elif self.queue["low"]:
                que = self.queue["low"]
            self.__handle(que)

        self.wd.quit()  # Closing webdriver after main loop

    def add(self, priority: str="high", *args, **kwargs):  # Adding new handler in queue
        self.queue[priority].append({
            "args": args,
            "kwargs": kwargs
        })
        self.changed = True
