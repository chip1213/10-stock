import os
import smtplib
import yfinance as yf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── 設定 ──────────────────────────────────────────
STOCK_SYMBOL = "00631L.TW"
DROP_THRESHOLD = 0.05       # 5% 跌幅警示
LOOKBACK_DAYS = 3           # 跟幾天前比較

# 從 GitHub Secrets 讀取 Email 設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]
# ─────────────────────────────────────────────────


def get_price_data(symbol: str) -> dict:
    """抓取最近 10 天的收盤價，回傳今日現價與 N 天前收盤價"""
    ticker = yf.Ticker(symbol)

    # 現價（今日盤中）
    intraday = ticker.history(period="1d", interval="1m")
    if intraday.empty:
        raise ValueError(f"無法取得 {symbol} 的即時價格")
    current_price = float(intraday["Close"].iloc[-1])

    # 歷史收盤（抓 15 天保險）
    history = ticker.history(period="15d")
    if len(history) < LOOKBACK_DAYS + 1:
        raise ValueError(f"歷史資料不足，無法計算 {LOOKBACK_DAYS} 天前價格")

    # 取 N 天前的收盤價（index -N 代表倒數第N筆，不含今日盤中）
    base_price = float(history["Close"].iloc[-LOOKBACK_DAYS])
    base_date = history.index[-LOOKBACK_DAYS].strftime("%Y-%m-%d")

    return {
        "current_price": current_price,
        "base_price": base_price,
        "base_date": base_date,
    }


def send_alert_email(data: dict, drop_pct: float):
    subject = f"⚠️ 00631L 警示：{LOOKBACK_DAYS}天內跌幅 {drop_pct:.1f}%"
    body = f"""
    <h2>⚠️ 00631L（元大台灣50正2）跌幅警示</h2>
    <table border="1" cellpadding="8" style="border-collapse:collapse;">
        <tr><td><b>基準日期</b></td><td>{data['base_date']}（{LOOKBACK_DAYS}天前）</td></tr>
        <tr><td><b>基準收盤價</b></td><td>{data['base_price']:.2f} 元</td></tr>
        <tr><td><b>目前價格</b></td><td>{data['current_price']:.2f} 元</td></tr>
        <tr><td><b>{LOOKBACK_DAYS}天跌幅</b></td><td style="color:red;"><b>{drop_pct:.2f}%</b></td></tr>
        <tr><td><b>警示時間</b></td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
    </table>
    <p>請注意風險，審慎評估是否需要調整持倉。</p>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

    print(f"📧 警示 Email 已發送！{LOOKBACK_DAYS}天跌幅 {drop_pct:.2f}%")


def run():
    data = get_price_data(STOCK_SYMBOL)
    drop_pct = (data["base_price"] - data["current_price"]) / data["base_price"] * 100

    print(f"{LOOKBACK_DAYS}天前收盤: {data['base_price']:.2f} ({data['base_date']})")
    print(f"現價: {data['current_price']:.2f}")
    print(f"{LOOKBACK_DAYS}天跌幅: {drop_pct:.2f}%")

    if drop_pct >= DROP_THRESHOLD * 100:
        send_alert_email(data, drop_pct)
    else:
        print(f"✅ {LOOKBACK_DAYS}天跌幅未達 {DROP_THRESHOLD*100:.0f}%，無需警示")


if __name__ == "__main__":
    run()
