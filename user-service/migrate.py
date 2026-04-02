import psycopg2
import os
import time

def migrate():
    print("🚀 Starting Database Migration...")
    db_config = {
        "host": os.environ["DB_HOST"],
        "database": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASS"]
    }

    # Retry logic for DB readiness
    conn = None
    for i in range(10):
        try:
            conn = psycopg2.connect(**db_config)
            print("Connected to Database!")
            break
        except Exception as e:
            print(f"Waiting for DB... (attempt {i+1}/10) Error: {e}")
            time.sleep(2)

    if not conn:
        print("Could not connect to DB")
        exit(1)

    cur = conn.cursor()
    try:
        # STEP 1: Ensure the table exists
        print("Ensuring 'users' table exists...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE
            );
        """)

        # STEP 2: Rename logic (Legacy support for 'name' column)
        cur.execute("""
            DO $$ 
            BEGIN 
                IF EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name='users' AND column_name='name') THEN
                    ALTER TABLE users RENAME COLUMN name TO username;
                    RAISE NOTICE 'Successfully renamed name to username';
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("Migration complete! Table is ready.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()