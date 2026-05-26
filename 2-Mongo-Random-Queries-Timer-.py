import random
import os
from pymongo import MongoClient
from datetime import timedelta
from faker import Faker
import time
import csv

fake=Faker()
fake = Faker('it_IT')
fake_it = Faker('it_IT')

#1.Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["mobility_platform"]

users_collection = db["users"]
trips_collection = db["trips"]
stations_collection = db["stations"]
events_collection = db["events"]

#  2.Inputs
user_counts = [1000, 10000, 50000]    
trip_counts = [10000, 50000, 100000]
events_options = [0, 2, 5, 10]
num_stations = 120

results1=[]

#3. Clear (Function) 
def clear_information(db):
    db.users.drop()
    db.trips.drop()
    db.events.drop()



# 4 users-insert (Function) 
def insert_users(db, n_users):
    users_collection = db["users"]
    user_doc = []
    for i in range(n_users):
        new_user= {
            "user_id": i+1,
            "name_user": fake.first_name(), 
            "surname_user": fake.last_name(),
            "birthdate":str(fake.date_of_birth(minimum_age=18, maximum_age=70)),
            "country_user_origin": fake.country()
        }
         #adding to list
        user_doc.append(new_user)
        #add into mongo
    if user_doc:
        users_collection.insert_many(user_doc)
      #  print(f" Successfully inserted {n_users} users.")

# 5.station-insert (Function)
  
def insert_stations(db, n_stations):
    stations_collection = db["stations"]
    stations = []
    for i in range(n_stations):
        city = fake_it.city()
        station_name = f"station_{city}_{i+1}"
        station_doc = {
            "station_id": i+1,
            "name_station": station_name,
            "city_station": city,
            "maximum_capacity": fake.random_int(5, 1000),
            "location_station": {
                "type": "Point",
                "coordinates": [float(fake_it.longitude()), float(fake_it.latitude())]
            }
        }
        stations.append(station_doc)
    if stations:
      stations_collection.insert_many(stations)
     # print(f"Successfully inserted {n_stations} stations into MongoDB.")

# 6.Trip-insert (Function)     
def insert_trips(db, n_trips):
   trips_collection = db["trips"]
   user_ids = db["users"].distinct("user_id")
   station_ids = db["stations"].distinct("station_id")
   trips = []

   for i in range(n_trips):
        user_id = random.choice(user_ids)
        start_station = random.choice(station_ids)
        end_station = random.choice(station_ids)
        start_time = fake.date_time_between(start_date='-30d', end_date='now')
        end_time = start_time + timedelta(hours=random.randint(1, 5))
        total_cost = round(random.uniform(5.0, 50.0), 2)  #cost

        trip_doc = {
            "user_id": user_id,
            "start_station_id": start_station,
            "end_station_id": end_station,
            "start_time": start_time,
            "end_time": end_time,
            "total_cost": total_cost
        }
        trips.append(trip_doc)

   if trips:
       trips_collection.insert_many(trips)
       print(f"Successfully inserted {n_trips} trips into MongoDB.")

# 7.Event-insert   
def insert_events(db, events_per_trip):
    if events_per_trip == 0:
        print("We don't have any event")
        return
    events_collection = db["events"]
    trips = list(db["trips"].find({}, {"_id": 1, "start_time": 1, "end_time": 1}))
    event_types = ['Delays', 'Battery', 'GPS', 'Errors']
    all_events = []
    for trip in trips:
        for _ in range(events_per_trip):          
            timestamp = fake.date_time_between(
            start_date=trip["start_time"], 
            end_date=trip["end_time"]
            )
            
            event_doc = {
                "trip_id": trip["_id"],  
                "timestamp_event": timestamp,
                "event_type": random.choice(event_types),
                "location_event": {
                    "type": "Point",
                    "coordinates": [float(fake.longitude()), float(fake.latitude())]
                }
            }
            all_events.append(event_doc)

    if all_events:
        events_collection.insert_many(all_events)
        print(f" Events submitted successfully for {len(all_events)} records.")

