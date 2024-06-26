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
    description = (f"barrels delivered: {barrels_delivered}")
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
        
        green_ml+=(barrel.ml_per_barrel)*(barrel.potion_type[1])*(barrel.quantity)
        red_ml += (barrel.ml_per_barrel)*(barrel.potion_type[0])*(barrel.quantity)
        blue_ml += (barrel.ml_per_barrel)*(barrel.potion_type[2])*(barrel.quantity)
        dark_ml += (barrel.ml_per_barrel)*(barrel.potion_type[3])*(barrel.quantity)
        cost+= barrel.price*barrel.quantity

    print(f"gold_paid: {cost} red_ml: {red_ml} green_ml: {green_ml} blue_ml: {blue_ml} dark_ml: {dark_ml}")
    
    with db.engine.begin() as connection:
        cur_time = connection.execute(sqlalchemy.text("SELECT MAX(id) FROM timestamps")).fetchone()[0]
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description, timestamp) VALUES (:description, :time_purchased) RETURNING id"),
                               {"description":description, "time_purchased":cur_time}).fetchone()[0]
        result = connection.execute(sqlalchemy.text("INSERT INTO ml_ledgers (transaction_id, red_ml, green_ml, blue_ml, dark_ml) VALUES (:transaction_id, :red_ml, :green_ml, :blue_ml, :dark_ml)"),
                           {"transaction_id":transaction_id, "red_ml":red_ml, "green_ml":green_ml, "blue_ml":blue_ml, "dark_ml":dark_ml})
        result = connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (transaction_id, gold_diff) VALUES (:transaction_id, :gold_diff)"),
                           {"transaction_id":transaction_id, "gold_diff":-cost})

    return result

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        budget = connection.execute(sqlalchemy.text("SELECT SUM(gold_diff) FROM gold_ledgers")).fetchone()[0]
        ml_cap = connection.execute(sqlalchemy.text("SELECT ml_capacity FROM capacity")).fetchone()[0]

        barrels_bought = connection.execute(sqlalchemy.text("SELECT SUM(red_ml), SUM(green_ml), SUM(blue_ml), SUM(dark_ml) FROM ml_ledgers")).fetchone()


        red_ml = barrels_bought[0]
        green_ml = barrels_bought[1]
        blue_ml = barrels_bought[2]
        dark_ml = barrels_bought[3]



    purchase_plan = []
    blue_barrel_bought = False
    red_barrel_bought = False
    green_barrel_bought = False
    dark_barrel_bought = False
    total_ml = green_ml+blue_ml+red_ml+dark_ml
    barrel_size = 2500
    if ml_cap-total_ml<10000:
        barrel_size = 500
    iterations = 0
    while((total_ml<(ml_cap - 500)) and budget>=100 and iterations<20):
        if(iterations>10 and (ml_cap-total_ml<10000 or ((blue_barrel_bought == False) and (red_barrel_bought == False) and (green_barrel_bought == False)))):
            barrel_size = 500
        iterations+=1
        
        for barrel in wholesale_catalog:
            if(red_ml == 0 or (red_ml<=blue_ml and red_ml<=green_ml) and (not red_barrel_bought)):
                if((barrel.potion_type[0]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>barrel_size and ((barrel.ml_per_barrel+total_ml) <ml_cap)):
                    sku = barrel.sku
                    amt = 1
                    max_amt = min(barrel.quantity,(ml_cap-total_ml)//barrel.ml_per_barrel)
                    if(max_amt>3):
                        amt = 2
                    purchase_plan.append( 
                        {
                            "sku": sku,
                            "quantity": amt,
                        }
                    )
                    budget -= barrel.price * amt
                    total_ml+=barrel.ml_per_barrel*amt
                    red_ml += barrel.ml_per_barrel*amt
                    red_barrel_bought = True
            elif(green_ml == 0 or (green_ml<=blue_ml and green_ml<=red_ml) and (not green_barrel_bought)):
                if((barrel.potion_type[1]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>barrel_size and ((barrel.ml_per_barrel+total_ml) <ml_cap)):
                    sku = barrel.sku
                    amt = 1
                    max_amt = min(barrel.quantity,(ml_cap-total_ml)//barrel.ml_per_barrel)
                    if(max_amt>3):
                        amt = 2
                    purchase_plan.append( 
                        {
                            "sku": sku,
                            "quantity": amt,
                        }
                    )
                    budget -= barrel.price * amt
                    total_ml+=barrel.ml_per_barrel*amt
                    green_ml += barrel.ml_per_barrel*amt
                    green_barrel_bought = True
            elif(blue_ml == 0 or (blue_ml<=red_ml and blue_ml<=green_ml) and (not blue_barrel_bought)):
                if((barrel.potion_type[2]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>barrel_size and ((barrel.ml_per_barrel+total_ml) <ml_cap)):
                    sku = barrel.sku
                    amt = 1
                    max_amt = min(barrel.quantity,(ml_cap-total_ml)//barrel.ml_per_barrel)
                    if(max_amt>3):
                        amt = 2
                    purchase_plan.append( 
                        {
                            "sku": sku,
                            "quantity": amt,
                        }
                    )
                    budget -= barrel.price * amt
                    total_ml+=barrel.ml_per_barrel*amt
                    blue_ml += barrel.ml_per_barrel*amt
                    blue_barrel_bought = True
            elif(dark_ml<=red_ml and dark_ml<green_ml and dark_ml<blue_ml) and (not dark_barrel_bought):
                if((barrel.potion_type[3]>=1) and (barrel.price<=budget) and barrel.ml_per_barrel>barrel_size and ((barrel.ml_per_barrel+total_ml) <ml_cap)):
                    sku = barrel.sku
                    amt = 1
                    max_amt = min(barrel.quantity,(ml_cap-total_ml)//barrel.ml_per_barrel)
                    if(max_amt>3):
                        amt = 2
                    purchase_plan.append( 
                        {
                            "sku": sku,
                            "quantity": amt,
                        }
                    )
                    budget -= barrel.price * amt
                    total_ml+=barrel.ml_per_barrel*amt
                    dark_ml+=barrel.ml_per_barrel*amt
                    dark_barrel_bought = True

        if (red_ml<blue_ml) and (red_ml<green_ml) and (red_ml<dark_ml):
            red_barrel_bought = False
        elif (green_ml<blue_ml) and (green_ml<red_ml) and (green_ml<dark_ml):
            green_barrel_bought = False
        elif (blue_ml<red_ml) and (blue_ml<green_ml) and (blue_ml<dark_ml):
            blue_barrel_bought = False
        elif (dark_ml<red_ml) and (dark_ml<green_ml) and (dark_ml<blue_ml):
            dark_barrel_bought = False
        
 
    print(purchase_plan)
    return purchase_plan

