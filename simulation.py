! pip install neo4j faker

import random
from faker import Faker
from neo4j import GraphDatabase
from datetime import timedelta

fake = Faker()
fake_it = Faker('it_IT')

# 1. Connection to Neo4j Aura
NEO4J_URI = "neo4j+s://61ca1db0.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Ad5HNN6K4O36vQhb1XJbYeBBiX9yLVwObqZUyPlfOD0"
if 'driver' in globals() and globals()['driver'] is not None:
    try:
        globals()['driver'].close()
    except:
        pass

# 2. Inputs
user_counts = [1000, 10000, 50000]
trip_counts = [10000, 50000, 100000]
events_options = [0, 2, 5, 10]
num_stations = 120

#3. Clear (Function)
def clear_graph(tx):
    print("در حال پاکسازی دیتابیس گراف...")
    tx.run("MATCH (n) DETACH DELETE n")


# 4. Random station
def insert_stations(tx, n_stations):
    print(f"is creating {n_stations} random station...")
    for i in range(1, n_stations + 1):
        city = fake.city()
        station_name = f"station_{city}_{i}"
        lat = float(fake.latitude())
        lon = float(fake.longitude())

        tx.run("""
            MERGE (s:Station {station_id: $id})
            ON CREATE SET s.name_station = $name, s.city_station = $city,
                          s.maximum_capacity = $cap, s.latitude = $lat, s.longitude = $lon
        """, id=i, name=station_name, city=city, cap=random.randint(5, 1000), lat=lat, lon=lon)

#5.Main function of simulation and combined routing (user, trip, event)
def execute_simulation_round(tx, n_users, n_trips, n_events_per_trip, num_stations):
    # a. insert users
    user_ids = []
    for i in range(1, n_users + 1):
        u_id = f"U{i}"
        user_ids.append(u_id)
        tx.run("""
            CREATE (:User {user_id: $u_id, name_user: $name, surname_user: $surname,
                          birthdate: $bdate, country_user_origin: $country})
        """, u_id=u_id, name=fake.first_name(), surname=fake.last_name(),
            bdate=str(fake.date_of_birth(minimum_age=18, maximum_age=70)), country="Italy")

    #b. insert trips and connection to stations and users
    event_types = ['Delays', 'Battery', 'GPS', 'Errors']
    for j in range(1, n_trips + 1):
        t_id = f"T{j}"
        selected_user = random.choice(user_ids)
        start_station = random.randint(1, num_stations)
        end_station = random.randint(1, num_stations)

        start_time = fake.date_time_between(start_date='-30d', end_date='now')
        end_time = start_time + timedelta(hours=random.randint(1, 5))
        cost = round(random.uniform(5.0, 50.0), 2)

        # Create a trip and physical graphic relationships
        tx.run("""
            MATCH (u:User {user_id: $u_id})
            MATCH (sStart:Station {station_id: $s_start})
            MATCH (sEnd:Station {station_id: $s_end})
            CREATE (t:Trip {trip_id: $t_id, start_time: $s_time, end_time: $e_time, total_cost: $cost})
            CREATE (u)-[:PERFORMED]->(t)
            CREATE (t)-[:STARTS_AT]->(sStart)
            CREATE (t)-[:ENDS_AT]->(sEnd)
        """, u_id=selected_user, s_start=start_station, s_end=end_station,
             t_id=t_id, s_time=start_time.isoformat(), e_time=end_time.isoformat(), cost=cost)

        # c. insert events in graph and connection them to trip
        for e_idx in range(n_events_per_trip):
            e_id = f"E_{t_id}_{e_idx+1}"
            e_time = fake.date_time_between(start_date=start_time, end_date=end_time)

            tx.run("""
                MATCH (t:Trip {trip_id: $t_id})
                CREATE (e:Event {event_id: $e_id, timestamp_event: $e_time, event_type: $e_type})
                CREATE (t)-[:TRIGGERED]->(e)
            """, t_id=t_id, e_id=e_id, e_time=e_time.isoformat(), e_type=random.choice(event_types))

# Main Loop
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

round_num = 1
with driver.session() as session:
    # توجه: برای دیتابیس ابری رایگان Aura محدودیت حجم وجود دارد (حداکثر ۵۰ هزار گره و رابطه).
    # به همین دلیل در تست ابتدا با مقادیر کوچک صحت کارکرد حلقه‌ها را بسنج.
    #The values for testing
    for n_users in [100, 500]:
        for n_trips in [200, 1000]:
            for events in [0, 2]:
                print(f"\nExecution Round #:{round_num}")
                print("------------------------------------------------------------")

                #Clear
                session.execute_write(clear_graph)
                session.execute_write(insert_stations, num_stations)
                session.execute_write(execute_simulation_round, n_users, n_trips, events, num_stations)

                round_num += 1

driver.close()
print("successfully finished!")