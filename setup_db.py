import pandas as pd
import sqlite3
import os

def setup_database():
    """Download, clean and load Titanic data into SQLite."""
    csv_url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
    print(f"Downloading Titanic dataset from {csv_url}...")
    
    try:
        df = pd.read_csv(csv_url)
        
        # Simple Data Cleaning
        # Fill missing Age values with the median
        df['Age'] = df['Age'].fillna(df['Age'].median())
        # Drop Cabin column (too many missing values)
        df = df.drop(columns=['Cabin'])
        # Fill missing Embarked values with the mode
        df['Embarked'] = df['Embarked'].fillna(df['Embarked'].mode()[0])
        
        # Convert some columns to lowercase to avoid case-sensitivity issues
        df.columns = [c.lower() for c in df.columns]
        
        # Connect to SQLite
        conn = sqlite3.connect('titanic.db')
        print("Loading data into 'titanic' table in 'titanic.db'...")
        df.to_sql('titanic', conn, if_exists='replace', index=False)
        conn.close()
        print("Database setup complete.")
        
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    setup_database()
