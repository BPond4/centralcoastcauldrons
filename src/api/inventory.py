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
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, num_green_ml, num_blue_potions, num_blue_ml, num_red_potions, num_red_ml, gold FROM global_inventory")).fetchone()
        
        green_potions = result[0]
        green_ml = result[1]
        blue_potions = result[2]
        blue_ml = result[3]
        red_potions = result[4]
        red_ml = result[5]
        gold = result[6]
        
    return {"number_of_green_potions": green_potions, "green_ml_in_barrels": green_ml, "number_of_blue_potions": blue_potions, "blue_ml_in_barrels": blue_ml, "number_of_red_potions": red_potions, "red_ml_in_barrels": red_ml, "gold": gold}

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
