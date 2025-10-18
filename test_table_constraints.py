#!/usr/bin/env python3
"""
Test script to check the actual constraints on security_price_dtl table
"""
from source_code.config import pg_db_conn_manager

def check_table_constraints():
    """Check what unique constraints exist on security_price_dtl table"""
    print("=" * 60)
    print("CHECKING security_price_dtl TABLE CONSTRAINTS")
    print("=" * 60)
    
    try:
        # Query to check unique constraints on the table
        constraints_query = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            tc.is_deferrable,
            tc.initially_deferred
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name 
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_name = 'security_price_dtl'
            AND tc.table_schema = 'public'
            AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
        ORDER BY tc.constraint_name, kcu.ordinal_position;
        """
        
        constraints = pg_db_conn_manager.fetch_data(constraints_query)
        
        if constraints:
            print("Found constraints:")
            current_constraint = None
            columns = []
            
            for constraint in constraints:
                if current_constraint != constraint['constraint_name']:
                    if current_constraint:
                        print(f"  {current_constraint} ({constraint_type}): {', '.join(columns)}")
                    current_constraint = constraint['constraint_name']
                    constraint_type = constraint['constraint_type']
                    columns = []
                
                columns.append(constraint['column_name'])
            
            # Print last constraint
            if current_constraint:
                print(f"  {current_constraint} ({constraint_type}): {', '.join(columns)}")
        else:
            print("❌ No unique or primary key constraints found on security_price_dtl table")
        
        # Also check table structure
        print("\nTable structure:")
        table_structure_query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'security_price_dtl' 
            AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        
        columns = pg_db_conn_manager.fetch_data(table_structure_query)
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        return constraints
        
    except Exception as e:
        print(f"❌ Error checking constraints: {str(e)}")
        return []

def main():
    print("SECURITY PRICE TABLE CONSTRAINT ANALYSIS")
    print("=" * 60)
    
    constraints = check_table_constraints()
    
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    
    if constraints:
        print("✅ Found constraints on security_price_dtl table")
        print("\nNext steps:")
        print("• Update batch_upsert ON CONFLICT clause to use existing constraint")
        print("• Or create appropriate unique constraint if needed")
    else:
        print("❌ No unique constraints found - this explains the error")
        print("\nPossible solutions:")
        print("• Add unique constraint on (security_id, price_source_id, price_date)")
        print("• Or use ON CONFLICT (security_price_id) if that's the primary key")
        print("• Or remove ON CONFLICT clause and handle duplicates differently")

if __name__ == "__main__":
    main()