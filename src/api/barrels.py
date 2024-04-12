from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    green_ml = 0
    cost = 0
    for barrel in barrels_delivered:
        green_ml+=barrel.ml_per_barrel
        cost+= barrel.price
    
    with db.engine.begin() as connection:
        prev_green_ml = (connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone())[0]
        
    with db.engine.begin() as connection:
        prev_gold = (connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())[0]

    new_ml = green_ml+prev_green_ml
    new_gold = prev_gold-cost
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :new_ml, gold = :new_gold"),
        {"new_ml": new_ml, "new_gold": new_gold})
    return result

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        green_potions = (connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone())[0]

    
    if(green_potions<10):
        for barrel in wholesale_catalog:
            if barrel.potion_type[1]==100:
                sku = barrel.sku
                return [
                    {
                        "sku": sku,
                        "quantity": 1,
                    }
                ]
            else:
                return[
                
                ]
    