# 8.run-Query1   
def run_query1(db):   
   start = time.time() 
     #"Return all trips with: user information, start and end station names"   # Joing users, trip, and station tables- "trip information and name of station" 
   query1= [ 
       {
          # 1. Join with users collection
           "$lookup":{
                "from": "users",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user_info"
            }
      },
      # convert user array into object
      {"$unwind": "$user_info"},
       # 2. Join with stations collection
       {
           "$lookup": {
                "from": "stations",
                "localField": "start_station_id",
                "foreignField": "station_id",
                "as": "start_st_info"
           }
       },
       {"$unwind": "$start_st_info"},
        # 3. Join with stations collection for the end-station
        {
            "$lookup":{
               "from": "stations",
                "localField": "end_station_id",
                "foreignField": "station_id",
                "as": "end_st_info"
            }
        },
        {"$unwind": "$end_st_info"},
        # 4. Now, selectione the main fields
        {
            "$project": {
                "trip_id": 1,
                "user_id": "$user_info.user_id",
                "name_user": "$user_info.name_user",
                "surname_user": "$user_info.surname_user",
                "country_user_origin": "$user_info.country_user_origin",
                "start_station": "$start_st_info.name_station",
                "end_station": "$end_st_info.name_station",
                "_id": 0
            }
        }
      ]
   results = list(db["trips"].aggregate(query1))
   return time.time() - start

# 9.run-Query2   
def run_query2(db):   
   start = time.time() 
     #"Return all users with: number of trips performed, average trip duration"    #GROUP BY, user information, average.time.
   query2= [ 
       # 1. Join with trips collection (LEFT JOIN)
       {
            "$lookup": {
                "from": "trips",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "user_trips"
            }
       },
       {
            "$unwind": {
                "path": "$user_trips",
                "preserveNullAndEmptyArrays": True 
            }
        },
        # 3. time
        {
            "$project": {
                "user_id": 1,
                "name_user": 1,
                "surname_user": 1,
                "duration": {
                    "$subtract": ["$user_trips.end_time", "$user_trips.start_time"]
                },
                "has_trip": { "$cond": [{ "$ifNull": ["$user_trips.trip_id", False] }, 1, 0] }
            }
        },
        # 4. (GROUP BY based on group and duration
        {
            "$group": {
                "_id": {
                    "user_id": "$user_id",
                    "name_user": "$name_user",
                    "surname_user": "$surname_user"
                },
                "total_trips": { "$sum": "$has_trip" }, #Calculating the number of trips
                "avg_tripduration": { "$avg": "$duration" } # Average the time duration
            }
        },
        # 5. Sorting the results
        {
            "$project": {
                "user_id": "$_id.user_id",
                "name_user": "$_id.name_user",
                "surname_user": "$_id.surname_user",
                "total_trips": 1,
                "avg_tripduration": 1,
                "_id": 0
            }
        }
   ]
   results = list(db["users"].aggregate(query2))
   return time.time() - start
# 10.run-Query3
def run_query3(db):
    start = time.time()
    query3 = [
        # 1. number of trips which are started
        {
            "$lookup": {
                "from": "trips",
                "localField": "station_id",
                "foreignField": "start_station_id",
                "as": "started_docs"
            }
},
        # 2. number of trips which are finished in that station
        {
            "$lookup": {
                "from": "trips",
                "localField": "station_id",
                "foreignField": "end_station_id",
                "as": "ended_docs"
            }
        },
        # 3. convert list to number
        {
            "$project": {
                "name_station": 1,
                "trips_started": { "$size": "$started_docs" },
                "trips_ended": { "$size": "$ended_docs" },
                "_id": 0
            }
        }
    ]
    results = list(db["stations"].aggregate(query3))  
    return time.time() - start

