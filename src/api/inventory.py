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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
        
        green_potions = result['num_green_potions']
        green_ml = result['num_green_ml']
        blue_potions = result['num_blue_potions']
        blue_ml = result['num_blue_ml']
        red_potions = result['num_red_potions']
        red_ml = result['num_red_ml']
        dark_potions = result['num_dark_potions']
        dark_ml = result['num_dark_ml']
        gold = result['gold']
        
    return {"number_of_green_potions": green_potions, "green_ml_in_barrels": green_ml, "number_of_blue_potions": blue_potions, "blue_ml_in_barrels": blue_ml, "number_of_red_potions": red_potions, "red_ml_in_barrels": red_ml, "number_of_dark_potions": dark_potions, "dark_ml_in_barrels": dark_ml, "gold": gold}

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
