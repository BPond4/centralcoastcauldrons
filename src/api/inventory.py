from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        mls = connection.execute(sqlalchemy.text("SELECT SUM(red_ml), SUM(green_ml), SUM(blue_ml), SUM(dark_ml) FROM ml_ledgers")).fetchone()
        red_ml = mls[0]
        green_ml = mls[1]
        blue_ml = mls[2]
        dark_ml = mls[3]

        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers")).fetchone()[0]

        gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_diff) FROM gold_ledgers")).fetchone()[0]
        
    return {"number_of_potions": total_potions, "green_ml_in_barrels": green_ml, "blue_ml_in_barrels": blue_ml, "red_ml_in_barrels": red_ml, "dark_ml_in_barrels": dark_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
