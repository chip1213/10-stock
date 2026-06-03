# 00631L 股價跌幅警示

當元大台灣50正2（00631L）盤中跌幅超過 **10%** 時，自動發送 Email 通知。

## 執行邏輯

| 時間（台灣）| 動作 |
|---|---|
| 09:00（週一至週五）| 抓取昨日收盤價並儲存 |
| 10:30（週一至週五）| 抓取當前價格，若跌幅 ≥ 10% 則發送警示 Email |

---

## 設定步驟

### 1. Fork 或 Clone 這個 Repo

### 2. 設定 Gmail App Password

1. 前往 [Google 帳戶安全性](https://myaccount.google.com/security)
2. 開啟兩步驟驗證
3. 搜尋「應用程式密碼」，產生一組 16 位密碼
4. 記下這組密碼（只顯示一次）

### 3. 在 GitHub 設定 Secrets

前往你的 Repo → **Settings → Secrets and variables → Actions → New repository secret**

新增以下三個 Secrets：

| Secret 名稱 | 內容 |
|---|---|
| `EMAIL_SENDER` | 你的 Gmail 地址（例：`yourname@gmail.com`）|
| `EMAIL_PASSWORD` | 上一步產生的 Gmail App Password |
| `EMAIL_RECEIVER` | 要收到通知的 Email 地址 |

### 4. 啟用 GitHub Actions

前往 Repo 的 **Actions** 頁籤，確認 Workflow 已啟用。

---

## 手動測試

在 Actions 頁籤選擇 **00631L 股價監控** → **Run workflow**，選擇模式：
- `save`：測試儲存昨日收盤價
- `check`：測試比較現價與發送邏輯

---

## 注意事項

- GitHub Actions 的 cron 時間為 **UTC**，台灣時間 = UTC + 8
- Free tier 每月有 2,000 分鐘限制，此專案每月約使用 40 分鐘，完全足夠
- 若台股休市（例如假日），yfinance 可能回傳空資料，程式會自動略過
