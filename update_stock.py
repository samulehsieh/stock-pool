import pandas as pd
from pathlib import Path
from git import Repo
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

# -----------------------------
# Gmail 設定
# -----------------------------
GMAIL_USER = os.environ.get("GMAIL_USER")          # 在 GitHub Secrets 設定
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASS")  # App 密碼
TO_EMAIL = os.environ.get("TO_EMAIL")              # 收件人

# -----------------------------
# Repo 路徑
# -----------------------------
repo_path = Path(__file__).parent
file_path = repo_path / "股票池.csv"

# -----------------------------
# 下載 CSV
# -----------------------------
URL_TWSE = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"
URL_TPEX = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"

twse_df = pd.read_csv(URL_TWSE, encoding="utf-8-sig")
tpex_df = pd.read_csv(URL_TPEX, encoding="utf-8-sig")

df = pd.concat([twse_df, tpex_df], ignore_index=True)
df = df[["公司代號","公司簡稱"]].copy()
df.columns = ["代號","名稱"]
df = df.sort_values("代號").reset_index(drop=True)

# -----------------------------
# 讀舊資料
# -----------------------------
if file_path.exists():
    old_df = pd.read_csv(file_path, encoding="utf-8-sig")
else:
    old_df = pd.DataFrame(columns=["代號","名稱"])

# -----------------------------
# 比對
# -----------------------------
new = df[~df["代號"].isin(old_df["代號"])]
removed = old_df[~old_df["代號"].isin(df["代號"])]

if not df.equals(old_df):
    # 更新股票池
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    repo = Repo(repo_path)
    repo.git.add("股票池.csv")
    repo.index.commit("Update 股票池.csv")
    origin = repo.remote(name='origin')
    origin.push()
    print("股票池.csv 已更新並推送到 GitHub")

    # -----------------------------
    # 發送 Gmail
    # -----------------------------
    content = f"台股股票池變動提醒 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    if not new.empty:
        content += "新增公司：\n" + new.to_string(index=False) + "\n\n"
    if not removed.empty:
        content += "移除公司：\n" + removed.to_string(index=False) + "\n\n"

    msg = MIMEText(content)
    msg["Subject"] = "台股股票池變動通知"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

    print("Gmail 通知已發送")
else:
    print("股票池.csv 沒有變動")
