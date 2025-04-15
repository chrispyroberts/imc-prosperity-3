import subprocess
import re
import os
import pandas as pd
from itertools import product
import time

# === CONFIG ===
ORIGINAL_FILE = "french_guy.py"  # <- Change if your actual trader file has a different name
TEMP_FILE = "basket_trader_temp.py"

param_ranges = {
    "z_score_threshold": [10, 15, 20, 25, 30],
    "z_score_threshold_basket_2": [10, 15, 20, 25, 30],
    "premium_diff_window": [30, 40, 50, 60, 70, 250, 1000],
}

# === FILE SETUP ===
def create_temp_trader_file():
    with open(ORIGINAL_FILE, 'r') as f:
        content = f.read()
    with open(TEMP_FILE, 'w') as f:
        f.write(content)
    return content

def modify_parameters(z_score, z_score_b2, window):
    with open(TEMP_FILE, 'r') as f:
        content = f.read()
    
    content = re.sub(r'self\.z_score_threshold\s*=\s*\d+', f'self.z_score_threshold = {z_score}', content)
    content = re.sub(r'self\.z_score_threshold_basket_2\s*=\s*\d+', f'self.z_score_threshold_basket_2 = {z_score_b2}', content)
    content = re.sub(r'self\.premium_diff_window\s*=\s*\d+', f'self.premium_diff_window = {window}', content)

    with open(TEMP_FILE, 'w') as f:
        f.write(content)

# === BACKTEST RUNNER ===
def run_backtest():
    try:
        result = subprocess.run(
            ["python", "-m", "prosperity3bt", TEMP_FILE, "2", "--no-out", "--no-progress"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        if lines:
            last_line = lines[-1]
            match = re.search(r'Total profit:\s*(-?[\d,]+)', last_line)
            if match:
                pnl = float(match.group(1).replace(',', ''))
                return pnl
    except Exception as e:
        print(f"[ERROR] Backtest failed: {e}")
    return None

# === GRID SEARCH ===
def grid_search():
    print("📈 Starting Grid Search...")
    create_temp_trader_file()
    results = []
    
    combinations = list(product(
        param_ranges["z_score_threshold"],
        param_ranges["z_score_threshold_basket_2"],
        param_ranges["premium_diff_window"]
    ))

    for i, (z, z_b2, win) in enumerate(combinations):
        print(f"▶️ ({i+1}/{len(combinations)}) Testing z={z}, z_b2={z_b2}, window={win}")
        modify_parameters(z, z_b2, win)
        pnl = run_backtest()
        if pnl is not None:
            results.append({
                "z_score_threshold": z,
                "z_score_threshold_basket_2": z_b2,
                "premium_diff_window": win,
                "PNL": pnl
            })
        else:
            print("⚠️ No PNL returned, skipping...")
        time.sleep(0.1)

    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    df = pd.DataFrame(results).sort_values(by="PNL", ascending=False)
    df.to_csv("basket_gridsearch_results.csv", index=False)
    print("\n✅ Grid search complete! Top 5 results:")
    print(df.head(5).to_string(index=False))

if __name__ == "__main__":
    grid_search()
