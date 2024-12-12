import time
import random
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from models import ItemModel, StoreModel, UserModel
from db import db
from app import create_app
from tabulate import tabulate

DATABASE_URL = "postgresql://storesdb_owner:5l**********@ep-fragrant-firefly-a5wdov3w.us-east-2.aws.neon.tech/storesdb?sslmode=require"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def recreate_tables():
    db.drop_all()
    db.create_all()

def populate_db(num_records):
    # Create stores
    stores = [StoreModel(name=f"Store {i}") for i in range(num_records)]
    session.bulk_save_objects(stores)
    session.commit()

    # Create items
    items = [ItemModel(name=f"Item {i}", price=random.uniform(1, 100), store_id=random.randint(1, num_records)) for i in range(num_records)]
    session.bulk_save_objects(items)
    session.commit()

def measure_query_time(query_func, *args):
    start_time = time.time()
    query_func(*args)
    end_time = time.time()
    return end_time - start_time

def select_query():
    session.query(ItemModel).all()

def update_query():
    stmt = update(ItemModel).values(price=random.uniform(1, 100))
    session.execute(stmt)
    session.commit()

def insert_query(num_records):
    items = [ItemModel(name=f"New Item {i}", price=random.uniform(1, 100), store_id=random.randint(1, num_records)) for i in range(num_records)]
    session.bulk_save_objects(items)
    session.commit()

def delete_query():
    session.query(ItemModel).delete()
    session.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        results = []
        for num_records in [1000, 10000, 100000, 1000000]:
            print(f"Recreating tables...")
            recreate_tables()

            print(f"Populating database with {num_records} records...")
            populate_db(num_records)

            print(f"Measuring query times for {num_records} records...")
            select_time = measure_query_time(select_query)
            update_time = measure_query_time(update_query)
            insert_time = measure_query_time(insert_query, num_records)
            delete_time = measure_query_time(delete_query)

            results.append([num_records, select_time, update_time, insert_time, delete_time])

        print(tabulate(results, headers=["Number of Records", "Select (s)", "Update (s)", "Insert (s)", "Delete (s)"], tablefmt="pretty"))