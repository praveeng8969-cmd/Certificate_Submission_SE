import os
import sys
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.resource import Resource


def init_db():
    Base.metadata.create_all(bind=engine)


def seed_data(db_session=None):
    close_after = False
    if db_session is None:
        db = SessionLocal()
        close_after = True
    else:
        db = db_session

    try:
        # Seed Users
        users_data = [
            {
                "id": "U001",
                "name": "Demo User One",
                "role": "USER",
                "status": "ACTIVE",
                "phone": "9876543210"
            },
            {
                "id": "U002",
                "name": "Demo User Two",
                "role": "USER",
                "status": "ACTIVE",
                "phone": "9876543211"
            },
            {
                "id": "A001",
                "name": "Demo Administrator",
                "role": "ADMINISTRATOR",
                "status": "ACTIVE",
                "phone": "9876543212"
            }
        ]

        for u_data in users_data:
            existing_user = db.query(User).filter(User.id == u_data["id"]).first()
            if not existing_user:
                new_user = User(**u_data)
                db.add(new_user)

        # Seed Resources EXACTLY as specified
        resources_data = [
            {
                "id": "S101",
                "service_name": "Certificate Request A",
                "capacity": 10,
                "status": "ACTIVE",
                "base_value": Decimal("500.00"),
                "charge_applicable": True
            },
            {
                "id": "S102",
                "service_name": "Certificate Request B",
                "capacity": 5,
                "status": "ACTIVE",
                "base_value": Decimal("1500.00"),
                "charge_applicable": True
            },
            {
                "id": "S103",
                "service_name": "Certificate Request C",
                "capacity": 0,
                "status": "INACTIVE",
                "base_value": Decimal("0.00"),
                "charge_applicable": False
            }
        ]

        for r_data in resources_data:
            existing_resource = db.query(Resource).filter(Resource.id == r_data["id"]).first()
            if not existing_resource:
                new_resource = Resource(**r_data)
                db.add(new_resource)

        db.commit()
        print("Database seeded successfully without modifying existing requests.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    init_db()
    seed_data()
