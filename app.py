from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
db = SQLAlchemy(app)

# 数据库模型
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=10000.0)

with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add(User(balance=10000.0))
        db.session.commit()

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

@app.route('/stock/<symbol>/history')
def get_history(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period='1mo')
    dates = hist.index.strftime('%m/%d').tolist()
    prices = round(hist['Close'], 2).tolist()
    return jsonify({'dates': dates, 'prices': prices})

@app.route('/portfolio')
def get_portfolio():
    user = User.query.first()
    holdings = Portfolio.query.all()
    return jsonify({
        'balance': round(user.balance, 2),
        'holdings': [{'symbol': h.symbol, 'shares': h.shares, 'avg_price': h.avg_price} for h in holdings]
    })

@app.route('/buy', methods=['POST'])
def buy():
    data = request.json
    symbol = data['symbol'].upper()
    shares = float(data['shares'])

    ticker = yf.Ticker(symbol)
    price = ticker.info.get('currentPrice')
    if not price:
        return jsonify({'error': '找不到股票价格'}), 400

    total = price * shares
    user = User.query.first()
    if user.balance < total:
        return jsonify({'error': '余额不足'}), 400

    user.balance -= total
    holding = Portfolio.query.filter_by(symbol=symbol).first()
    if holding:
        total_shares = holding.shares + shares
        holding.avg_price = (holding.avg_price * holding.shares + price * shares) / total_shares
        holding.shares = total_shares
    else:
        db.session.add(Portfolio(symbol=symbol, shares=shares, avg_price=price))

    db.session.commit()
    return jsonify({'message': f'成功买入 {shares} 股 {symbol}', 'balance': round(user.balance, 2)})

@app.route('/sell', methods=['POST'])
def sell():
    data = request.json
    symbol = data['symbol'].upper()
    shares = float(data['shares'])

    holding = Portfolio.query.filter_by(symbol=symbol).first()
    if not holding or holding.shares < shares:
        return jsonify({'error': '持仓不足'}), 400

    ticker = yf.Ticker(symbol)
    price = ticker.info.get('currentPrice')

    user = User.query.first()
    user.balance += price * shares
    holding.shares -= shares
    if holding.shares == 0:
        db.session.delete(holding)

    db.session.commit()
    return jsonify({'message': f'成功卖出 {shares} 股 {symbol}', 'balance': round(user.balance, 2)})

if __name__ == '__main__':
    app.run(debug=True)