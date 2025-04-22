import subprocess
import re
import os
import pandas as pd
from itertools import product
import time

# === CONFIG ===
ORIGINAL_FILE = "OLIVIA IS THE GOAT.py"  # <-- your trader file
TEMP_FILE = "temp_trader.py"

param_ranges = {
    "window_size": [10, 15, 20, 25, 30],
    "voucher_trading_threshold": [0.2, 0.4, 0.5, 0.6, 0.8],
}

# === FILE SETUP ===
def create_temp_trader_file():
    with open(ORIGINAL_FILE, 'r') as f:
        content = f.read()
    with open(TEMP_FILE, 'w') as f:
        f.write(content)
    return content

def modify_parameters(window_size, threshold):
    with open(TEMP_FILE, 'r') as f:
        content = f.read()

    content = re.sub(r'self\.window_size\s*=\s*\d+', f'self.window_size = {window_size}', content)
    content = re.sub(r'self\.voucher_trading_threshold\s*=\s*[\d.]+', f'self.voucher_trading_threshold = {threshold}', content)

    with open(TEMP_FILE, 'w') as f:
        f.write(content)

# === BACKTEST RUNNER ===
def run_backtest():
    try:
        result = subprocess.run(
            ["python", "-m", "prosperity3bt", TEMP_FILE, "5-1" , "--no-out", "--no-progress"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        if lines:
            last_line = lines[-1]
            print(last_line)
            match = re.search(r'Total profit:\s*(-?[\d,]+)', last_line)
            if match:
                pnl = float(match.group(1).replace(',', ''))
                return pnl
    except Exception as e:
        print(f"[ERROR] Backtest failed: {e}")
    return None

# === GRID SEARCH ===
def grid_search():
    print("🧪 Starting Grid Search...")
    create_temp_trader_file()
    results = []

    combinations = list(product(
        param_ranges["window_size"],
        param_ranges["voucher_trading_threshold"]
    ))

    for i, (ws, thresh) in enumerate(combinations):
        print(f"▶️ ({i+1}/{len(combinations)}) Testing window_size={ws}, threshold={thresh}")
        modify_parameters(ws, thresh)
        pnl = run_backtest()
        if pnl is not None:
            results.append({
                "window_size": ws,
                "voucher_trading_threshold": thresh,
                "PNL": pnl
            })
        else:
            print("⚠️ No PNL returned, skipping...")
        time.sleep(0.1)

    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    df = pd.DataFrame(results).sort_values(by="PNL", ascending=False)
    df.to_csv("voucher_gridsearch_results.csv", index=False)
    print("\n✅ Grid search complete! Top 5 results:")
    print(df.head(5).to_string(index=False))

if __name__ == "__main__":
    grid_search()
