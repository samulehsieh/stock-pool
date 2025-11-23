import pandas as pd
from pathlib import Path
from git import Repo  # pip install GitPython

# Repo 路徑
repo_path = Path(__file__).parent
file_path = repo_path / "股票池.csv"

# 下載官方 CSV
URL_TWSE = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"
URL_TPEX = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"

twse_df = pd.read_csv(URL_TWSE, encoding="utf-8-sig")
tpex_df = pd.read_csv(URL_TPEX, encoding="utf-8-sig")

# 合併 & 清理欄位
df = pd.concat([twse_df, tpex_df], ignore_index=True)
df = df[["公司代號", "公司簡稱"]].copy()
df.columns = ["代號", "名稱"]
df = df.sort_values("代號").reset_index(drop=True)

# 比對
if file_path.exists():
    old_df = pd.read_csv(file_path, encoding="utf-8-sig")
else:
    old_df = pd.DataFrame(columns=["代號","名稱"])

if not df.equals(old_df):
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    repo = Repo(repo_path)
    repo.git.add("股票池.csv")
    repo.index.commit("Update 股票池.csv")
    origin = repo.remote(name='origin')
    origin.push()
    print("股票池.csv 已更新並推送到 GitHub")
else:
    print("股票池.csv 沒有變動")
