import sqlite3

# db_path = r"G:\\Yuval_Dahan\\Latency\\Latency_Results\\latency_results.db"

# conn = sqlite3.connect(db_path)
# cur = conn.cursor()

# # Run the migration – add the new column
# cur.execute("ALTER TABLE test_results ADD COLUMN uplink_transceiver TEXT;")

# conn.commit()
# conn.close()

# print("✅ Column 'module_type' added successfully.")


conn = sqlite3.connect(r"G:\\Yuval_Dahan\\Latency\\Latency_Results\\latency_results.db")
cur = conn.cursor()
cur.execute("PRAGMA table_info(test_results);")
for row in cur.fetchall():
    print(row)
conn.close()