import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
import requests
import threading
import random
import time
import logging
from fake_useragent import UserAgent
import platform
import os

# if platform.system() == 'Windows':
#     os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# from kivy import Config
# Config.set('graphics', 'multisamples', '0')

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StressTestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.url_input = TextInput(
            multiline=False,
            hint_text='Введите URL для тестирования (https://example.com)'
        )
        layout.add_widget(self.url_input)

        settings_layout = BoxLayout(orientation='horizontal', spacing=10)

        self.threads_input = TextInput(
            multiline=False,
            hint_text='Количество потоков (1-100)',
            text='10'
        )
        settings_layout.add_widget(self.threads_input)

        self.delay_input = TextInput(
            multiline=False,
            hint_text='Задержка (сек)',
            text='0.1'
        )
        settings_layout.add_widget(self.delay_input)

        layout.add_widget(settings_layout)

        self.method_spinner = Spinner(
            text='GET',
            values=('GET', 'POST', 'HEAD'),
            size_hint=(None, None),
            size=(100, 44),
            pos_hint={'center_x': .5, 'center_y': .5})
        layout.add_widget(self.method_spinner)

        control_layout = BoxLayout(orientation='horizontal', spacing=10)

        self.start_button = Button(text='Начать тест')
        self.start_button.bind(on_press=self.start_test)
        control_layout.add_widget(self.start_button)

        self.stop_button = Button(text='Остановить', disabled=True)
        self.stop_button.bind(on_press=self.stop_test)
        control_layout.add_widget(self.stop_button)

        layout.add_widget(control_layout)

        self.stats_label = Label(text='Статистика: 0 запросов')
        layout.add_widget(self.stats_label)

        return layout

    def make_request(self, url, method):
        try:
            ua = UserAgent()
            headers = {
                'User-Agent': ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }

            params = {
                '_': str(time.time()),
                'rand': str(random.random())
            }

            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=5)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=params, timeout=5)
            elif method == 'HEAD':
                response = requests.head(url, headers=headers, params=params, timeout=5)

            return response.status_code

        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    def test_thread(self, url, method, delay):
        while self.is_testing:
            status = self.make_request(url, method)
            if status:
                self.requests_count += 1
                self.stats_label.text = f'Статистика: {self.requests_count} запросов'
            time.sleep(float(delay))

    def start_test(self, instance):
        url = self.url_input.text
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            threads_count = int(self.threads_input.text)
            delay = float(self.delay_input.text)

            if threads_count < 1 or threads_count > 100:
                logger.error("Некорректное количество потоков")
                return

        except ValueError:
            logger.error("Некорректные параметры")
            return

        self.is_testing = True
        self.requests_count = 0
        self.start_button.disabled = True
        self.stop_button.disabled = False

        self.threads = []
        for _ in range(threads_count):
            thread = threading.Thread(
                target=self.test_thread,
                args=(url, self.method_spinner.text, delay)
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

        logger.info(f"Тест запущен: {url}, {threads_count} потоков")

    def stop_test(self, instance):
        self.is_testing = False
        self.start_button.disabled = False
        self.stop_button.disabled = True
        logger.info("Тест остановлен")


if __name__ == '__main__':
    StressTestApp().run()
