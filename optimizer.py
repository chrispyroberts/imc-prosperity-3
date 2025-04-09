import subprocess
import re
import os
import pandas as pd
from itertools import product
import time

# Path to the original trader file
ORIGINAL_FILE = "squid_ink_trader_v1.py"
# Path to the temporary file we'll modify
TEMP_FILE = "squid_ink_trader_temp.py"

# Define parameter ranges to test
param_ranges = {
    "WINDOW_SIZE": [500],
    "ENTER": [4.0, 5.0, 6.0],
    "EXIT": [2.0, 3.0, 4.0],
}

# Create a copy of the original file to modify
def create_temp_trader_file():
    with open(ORIGINAL_FILE, 'r') as f:
        content = f.read()
    
    with open(TEMP_FILE, 'w') as f:
        f.write(content)
    
    return content

# Modify the parameters in the temporary file
def modify_parameters(window_size, enter_long, enter_short, exit_long, exit_short):
    with open(TEMP_FILE, 'r') as f:
        content = f.read()
    
    # Replace the parameter values
    pattern_window = r'self\.WINDOW_SIZE\s*=\s*\d+'
    pattern_enter_long = r'self\.ENTER_LONG\s*=\s*-?\d+\.?\d*'
    pattern_enter_short = r'self\.ENTER_SHORT\s*=\s*-?\d+\.?\d*'
    pattern_exit_long = r'self\.exit_long\s*=\s*-?\d+\.?\d*'
    pattern_exit_short = r'self\.exit_short\s*=\s*-?\d+\.?\d*'
    
    content = re.sub(pattern_window, f'self.WINDOW_SIZE = {window_size}', content)
    content = re.sub(pattern_enter_long, f'self.ENTER_LONG = {enter_long}', content)
    content = re.sub(pattern_enter_short, f'self.ENTER_SHORT = {enter_short}', content)
    content = re.sub(pattern_exit_long, f'self.exit_long = {exit_long}', content)
    content = re.sub(pattern_exit_short, f'self.exit_short = {exit_short}', content)
    
    with open(TEMP_FILE, 'w') as f:
        f.write(content)

# Run the backtest and extract the PNL
def run_backtest():
    try:
        # Run the backtest command and show the output in real-time
        print("\n----- Running Backtest -----")
        result = subprocess.run(
            ["python", "-m", "prosperity3bt", TEMP_FILE, "1", "--no-out", '--no-progress'],
            capture_output=True,
            text=True,
            check=True
        )
        
    
        # Extract the PNL from the last line of output
        output_lines = result.stdout.strip().split('\n')
            
        # Extract the PNL from the last line of output
        if output_lines:
            total_profit_line = output_lines[-1]

            if total_profit_line:
                pnl_match = re.search(r'Total profit:\s*(-?[\d,]+)', total_profit_line)
                if pnl_match:
                    # Remove commas from the number and convert to float
                    pnl_str = pnl_match.group(1).replace(',', '')
                    pnl = float(pnl_str)
                    print(f"\n----- Backtest Complete: PNL = {pnl} -----\n")
                    return pnl
                else:
                    print(f"\nCould not extract PNL from output line: {total_profit_line}")
                    return None
            else:
                print("\nNo 'Total profit:' line found in output")
                return None
        else:
            print("\nNo output from backtest command")
            return None
    except Exception as e:
        print(f"Error running backtest: {e}")
        return None
    
# Main function to perform grid search
def grid_search():
    # Make a copy of the original file
    create_temp_trader_file()
    
    results = []
    
    # Generate all parameter combinations
    param_combinations = list(product(
        param_ranges["WINDOW_SIZE"],
        param_ranges["ENTER"],
        param_ranges["EXIT"]
    ))
    
    total_combinations = len(param_combinations)
    print(f"Starting grid search with {total_combinations} parameter combinations...")
    
    # Try each parameter combination
    for i, (window_size, enter, exit) in enumerate(param_combinations):
        enter_long = -enter
        enter_short = enter
        exit_long = -exit
        exit_short = exit
        print(f"Testing combination {i+1}/{total_combinations}: WINDOW_SIZE={window_size}, ENTER_LONG={enter_long}, "
              f"ENTER_SHORT={enter_short}, exit_long={exit_long}, exit_short={exit_short}")
        
        # Modify the parameters
        modify_parameters(window_size, enter_long, enter_short, exit_long, exit_short)
        
        # Run the backtest
        pnl = run_backtest()
        
        if pnl is not None:
            # Record the results
            results.append({
                "WINDOW_SIZE": window_size,
                "ENTER_LONG": enter_long,
                "ENTER_SHORT": enter_short,
                "exit_long": exit_long,
                "exit_short": exit_short,
                "PNL": pnl
            })
            print(f"PNL: {pnl}")
        
        # Short delay to avoid system overload
        time.sleep(0.1)
    
    # Clean up
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by PNL in descending order
    results_df = results_df.sort_values("PNL", ascending=False)
    
    # Save results to CSV
    results_df.to_csv("parameter_optimization_results.csv", index=False)
    
    # Print the top 10 results
    print("\nTop 10 Parameter Combinations:")
    print(results_df.head(10))
    
    # Return the best parameters
    if not results_df.empty:
        best_params = results_df.iloc[0]
        print("\nBest Parameters:")
        print(f"WINDOW_SIZE: {best_params['WINDOW_SIZE']}")
        print(f"ENTER_LONG: {best_params['ENTER_LONG']}")
        print(f"ENTER_SHORT: {best_params['ENTER_SHORT']}")
        print(f"exit_long: {best_params['exit_long']}")
        print(f"exit_short: {best_params['exit_short']}")
        print(f"PNL: {best_params['PNL']}")
        return best_params
    else:
        print("No valid results found.")
        return None

if __name__ == "__main__":
    grid_search()