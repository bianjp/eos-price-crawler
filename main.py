#!/usr/bin/env python3
import time
from concurrent.futures import ThreadPoolExecutor
import csv
import os.path

from price_loader import PriceLoader


class App:
    CSV_FILE = os.path.join(os.path.dirname(__file__), 'data', 'eos.csv')
    CSV_HEADER = ['Time', 'CoinMarketCap', 'Bitfinex', 'Average', 'OTCBTC']

    def __init__(self):
        self.executor = ThreadPoolExecutor(20)

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

    def append_row(self, data: dict):
        self.writer.writerow(data)
        self.csv_file.flush()

    def start(self):
        while True:
            # Run every 20s
            time.sleep(((60 - time.localtime().tm_sec - time.time() % 1) % 20 or 20) + 0.1)

            start_time = time.strftime('%Y-%m-%d %H:%M:%S')
            coinmarketcap_task = self.executor.submit(PriceLoader.coinmarketcap)
            bitfinex_task = self.executor.submit(PriceLoader.bitfinex)
            otcbtc_task = self.executor.submit(PriceLoader.otcbtc)

            coinmarketcap_price = coinmarketcap_task.result()
            bitfinex_price = bitfinex_task.result()
            otcbtc_price = otcbtc_task.result()

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


def main():
    app = App()
    app.start()


if __name__ == '__main__':
    main()
