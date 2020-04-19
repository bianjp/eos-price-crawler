#!/usr/bin/env python3
import time
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
import csv
import os.path

from price_loader import PriceLoader
from log import logger


class App:
    CSV_FILE = os.path.join(os.path.dirname(__file__), 'data', 'eos.csv')
    CSV_HEADER = ['Time', 'CoinMarketCap', 'Bitfinex', 'Average', 'OTCBTC']

    # 关注的价格
    # 第一行为超出时需要发出提示的价格区间
    # 第二行为超出时需要额外关注变化（提高查询频率）的价格区间
    CONCERNED_PRICES_FILE = '/tmp/eos-concerned-prices'
    DEFAULT_CONCERNED_PRICES_FILE_CONTENT = '50 100\n52 98'

    def __init__(self):
        self.executor = ThreadPoolExecutor(20)
        # 查询频率。单位：秒
        self.query_interval = 10

        # 不关注的价格区间
        # OTCBTC 价格在此区间时，使用较大的查询间隔；超出此区间时，使用较小的查询间隔
        self.concerned_prices = (50, 100)
        self.concerned_prices_file_mtime = 0
        self.init_concerned_prices()

        os.makedirs(os.path.dirname(self.CSV_FILE), 0o755, True)

        # gnome shell extension 中使用
        # os.path.exists 对 broken symbolic link 也返回 false, 因此不能检查是否存在再删除
        try:
            os.remove('/tmp/eos-price.csv')
        except FileNotFoundError:
            pass
        os.symlink(os.path.abspath(self.CSV_FILE), '/tmp/eos-price.csv')

        # 初始化汇率
        PriceLoader.coinmarketcap()

        file_exists = os.path.exists(self.CSV_FILE)
        self.csv_file = open(self.CSV_FILE, 'a')
        self.writer = csv.DictWriter(self.csv_file, __class__.CSV_HEADER)
        if not file_exists:
            self.writer.writeheader()

    def init_concerned_prices(self):
        if not os.path.exists(self.CONCERNED_PRICES_FILE):
            with open(self.CONCERNED_PRICES_FILE, 'w') as f:
                f.write(self.DEFAULT_CONCERNED_PRICES_FILE_CONTENT)
        self.update_concerned_prices()

    def update_concerned_prices(self):
        if not os.path.exists(self.CONCERNED_PRICES_FILE):
            return
        mtime = os.path.getmtime(self.CONCERNED_PRICES_FILE)
        if mtime == self.concerned_prices_file_mtime:
            return

        with open(self.CONCERNED_PRICES_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                line = content.split('\n')[1].strip()
                prices = [float(i) for i in line.split(' ')]
                self.concerned_prices = (prices[0], prices[1])
                self.concerned_prices_file_mtime = mtime

    def append_row(self, data: dict):
        self.writer.writerow(data)
        self.csv_file.flush()

    def get_task_result(self, task: Future, id: str):
        # noinspection PyBroadException
        try:
            return task.result(5)
        except TimeoutError:
            logger.error('[%s] Timeout', id)
        except Exception:
            logger.exception('[%s] Exception', id)

    def sleep(self):
        t = 0.1 + (60 - time.localtime().tm_sec - time.time() % 1) % self.query_interval
        time.sleep(t)

    def start(self):
        while True:
            self.sleep()

            start_time = time.strftime('%Y-%m-%d %H:%M:%S')
            coinmarketcap_task = self.executor.submit(PriceLoader.coinmarketcap)
            bitfinex_task = self.executor.submit(PriceLoader.bitfinex)
            otcbtc_task = self.executor.submit(PriceLoader.otcbtc)

            coinmarketcap_price = self.get_task_result(coinmarketcap_task, 'coinmarketcap')
            bitfinex_price = self.get_task_result(bitfinex_task, 'bitfinex')
            otcbtc_price = self.get_task_result(otcbtc_task, 'otcbtc')

            if coinmarketcap_price and bitfinex_price:
                average_price = round((coinmarketcap_price + bitfinex_price) / 2, 2)
            else:
                average_price = None

            self.append_row({
                'Time': start_time,
                'CoinMarketCap': coinmarketcap_price,
                'Bitfinex': bitfinex_price,
                'Average': average_price,
                'OTCBTC': otcbtc_price,
            })

            self.update_concerned_prices()
            if otcbtc_price:
                if self.concerned_prices[0] < otcbtc_price < self.concerned_prices[1]:
                    self.query_interval = 60
                else:
                    self.query_interval = 10


def main():
    app = App()
    app.start()


if __name__ == '__main__':
    main()
