"""
Script to check data in production database tables
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings

def check_database_tables():
    """Connect to production database and check table row counts"""
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"\n{'='*80}")
        print(f"Connected to Production Database: {settings.DB_NAME}")
        print(f"Host: {settings.DB_HOST}")
        print(f"{'='*80}\n")
        
        # Get all user tables with row counts
        query = """
        SELECT 
            schemaname,
            tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.\n")
            return
        
        # Display results
        print(f"{'Table Name':<40} {'Row Count':>15}")
        print(f"{'-'*55}")
        
        total_rows = 0
        for table in tables:
            table_name = table['tablename']
            row_count = table['row_count']
            total_rows += row_count
            
            # Color coding for better visibility
            if row_count == 0:
                status = "⚠️  EMPTY"
            elif row_count < 10:
                status = f"✓  {row_count:,}"
            else:
                status = f"✓  {row_count:,}"
            
            print(f"{table_name:<40} {status:>15}")
        
        print(f"{'-'*55}")
        print(f"{'TOTAL':<40} {total_rows:>15,}\n")
        
        # Check specific important tables (customize based on your schema)
        important_tables = ['users', 'products', 'orders', 'transactions', 'refunds']
        
        print(f"\n{'='*80}")
        print("Detailed Check for Important Tables:")
        print(f"{'='*80}\n")
        
        for table_name in important_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
                result = cursor.fetchone()
                count = result['count']
                
                # Get sample data (first 3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_data = cursor.fetchall()
                
                print(f"📊 Table: {table_name}")
                print(f"   Total Rows: {count:,}")
                
                if count > 0 and sample_data:
                    print(f"   Sample Data (first row):")
                    for key, value in sample_data[0].items():
                        print(f"      {key}: {value}")
                else:
                    print(f"   ⚠️  No data in this table")
                
                print()
                
            except psycopg2.Error as e:
                print(f"⚠️  Table '{table_name}' not found or error: {e}\n")
        
        cursor.close()
        conn.close()
        
        print(f"{'='*80}")
        print("Database check completed successfully!")
        print(f"{'='*80}\n")
        
    except psycopg2.Error as e:
        print(f"❌ Database connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_tables()
