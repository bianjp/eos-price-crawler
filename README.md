# EOS 价格爬虫

从以下数据源抓取 EOS 价格，保存在 csv 文件中：

* [CoinMarketCap](https://coinmarketcap.com/api/): 数据每 5 分钟更新一次
* [Bitfinex](https://docs.bitfinex.com/v1/reference#rest-public-ticker)
* [OTCBTC](https://otcbtc.com/sell_offers?currency=eos&fiat_currency=cny&payment_type=all): 取出售广告中的最低单价（忽略订单最大限额小于 500 的广告）

对 CoinMarketCap 与 Bitfinex 的价格会计算平均值，OTCBTC 网站显示的当前 EOS 市价即为这个平均值。

可通过 Gnome Shell Extension 读取 csv 文件，将 EOS 实时价格显示在系统状态栏。

也可在命令行监视 csv 文件变化：

```bash
tail -f data/eos.csv | tr ',' '\t'
```

## 爬虫

### 依赖

* Python 3
* Python packages: requests

### 安装

安装 Python 依赖：

```bash
sudo pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

## Gnome Shell Extension

1. 安装：
    ```bash
    ln -sf $(readlink -e gnome-shell-extension) ~/.local/share/gnome-shell/extensions/eos-live-price@bianjp.com
    ```
2. 重启 Gnome Shell: Alt + F2, 输入 "r", 回车
3. 启用：`gnome-shell-extension-tool -e eos-live-price@bianjp.com`。也可通过 Gnome Tweak Tool 或 https://extensions.gnome.org/local/ 启用扩展。

平均价格有明显上涨/下跌，或 OTCBTC 最低售价低于或超过特定值时会有气泡提示。可按需修改检测逻辑。

每次修改扩展的代码后需要重启 Gnome Shell 才会生效。
