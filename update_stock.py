import pandas as pd
from pathlib import Path
import requests
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
from subprocess import run, PIPE

# -----------------------------
# Gmail 設定（從 GitHub Secrets）
# -----------------------------
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")

# -----------------------------
# Repo 路徑
# -----------------------------
repo_path = Path(__file__).parent
file_path = repo_path / "股票池.csv"

# -----------------------------
# 你原本的 CSV 網址（保持不動）
# -----------------------------
URL_TWSE = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"
URL_TPEX = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"

# -----------------------------
# 下載 CSV
# -----------------------------
def fetch_csv(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8-sig"
    df = pd.read_csv(StringIO(r.text))
    df.columns = df.columns.str.strip()  # 去掉欄位空白
    return df

twse_df = fetch_csv(URL_TWSE)
tpex_df = fetch_csv(URL_TPEX)

# -----------------------------
# 合併 & 清理欄位
# -----------------------------
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
    # 更新 CSV
    df.to_csv(file_path, index=False, encoding="utf-8-sig")

    # -----------------------------
    # 用 git CLI push
    # -----------------------------
    token = os.environ["GITHUB_TOKEN"]
    repo_url = "https://github.com/samulehsieh/-.git"  # 改成你 repo 名稱
    repo_url_with_token = f"https://x-access-token:{token}@github.com/samulehsieh/-.git"

    run(["git", "config", "--global", "user.email", "action@github.com"], cwd=repo_path)
    run(["git", "config", "--global", "user.name", "GitHub Action"], cwd=repo_path)
    run(["git", "remote", "set-url", "origin", repo_url_with_token], cwd=repo_path)

    run(["git", "add", "股票池.csv"], cwd=repo_path)
    run(["git", "commit", "-m", "Update 股票池.csv"], cwd=repo_path, stdout=PIPE, stderr=PIPE)
    run(["git", "push", "origin", "HEAD"], cwd=repo_path)

    # -----------------------------
    # Gmail 通知
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

    print("股票池.csv 已更新並推送到 GitHub，Gmail 通知已發送")
else:
    print("股票池.csv 沒有變動")
