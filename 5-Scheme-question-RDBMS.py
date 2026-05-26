import psycopg2
import random


#1.connection
conn = psycopg2.connect(
    database="mobilityplatform_db", 
    user="postgres", 
    password="1161369fatemeh",
    host="localhost",
    port="5432"
    )

cur = conn.cursor()

#2. Writing query
# def upgrade_schema():
#     alter_query = """
#         alter table events 
#         add column if not exists battery_level integer
#         check (battery_level >= 0 and battery_level <= 100);
#         """
#     try:
#        with conn.cursor() as cur:
#         cur.execute(alter_query)
#         conn.commit()
#         print("Schema updated successfully!")
#     except:
#         print(f"Error")
# upgrade_schema()


#3.insert value in the battery_value

def update_event_type():
    try:
        with conn.cursor() as cur:
            # 1. recieve event-id, time of events table 
            cur.execute("select event_id from events where battery_level is null")
            rows = cur.fetchall()
            for row in rows:
                event_id = row[0]

                # creating random input among 0 to 100               
                new_value = random.randint(0, 100)
                
                # 2. update the records based on (trip_id)
                cur.execute(
                    "update events set battery_level = %s where event_id = %s",  #When find event_id, update that recorde with new value which is random
                    (new_value, event_id)
                )
            
            conn.commit()
            print(f"Successfully updated {len(rows)} records.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
update_event_type()
