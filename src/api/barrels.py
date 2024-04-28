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

    # with db.engine.begin() as connection:
    #     try:
    #         connection.execute(
    #             sqlalchemy.text(
    #                 "INSERT INTO processed (job_id, type) VALUES (:order_id, 'barrels')"),
    #                 [{"order_id": order_id}]
    #         )
    #     except IntegrityError as e:
    #         return "OK"
    green_ml = 0
    red_ml = 0
    blue_ml = 0
    dark_ml = 0
    cost = 0

    

    for barrel in barrels_delivered:
        if(barrel.potion_type!= [1,0,0,0] and barrel.potion_type != [0,1,0,0] and barrel.potion_type!= [0,0,1,0] and barrel.potion_type != [0,0,0,1]):
            raise Exception("Invalid potion type")
        
        green_ml+=(barrel.ml_per_barrel)*(barrel.potion_type[1])
        red_ml += (barrel.ml_per_barrel)*(barrel.potion_type[0])
        blue_ml += (barrel.ml_per_barrel)*(barrel.potion_type[2])
        dark_ml += (barrel.ml_per_barrel)*(barrel.potion_type[3])
        cost+= barrel.price

    print(f"gold_paid: {cost} red_ml: {red_ml} green_ml: {green_ml} blue_ml: {blue_ml} dark_ml: {dark_ml}")
    
    with db.engine.begin() as connection:
        prev_green_ml = (connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone())[0]
        prev_red_ml = (connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).fetchone())[0]
        prev_blue_ml = (connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).fetchone())[0]
        prev_dark_ml = (connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).fetchone())[0]
        prev_gold = (connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())[0]

    new_green_ml = green_ml+prev_green_ml
    new_red_ml = red_ml+prev_red_ml
    new_blue_ml = blue_ml+prev_blue_ml
    new_dark_ml = dark_ml+prev_dark_ml
    new_gold = prev_gold-cost
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :new_green_ml, num_red_ml = :new_red_ml, num_blue_ml = :new_blue_ml, num_dark_ml = :new_dark_ml, gold = :new_gold"),
        {"new_green_ml": new_green_ml,"new_red_ml": new_red_ml, "new_blue_ml": new_blue_ml, "new_dark_ml": new_dark_ml, "new_gold": new_gold})
    
    print(new_red_ml)
    print(new_green_ml)
    print(new_blue_ml)
    print(new_dark_ml)

    return result

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).fetchone()[0]
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone()[0]
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).fetchone()[0]
        dark_ml = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).fetchone()[0]

        budget = (connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())[0]
        ml_cap = (connection.execute(sqlalchemy.text("SELECT ml_capacity FROM capacity")).fetchone())[0]

    purchase_plan = []
    blue_barrel_bought = False
    red_barrel_bought = False
    green_barrel_bought = False
    dark_barrel_bought = False
    total_ml = green_ml+blue_ml+red_ml+dark_ml

    for barrel in wholesale_catalog:
        if(green_ml == 0 or (green_ml<=blue_ml and green_ml<=red_ml) or red_barrel_bought or blue_barrel_bought):
            if((barrel.potion_type[1]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>=500 and ((barrel.ml_per_barrel+total_ml) <ml_cap) and (not green_barrel_bought)):
                sku = barrel.sku
                
                purchase_plan.append( 
                    {
                        "sku": sku,
                        "quantity": 1,
                    }
                )
                budget -= barrel.price
                total_ml+=barrel.ml_per_barrel
                green_barrel_bought = True
        elif(red_ml == 0 or (red_ml<=blue_ml and red_ml<=green_ml) or green_barrel_bought or blue_barrel_bought):
            if((barrel.potion_type[0]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>=500 and ((barrel.ml_per_barrel+total_ml) <ml_cap)and (not red_barrel_bought)):
                sku = barrel.sku
                
                purchase_plan.append( 
                    {
                        "sku": sku,
                        "quantity": 1,
                    }
                )
                budget -= barrel.price
                total_ml+=barrel.ml_per_barrel
                red_barrel_bought = True
        elif(blue_ml == 0 or (blue_ml<=red_ml and blue_ml<=green_ml) or green_barrel_bought or red_barrel_bought):
            if((barrel.potion_type[2]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>=500 and ((barrel.ml_per_barrel+total_ml) <ml_cap)and (not blue_barrel_bought)):
                sku = barrel.sku
                
                purchase_plan.append( 
                    {
                        "sku": sku,
                        "quantity": 1,
                    }
                )
                budget -= barrel.price
                total_ml+=barrel.ml_per_barrel
                blue_barrel_bought = True
        elif(dark_ml == 0 or (dark_ml<=blue_ml and dark_ml<=green_ml)):
            if((barrel.potion_type[3]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>=500 and ((barrel.ml_per_barrel+total_ml) <ml_cap)and (not dark_barrel_bought)):
                sku = barrel.sku
                
                purchase_plan.append( 
                    {
                        "sku": sku,
                        "quantity": 1,
                    }
                )
                budget -= barrel.price
                total_ml+=barrel.ml_per_barrel
                dark_barrel_bought = True
        
 
    print(purchase_plan)
    return purchase_plan

