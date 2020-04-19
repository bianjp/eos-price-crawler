import requests
import time
from typing import Optional
import re
import random

from log import logger


class PriceLoader:
    # 美元-人民币汇率
    usd_exchange_rate = 6.40
    request_timeout = 5

    user_agents = [
        'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:58.0) Gecko/20100101 Firefox/58.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13) AppleWebKit/605.1.4 (KHTML, like Gecko) Version/11.1 Safari/605.1.4',
    ]

    @staticmethod
    def random_user_agent():
        return __class__.user_agents[random.randint(0, len(__class__.user_agents) - 1)]

    @staticmethod
    # https://coinmarketcap.com/api/
    # 请求频率限制：10/min
    def coinmarketcap() -> Optional[float]:
        start_time = time.time()
        # noinspection PyBroadException
        try:
            # CoinMarketCap 数据源 5 分钟更新一次
            res = requests.get('https://api.coinmarketcap.com/v1/ticker/eos/?convert=CNY',
                               timeout=__class__.request_timeout)
            if res.status_code != 200:
                logger.error('[coinmarketcap] Request failed: status_code=%s, reason=%s, content=%s',
                             res.status_code, res.reason, repr(res.text))
                return
            logger.debug('[coinmarketcap] Response: %s', res.text)
            result = res.json()[0]
            price_usd = float(result['price_usd'])
            price_cny = float(result['price_cny'])
            exchange_rate = price_cny / price_usd
            if 5 < exchange_rate < 10:
                __class__.usd_exchange_rate = exchange_rate
            return round(price_cny, 2)
        except Exception:
            logger.exception('[coinmarketcap] Failed')
        finally:
            time_spent = (time.time() - start_time) * 1000
            logger.debug('[coinmarketcap] Time spent: %fms', time_spent)

    @staticmethod
    # https://coinmarketcap.com/currencies/eos/
    def coinmarketcap_html() -> Optional[float]:
        start_time = time.time()
        # noinspection PyBroadException
        try:
            res = requests.get('https://coinmarketcap.com/currencies/eos/',
                               timeout=__class__.request_timeout,
                               headers={'User-Agent': __class__.random_user_agent()})
            if res.status_code != 200:
                logger.error('[coinmarketcap] Request failed: status_code=%s, reason=%s, content=%s',
                             res.status_code, res.reason, repr(res.text))
                return

            match = re.search(r'data-currency-price data-usd="([\d.]+)"', res.text)
            if match:
                price_usd = float(match.group(1))
            else:
                logger.error('[coinmarketcap] No price found')
                return

            match = re.search(r'data-cny="([\d.]+)"', res.text)
            if match:
                __class__.exchange_rate = 1 / float(match.group(1))
            else:
                logger.error('[coinmarketcap] No CNY exchange rate found')
                return

            return round(price_usd * __class__.exchange_rate, 2)
        except Exception:
            logger.exception('[coinmarketcap] Failed')
        finally:
            time_spent = (time.time() - start_time) * 1000
            logger.debug('[coinmarketcap] Time spent: %fms', time_spent)

    @staticmethod
    # https://docs.bitfinex.com/v1/reference#rest-public-ticker
    # 请求频率限制：30/min
    def bitfinex() -> Optional[float]:
        start_time = time.time()
        # noinspection PyBroadException
        try:
            res = requests.get('https://api.bitfinex.com/v1/pubticker/eosusd', timeout=__class__.request_timeout)
            if res.status_code != 200:
                logger.error('[bitfinex] Request failed: status_code=%s, reason=%s, content=%s',
                             res.status_code, res.reason, repr(res.text))
            logger.debug('[bitfinex] Response: %s', res.text)
            result = res.json()
            return round(float(result['last_price']) * __class__.usd_exchange_rate, 2)
        except Exception:
            logger.exception('[bitfinex] Failed')
        finally:
            time_spent = (time.time() - start_time) * 1000
            logger.debug('[bitfinex] Time spent: %fms', time_spent)

    @staticmethod
    # https://otcbtc.com/sell_offers?currency=eos&fiat_currency=cny&payment_type=all
    def otcbtc() -> Optional[float]:
        start_time = time.time()
        # noinspection PyBroadException
        try:
            retry = 3
            res = None
            while retry > 0:
                res = requests.get('https://otcbtc.com/sell_offers?currency=eos&fiat_currency=cny&payment_type=all',
                                   timeout=__class__.request_timeout,
                                   headers={'User-Agent': __class__.random_user_agent()},
                                   cookies={'locale': 'zh-CN'})
                if res.status_code == 200:
                    break
                retry -= 1

            if res.status_code != 200:
                logger.error('[otcbtc] Request failed: status_code=%s, reason=%s, content=%s',
                             res.status_code, res.reason, repr(res.text))

            # 快速交易
            quick_text = res.text[
                         res.text.index('single-offer-table'):res.text.index('single-offer-container__load-more')]
            quick_prices = []
            for m in re.finditer(
                    r'<li class="single-offer-table-price">\s*([\d,.]+)\s*</li>.*?<li class="single-offer-table-total">\s*([\d,.]+)\s*</li>',
                    quick_text, re.DOTALL):
                if float(m[2].replace(',', '')) > 500:
                    quick_prices.append(float(m[1].replace(',', '')))
            quick_prices.sort()
            min_quick_price = len(quick_prices) > 0 and quick_prices[0] or None

            # 普通交易
            normal_content = res.text[res.text.index('long-solution-list'):res.text.index('pagination-sm')]
            min_normal_price = None
            for m in re.finditer(r'</span>\s*[\d,.]+\s*-\s*([\d,.]+)\s*<span.*?单价</span>\s*([\d,.]+)\s*<span',
                                 normal_content, re.DOTALL):
                max_amount = float(m[1].replace(',', ''))
                if max_amount > 500:
                    min_normal_price = float(m[2].replace(',', ''))
                    break

            return min_quick_price and min_normal_price and min(min_quick_price, min_normal_price) or None

        except Exception:
            logger.exception('[otcbtc] Failed')
        finally:
            time_spent = (time.time() - start_time) * 1000
            logger.debug('[otcbtc] Time spent: %fms', time_spent)
