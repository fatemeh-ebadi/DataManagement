import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
import time
import random
from datetime import timedelta
import csv

fake=Faker()
fake_it = Faker('it_IT')
stations = []    

#1.Connection
conn = psycopg2.connect(
    dbname="mobilityplatform_db",
    user="postgres",
    password="1161369fatemeh",
    host="localhost",
    port="5432"
    )

cur = conn.cursor()


#  2.Inputs
user_counts = [1000, 10000, 50000]    # users
trip_counts = [10000, 50000, 100000]     #trips
events_options = [0, 2, 5, 10]
 
 
num_users = user_counts[0]
num_trips = trip_counts[0]
num_station=100


#3. Clear (Function) 
def  clear_information(conn):
     with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE users, trip, events RESTART IDENTITY CASCADE;")
        conn.commit()

# 4 users-insert (Function) 
def insert_users(conn, n_users):
    users = []
    for i in range(n_users):
        users.append((
            fake.first_name(), 
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=70),
            fake.country()
        ))

    query = "INSERT INTO users (name_user, surname_user, birthdate_user, country_user_origin) VALUES %s"

    with conn.cursor() as cur:
        execute_values(cur, query, users)
        conn.commit()

 # 5.station-insert (Function) 
def insert_stations(conn, n_station):
    #fake_it=Faker('it_IT')
    stations = []    
    for i in range(n_station):
        #Creating the real name of Italian Cities
        city = fake_it.city()
        station_name = f"station_{city}_{i+1}"

        stations.append((
            station_name,
            city,
            fake_it.random_int(5, 1000),      # Maximum_capacity
            f"POINT({fake_it.longitude()} {fake_it.latitude()})" # location_station
        ))
    query1= " INSERT INTO station (name_station, city_station, maximum_capacity, location_station) VALUES %s"       
    with conn.cursor() as cur:
       execute_values(cur, query1, stations)
       conn.commit()
    print(f"Successfully inserted {n_station} stations.") 

 # 6.Trip-insert (Function)     
def insert_trips(conn, n_trips):   
     with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT station_id FROM station")
        station_ids = [row[0] for row in cur.fetchall()]
        trips = []
        for i in range(n_trips):
        # The random selection of user, start and end station 
            user_id = random.choice(user_ids)
            start_station = random.choice(station_ids)
            end_station = random.choice(station_ids) 
            start_time = fake.date_time_between(start_date='-30d', end_date='now')   # a range for one month among 30 days ago and now.
            end_time = start_time + timedelta(hours=random.randint(1, 5))     #Start Time + Timedelta = End Time    #10+3hours=1pm
            total_cost = round(random.uniform(5.0, 50.0), 2) # total_cost:Minimum price(5)+Maximum price(50), Rounds to two decimal places for cents(2)
            trips.append((    #The name of my array
                        user_id,
                        start_station,
                        end_station,
                        start_time,
                        end_time,
                        total_cost
                    ))
            #print(f"Successfully inserted {len(trips)} of {n_trips} into the new trips.")

        query2 = "INSERT INTO trip (user_id, start_station, end_station, start_time, end_time, total_cost) VALUES %s"
        execute_values(cur, query2, trips)
        conn.commit()    
           


 # 7.Event-insert   
def insert_events(conn, events):
      if events == 0:
        print("We don't have any event")
        return
      
      with conn.cursor() as cur:
        cur.execute("SELECT trip_id, start_time, end_time FROM trip") # recieve trip infomation
        trips = cur.fetchall()
        
        all_events = []
        event_types = ['Delays', 'Battery', 'GPS', 'Errors']
        for trip in trips: #for each loop, one of raw which are from trips table
            trip_i, start_t, end_t = trip

            for i in range(events):
              event_time = fake.date_time_between(start_date=start_t, end_date=end_t)

              all_events.append((
                    trip_i,
                    event_time,
                    random.choice(event_types),
                    f"POINT({fake.latitude()} {fake.longitude()})"
                ))
        query3 = "INSERT INTO events (trip_id, timestamp_event, event_type, location_event) VALUES %s"
        execute_values(cur, query3, all_events)
        conn.commit()
        print(f"events are submitted  successfully for {len(all_events)}.")
        
