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
        sub = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM cart_items")).fetchone()[0]
        add = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM bottler_ledgers")).fetchone()[0]
        total_potions = add-sub

        barrels_bought = connection.execute(sqlalchemy.text("SELECT SUM(gold_paid), SUM(red_ml), SUM(green_ml), SUM(blue_ml), SUM(dark_ml) FROM barrel_ledgers")).fetchone()
        potions = connection.execute(sqlalchemy.text("SELECT potion_id, num_potions FROM bottler_ledgers")).fetchall()

        gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_paid) FROM cart_items")).fetchone()[0]
        gold -= barrels_bought[0]
        red_ml = barrels_bought[1]
        green_ml = barrels_bought[2]
        blue_ml = barrels_bought[3]
        dark_ml = barrels_bought[4]

        for potion in potions:
            mls = connection.execute(sqlalchemy.text("SELECT red, green, blue, dark FROM potions WHERE id = :potion_id"),{"potion_id":potion[0]}).fetchone()
            red_ml -= (mls[0]*potion[1])
            green_ml -= (mls[1]*potion[1])
            blue_ml -= (mls[2]*potion[1])
            dark_ml -= (mls[3]*potion[1])
        
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
