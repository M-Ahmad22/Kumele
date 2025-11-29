# import psycopg2

# try:
#     # Connect as superuser
#     conn = psycopg2.connect(
#         host="localhost",
#         port=5432,
#         database="postgres",
#         user="postgres",
#         password="Ahmad@22"  # must be correct!
#     )
#     conn.autocommit = True  # Required for ALTER USER

#     cur = conn.cursor()
#     # Change password
#     cur.execute("ALTER USER postgres WITH PASSWORD 'Ahmad@22';")
#     print("✅ Password changed successfully!")

#     cur.close()
#     conn.close()

# except Exception as e:
#     print("❌ Failed:", e)

# import psycopg2

# conn = psycopg2.connect(
#     dbname="kumele_synthetic",
#     user="postgres",
#     password="Ahmad@22",
#     host="localhost",
#     port=5432
# )
# cur = conn.cursor()
# cur.execute("SELECT 1;")
# print(cur.fetchone())
# conn.close()

import sqlalchemy as sa

DATABASE_URL = "postgresql://neondb_owner:npg_AGR3UqkWr9Hm@ep-little-wildflower-a44yju28-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = sa.create_engine(DATABASE_URL, future=True)

try:
    with engine.connect() as conn:
        result = conn.execute(sa.text("SELECT NOW()"))
        print("Connected!", result.fetchone())
except Exception as e:
    print("FAILED:", e)