# 8.run-Query1      
def run_query1(conn):   
    start = time.time()
    #"Return all trips with: user information, start and end station names"  # Joing users, trip, and station tables- "trip information and name of station"
    with conn.cursor() as cur:
            query4= """SELECT t.trip_id, u.user_id, u.name_user, u.surname_user, u.country_user_origin,
                st1.name_station as start_station, st2.name_station AS end_station
                
                    FROM trip as t join users as u on t.user_id=u.user_id 
                    join station as st1 on t.start_station=st1.station_id
                join station as st2 on t.end_station=st2.station_id
            """
            cur.execute(query4)
            cur.fetchall()
    return time.time()-start

# 9.run-Query2
def run_query2(conn):   
    start = time.time()
    #"Return all users with: number of trips performed, average trip duration"    #GROUP BY, user information, average.time, 
    with conn.cursor() as cur:
        query5="""select u.user_id, u.name_user, u.surname_user, COUNT(t.trip_id) as total_trips,
                AVG((t.end_time-t.start_time)) as avg_tripduration
                from users as u left join trip as t on u.user_id=t.user_id
                GROUP BY u.user_id, u.name_user, u.surname_user;
            """
        cur.execute(query5)
        cur.fetchall()
    return time.time() - start

# 10.run-Query3
def run_query3(conn):   
    start = time.time()
    #"Return all stations with: number of trips starting there, number of trips ending there;" # number of stations
    with conn.cursor() as cur:
        query6=""" select st.name_station,
                    (select COUNT(*) from trip t where t.start_station = st.station_id) as trips_started,
                    (select COUNT(*) from trip t where t.end_station = st.station_id) as trips_ended
                from station st;
            """
        cur.execute(query6)
        cur.fetchall()
    return time.time() - start
    
# 11.run-Query4
def run_query4(conn):   
    start = time.time()
    #"Return all trips that contain at least one event with type ERROR;"m  #filter Error
    with conn.cursor() as cur:
        query7="""
            SELECT DISTINCT t.trip_id, t.user_id, t.start_time
            FROM trip AS t join events as e on t.trip_id = e.trip_id
            where e.event_type = 'ERROR';
            """
        cur.execute(query7)
        cur.fetchall()
    return time.time() -start

number_insert=1

results=[]
# main function-part
insert_stations(conn, num_station)   
print(num_station)   
for n_users in user_counts:     
       for n_trips in trip_counts:
         for events in events_options:
              
              print(f"Execution Round #:{number_insert},----------, Number of Station: {num_station}")
              print(f" Users={n_users}, Trips={n_trips}, Events={events}")   
             
              number_insert +=1
              clear_information(conn)    
              insert_users(conn,n_users)
              insert_trips(conn,n_trips)
              insert_events(conn,events)
              time_q1 = run_query1(conn)
              time_q2 = run_query2(conn)
              time_q3 = run_query3(conn)
              time_q4 = run_query4(conn)
              results.append ([n_users, num_station, n_trips, events, time_q1, time_q2, time_q3, time_q4])
              print(f"Results: Q1={time_q1:.4f}s, Q2={time_q2:.4f}s, Q3={time_q3:.4f}s, Q4={time_q4:.4f}s")             
              print("Test Case Completed Successfully.\n")
              print("\n---------------------------------------------------------------------------------")
file_name = "performance_results.csv"
header = ["Users", "Stations", "Trips", "Events", "Time_Q1", "Time_Q2", "Time_Q3", "Time_Q4"]

with open(file_name, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(results)

print(f"✅ All results saved successfully in {file_name}!")
  



  