from flask import Flask, render_template, request, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/stock/<symbol>')
def get_stock(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return jsonify({
        'name': info.get('longName', symbol),
        'price': info.get('currentPrice', 'N/A'),
        'change': info.get('regularMarketChangePercent', 'N/A'),
        'high': info.get('dayHigh', 'N/A'),
        'low': info.get('dayLow', 'N/A'),
    })

if __name__ == '__main__':
    app.run(debug=True)