# 11.run-Query4
def run_query4(db):   
    start = time.time()
    #"Return all trips that contain at least one event with type ERROR;"m  #filter Error
    query4 = [
        # 1. Join with collection events
        {
            "$lookup": {
                "from": "events",
                "localField": "trip_id",
                "foreignField": "trip_id",
                "as": "trip_events"
            }
        },
        # 2. Filtering the events which have at least one ERROR 
        {
            "$match": {
                "trip_events.event_type": "ERROR"
            }
        },
        # 3. remove the repetitive items
        # grouping beased on  "trip_id"----> lead each trip present once 
        {
            "$group": {
                "_id": "$trip_id",
                "user_id": { "$first": "$user_id" },
                "start_time": { "$first": "$start_time" }
            }
        },
        # 4. Sorting the final result
        {
            "$project": {
                "trip_id": "$_id",
                "user_id": 1,
                "start_time": 1,
                "_id": 0
            }
        }
    ]
    results = list(db["trips"].aggregate(query4))
    return time.time() - start

# main function-part
insert_num=1
i=1
insert_stations(db, num_stations)
# clear_information(db)
for n_users in user_counts:
     for n_trips in trip_counts:
         for events in events_options:
                print(f"Execution Round #:{insert_num}")
            # print(f" Users={n_users}, Trips={n_trips}, Events={events}")
                print("\n------------------------------------------------------------")
                clear_information(db)
                insert_users (db, n_users)
                insert_trips (db, n_trips)
                insert_events (db, events)
                insert_num += 1
                
            # Save automatically fake information
                state_dir = f"E:\\Test_State\\Test_{i}"
                if not os.path.exists(state_dir):
                 os.makedirs(state_dir)
                 print(f"is running and saving {i}...")

                 # 1. Saving the data fake for Users
                users_data = list(db.users.find({}, {"_id": 0})) # read of Mongo
                if users_data:
                   headers_u = users_data[0].keys()
                   with open(os.path.join(state_dir, f"01_users_state_{i}.csv"), mode='w', newline='', encoding='utf-8-sig') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=headers_u)
                    writer.writeheader()
                    writer.writerows(users_data)

                # 2. Saving the data fake for Trips
                trips_data = list(db.trips.find({}, {"_id": 0}))
                if trips_data:
                 headers_t = trips_data[0].keys()
                with open(os.path.join(state_dir, f"02_trips_state_{i}.csv"), mode='w', newline='', encoding='utf-8-sig') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=headers_t)
                    writer.writeheader()
                    writer.writerows(trips_data)
                # 3. Saving the data fake for Events
                events_data = list(db.events.find({}, {"_id": 0}))
                if events_data and len(events_data) > 0:
                  headers_e = events_data[0].keys()
                  with open(os.path.join(state_dir, f"03_events_state_{i}.csv"), mode='w', newline='', encoding='utf-8-sig') as f_out:
                        writer = csv.DictWriter(f_out, fieldnames=headers_e)
                        writer.writeheader()
                        writer.writerows(events_data)    
                #  4. Saving the data fake for Stations
                stations_data = list(db.stations.find({}, {"_id": 0}))
                if stations_data:
                 headers_s = stations_data[0].keys()
                with open(os.path.join(state_dir, f"04_stations_state_{i}.csv"), mode='w', newline='', encoding='utf-8-sig') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=headers_s)
                    writer.writeheader()
                    writer.writerows(stations_data)
                print(f"Data {i} is saved successu")
                i+=1
                # -----------------------------------------------------
                db.users.create_index("user_id")
                db.trips.create_index("user_id")
                db.trips.create_index("start_station_id")
                db.trips.create_index("end_station_id")
                db.events.create_index("trip_id")

                time_q1 = run_query1(db)
                time_q2 = run_query2(db)
                time_q3 = run_query3(db)
                time_q4 = run_query4(db)

                results1.append ([n_users, num_stations, n_trips, events, time_q1, time_q2, time_q3, time_q4])
                print(f"Results: Q1={time_q1:.4f}s, ,Q2={time_q2:.4f}s,Q3={time_q3:.4f}s, Q4={time_q4:.4f}s")   
                print("Test Case Completed Successfully.\n")   

                file_name1 = r"C:\Users\Asus\Desktop\performance_results.csv"
                header5 = ["Users", "Stations", "Trips", "Events","Time_Q1", "Time_Q2", "Time_Q3", "Time_Q4"]

                with open(file_name1, mode='w', newline='') as f:
                 writer = csv.writer(f)
                 writer.writerow(header5)
                 writer.writerows(results1)      

