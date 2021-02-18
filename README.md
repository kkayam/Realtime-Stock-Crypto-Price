# Desktop stock/crypto price
Get live update for any group of stocks.

- Always on top
- Drag to move
- Scroll wheel to change opacity
- Edit background and tickers in config.txt
- Import any gif background using url or from resources folder
- Uses finnhub websocket for price updates

## Config File Format
First line is always for background, paste in the url or path after background=.

1 Ticker per line.

E.g. for bitcoin to USDT at binance:

BINANCE:BTCUSDT

You can find the specific tickers by opening up the crypto on binance

For normal stocks, e.g. Gamestop:

GME

If you want to see profits, write in this format for the stocks/cryptos you are interested in seeing the profit for:

(exchange:)ticker:amount@price

![example](resources/pic.png)
