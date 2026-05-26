let chart = null;
let currentSymbol = null;

async function searchStock() {
    const symbol = document.getElementById('symbolInput').value.toUpperCase();
    if (!symbol) return;
    currentSymbol = symbol;

    const response = await fetch(`/stock/${symbol}`);
    const data = await response.json();

    document.getElementById('stockName').textContent = data.name;
    document.getElementById('stockPrice').textContent = `$${data.price}`;

    const changeEl = document.getElementById('stockChange');
    const change = data.change.toFixed(2);
    changeEl.textContent = `${change > 0 ? '▲' : '▼'} ${Math.abs(change)}%`;
    changeEl.className = `stock-change ${change > 0 ? 'positive' : 'negative'}`;

    document.getElementById('stockHigh').textContent = `$${data.high}`;
    document.getElementById('stockLow').textContent = `$${data.low}`;
    document.getElementById('stockCard').style.display = 'block';
    document.getElementById('tradeMessage').textContent = '';

    const histRes = await fetch(`/stock/${symbol}/history`);
    const histData = await histRes.json();
    renderChart(histData.dates, histData.prices);
}

function renderChart(dates, prices) {
    if (chart) chart.destroy();
    const ctx = document.getElementById('priceChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '收盘价',
                data: prices,
                borderColor: '#00d4aa',
                backgroundColor: 'rgba(0, 212, 170, 0.1)',
                borderWidth: 2,
                pointRadius: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#fff' } } },
            scales: {
                x: { ticks: { color: '#aaa' }, grid: { color: '#333' } },
                y: { ticks: { color: '#aaa' }, grid: { color: '#333' } }
            }
        }
    });
}

async function tradeStock(action) {
    if (!currentSymbol) return;
    const shares = document.getElementById('sharesInput').value;

    const response = await fetch(`/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: currentSymbol, shares: shares })
    });

    const data = await response.json();
    const msgEl = document.getElementById('tradeMessage');

    if (data.error) {
        msgEl.style.color = '#ff6b6b';
        msgEl.textContent = `❌ ${data.error}`;
    } else {
        msgEl.style.color = '#00d4aa';
        msgEl.textContent = `✅ ${data.message}`;
        document.getElementById('balance').textContent = `$${data.balance.toLocaleString()}`;
        loadPortfolio();
    }
}

async function loadPortfolio() {
    const res = await fetch('/portfolio');
    const data = await res.json();

    document.getElementById('balance').textContent = `$${data.balance.toLocaleString()}`;

    const list = document.getElementById('holdingsList');
    if (data.holdings.length === 0) {
        list.innerHTML = '<p style="color:#aaa">暂无持仓</p>';
        return;
    }

    list.innerHTML = data.holdings.map(h => `
        <div class="holding-row">
            <span><strong>${h.symbol}</strong></span>
            <span>${h.shares} 股</span>
            <span>均价 $${h.avg_price.toFixed(2)}</span>
        </div>
    `).join('');

    document.getElementById('holdingsCard').style.display = 'block';
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('symbolInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchStock();
    });
    loadPortfolio();
});