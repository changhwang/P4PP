import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_excel(r'4pp_BOM_v5.xlsx')

print(f"Total items: {len(df)}")
print()

for i, row in df.iterrows():
    item_num = int(row['Item #']) if pd.notna(row['Item #']) else 0
    cat = str(row['Category'])[:25] if pd.notna(row['Category']) else ''
    item = str(row['Item'])[:55] if pd.notna(row['Item']) else ''
    qty = int(row['Qty']) if pd.notna(row['Qty']) else 0
    print(f"{item_num:2d}. [{cat:25s}] {item:55s} x{qty}")
