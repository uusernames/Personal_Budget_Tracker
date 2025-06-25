import sqlite3 #local SQLite database
import pandas as pd #data manipulation
import os  #file and directory operations

# Paths
DB_PATH = "budget.db" # SQLite database file
CSV_PATH = "data/sample_transactions.csv" # Input CSV file with transactions EXCEL fornat
OUTPUT_PATH = "output/monthly_summary.xlsx" # Output Excel file

os.makedirs("output", exist_ok=True) # creates output folder if it doesn't exist

# Load CSV
df = pd.read_csv(CSV_PATH, parse_dates=["date"]) #using padas to read CSV define dateframe set the date column as datetime

# Categorize into just 3 groups
def categorize_simple(row): #
    cat = row['category'].lower() # Convert category to lowercase for consistency
    amt = row['amount'] # Get the amount
    if cat == 'rent' and amt > 0:  # If rent is positive, categorize as Mandatory Expenses
        return "Mandatory Expenses"
    elif cat == 'salary': # If category is salary, categorize as Salary
        return "Salary"
    elif amt > 0: # If amount is positive and not salary, categorize as Expenses
        return "Expenses"
    else:
        # Assuming negative salary or refunds as income, lump them into Salary for simplicity
        return "Salary"

df['simple_category'] = df.apply(categorize, axis=1) # creates new column 'Category'

# Connect to DB and setup table
conn = sqlite3.connect(DB_PATH) # Connect to SQLite database
cursor = conn.cursor() # Create a cursor to execute SQL commands

cursor.execute("DROP TABLE IF EXISTS transactions") #delete existing table if it exists

cursor.execute("""
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL,
    simple_category TEXT
)
""")#define the table structure and variabbles

# Insert data
df.to_sql("transactions", conn, if_exists="append", index=False) # Insert the DataFrame into the SQLite table

# Query: sum by month and simple_category
query = """
SELECT 
    strftime('%Y-%m', date) AS month, 
    simple_category,
    SUM(amount) AS total
FROM transactions
GROUP BY month, simple_category
ORDER BY month, simple_category
""" #converts date to year month format, adds up the amounts by month and category, groups by the rows ad combination of month and category.

summary_df = pd.read_sql_query(query, conn)     # Execute the SQL query and load the result into a DataFrame

# Pivot to get rows as categories and columns as months
pivot = summary_df.pivot(index="simple_category", columns="month", values="total").fillna(0) 
pivot = pivot.reindex(["Expenses", "Mandatory Expenses", "Salary"]) # reorder categories
pivot.to_excel(OUTPUT_PATH) # Export to Excel

print(f" Summary with 3 categories exported to {OUTPUT_PATH}")
