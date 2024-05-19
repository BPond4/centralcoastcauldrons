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
    with db.engine.begin() as connection:
        pot_cap = (connection.execute(sqlalchemy.text("SELECT potion_capacity FROM capacity")).fetchone())[0]
        ml_cap = (connection.execute(sqlalchemy.text("SELECT ml_capacity FROM capacity")).fetchone())[0]
        cur_gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_diff) FROM gold_ledgers")).fetchone()[0]
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers")).fetchone()[0]
        mls = connection.execute(sqlalchemy.text("SELECT SUM(red_ml), SUM(green_ml), SUM(blue_ml), SUM(dark_ml) FROM ml_ledgers")).fetchone()
        total_ml = mls[0]+mls[1]+mls[2]+mls[3]

    potion_increase = 0
    ml_increase = 0
    if((total_potions/pot_cap>0.75) and (cur_gold>2000)):
        if(cur_gold>5000):
            potion_increase = 2
            cur_gold-=2000
        else:
            potion_increase = 1
            cur_gold -= 1000

    if((total_ml/ml_cap>0.75) and (cur_gold>2000)):
        if(cur_gold>5000):
            ml_increase = 2
            cur_gold-=2000
        else:
            ml_increase = 1
            cur_gold -= 1000

    print(f"Buying {potion_increase} potion capacity and {ml_increase} ml capacity")
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
    description = "Increasing capacity"
    count = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE capacity SET potion_capacity = potion_capacity + :pot_cap, ml_capacity = ml_capacity + :ml_cap"),
                           {"pot_cap": capacity_purchase.potion_capacity*50, "ml_cap": capacity_purchase.ml_capacity*10000})
        cur_time = connection.execute(sqlalchemy.text("SELECT MAX(id) FROM timestamps")).fetchone()[0]
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description, timestamp) VALUES (:description, :time_purchased) RETURNING id"),
                               {"description":description, "time_purchased":cur_time}).fetchone()[0]
        result = connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (transaction_id, gold_diff) VALUES (:transaction_id, :gold_diff)"),
                           {"transaction_id":transaction_id, "gold_diff":(-1000*count)})

    return result
