import os
import json
import smtplib
import yfinance as yf
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── 設定 ──────────────────────────────────────────
STOCK_SYMBOL = "00631L.TW"
DROP_THRESHOLD = 0.0       # 10% 跌幅警示
PRICE_CACHE_FILE = "prev_close.json"

# 從 GitHub Secrets 讀取 Email 設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.environ["EMAIL_SENDER"]     # 你的 Gmail
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"] # Gmail App Password
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"] # 收通知的信箱
# ─────────────────────────────────────────────────


def get_current_price(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        raise ValueError(f"無法取得 {symbol} 的即時價格")
    return float(data["Close"].iloc[-1])


def get_prev_close(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="2d")
    if len(data) < 2:
        raise ValueError(f"無法取得 {symbol} 的昨日收盤價")
    return float(data["Close"].iloc[-2])


def save_prev_close(price: float):
    with open(PRICE_CACHE_FILE, "w") as f:
        json.dump({"prev_close": price, "date": str(datetime.today().date())}, f)
    print(f"✅ 已儲存昨日收盤價: {price}")


def load_prev_close() -> float | None:
    if not os.path.exists(PRICE_CACHE_FILE):
        return None
    with open(PRICE_CACHE_FILE, "r") as f:
        data = json.load(f)
    return data.get("prev_close")


def send_alert_email(prev_close: float, current_price: float, drop_pct: float):
    subject = f"⚠️ 00631L 股價警示：跌幅 {drop_pct:.1f}%"
    body = f"""
    <h2>⚠️ 00631L（元大台灣50正2）跌幅警示</h2>
    <table border="1" cellpadding="8" style="border-collapse:collapse;">
        <tr><td><b>昨日收盤價</b></td><td>{prev_close:.2f} 元</td></tr>
        <tr><td><b>目前價格</b></td><td>{current_price:.2f} 元</td></tr>
        <tr><td><b>跌幅</b></td><td style="color:red;"><b>{drop_pct:.2f}%</b></td></tr>
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

    print(f"📧 警示 Email 已發送！跌幅 {drop_pct:.2f}%")


def run(mode: str):
    """
    mode = 'save'  → 09:00 執行，儲存昨日收盤價
    mode = 'check' → 10:30 執行，比較現價與昨收，必要時發 Email
    """
    if mode == "save":
        prev_close = get_prev_close(STOCK_SYMBOL)
        save_prev_close(prev_close)

    elif mode == "check":
        prev_close = load_prev_close()
        if prev_close is None:
            # 若沒有快取，直接從 yfinance 抓
            prev_close = get_prev_close(STOCK_SYMBOL)

        current_price = get_current_price(STOCK_SYMBOL)
        drop_pct = (prev_close - current_price) / prev_close * 100

        print(f"昨收: {prev_close:.2f} | 現價: {current_price:.2f} | 跌幅: {drop_pct:.2f}%")

        if drop_pct >= DROP_THRESHOLD * 100:
            send_alert_email(prev_close, current_price, drop_pct)
        else:
            print(f"✅ 跌幅未達 {DROP_THRESHOLD*100:.0f}%，無需警示")

    else:
        raise ValueError(f"未知 mode: {mode}，請使用 'save' 或 'check'")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    run(mode)
