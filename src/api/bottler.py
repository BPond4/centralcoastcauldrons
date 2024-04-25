from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(potions_delivered)
    new_red_ml = 0
    new_green_ml = 0
    new_blue_ml = 0
    new_dark_ml = 0
    new_total_potions = 0
    for potions in potions_delivered:
        new_total_potions += potions.quantity

        new_red_ml += (potions.quantity * potions.potion_type[0])
        new_green_ml += (potions.quantity * potions.potion_type[1])
        new_blue_ml += (potions.quantity * potions.potion_type[2])
        new_dark_ml += (potions.quantity * potions.potion_type[3])
        with db.engine.begin() as connection:
            result = (connection.execute(sqlalchemy.text("UPDATE potions SET quantity = quantity + :quant WHERE blue = :blue_val AND red = :red_val AND green = :green_val AND dark = :dark_val"),
                                        {"quant": potions.quantity, "blue_val": potions.potion_type[2], "red_val": potions.potion_type[0], "green_val": potions.potion_type[1], "dark_val":potions.potion_type[3]}))

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_green_ml = num_green_ml - :new_green_ml, num_red_ml = num_red_ml - :new_red_ml, num_blue_ml = num_blue_ml - :new_blue_ml,  num_dark_ml = num_dark_ml - :new_dark_ml, num_potions = num_potions + :new_potions"),
        {"new_green_ml": new_green_ml, "new_red_ml": new_red_ml, "new_blue_ml": new_blue_ml, "new_dark_ml": new_dark_ml, "new_potions": new_total_potions})

    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return result

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        prev_green_ml = (connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone())[0]
        prev_blue_ml = (connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).fetchone())[0]
        prev_red_ml = (connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).fetchone())[0]
        prev_dark_ml = (connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).fetchone())[0]
        cur_gold = (connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())[0]

    
    potion_list = []
    while len(potion_list)<10:
        if(prev_blue_ml>=34 and prev_red_ml>=33 and prev_green_ml>=33):
            amt = min(10-len(potion_list),min((prev_blue_ml//34),min((prev_red_ml//33),(prev_green_ml//33))))
            potion_list.append(
                {
                    "potion_type": [33,33,34,0],
                    "quantity": amt,
                }
            )
            prev_green_ml -= amt*33
            prev_blue_ml -= amt*34
            prev_red_ml -= amt*33
        elif(prev_red_ml>50 and prev_blue_ml>50):
            amt = min(10-len(potion_list),min(prev_blue_ml//50,prev_red_ml//50) - 1)
            potion_list.append(
                {
                    "potion_type": [50,0,50,0],
                    "quantity": amt,
                }
            )
            prev_blue_ml -= amt*50
            prev_red_ml -= amt*50
        elif(prev_green_ml>50 and prev_blue_ml>50):
            amt = min(10-len(potion_list),min(prev_blue_ml//50,prev_green_ml//50) - 1)
            potion_list.append(
                {
                    "potion_type": [0,50,50,0],
                    "quantity": amt,
                }
            )
            prev_green_ml -= amt * 50
            prev_blue_ml -= amt * 50
        elif(prev_red_ml>50 and prev_green_ml>50):
            amt = min(10-len(potion_list),min(prev_green_ml//50,prev_red_ml//50) - 1)
            potion_list.append(
                {
                    "potion_type": [50,50,0,0],
                    "quantity": amt,
                }
            )
            prev_green_ml -= amt*50
            prev_red_ml -= amt*50
        else:
            if(prev_red_ml>=200):
                amt = min(10-len(potion_list),(prev_red_ml//100)-1)
                potion_list.append(
                    {
                        "potion_type": [100,0,0,0],
                        "quantity": amt,
                    }
                )
                prev_red_ml -= amt*100
            if(prev_green_ml>=200):
                amt = min(10-len(potion_list),(prev_green_ml//100)-1)
                potion_list.append(
                    {
                        "potion_type": [0,100,0,0],
                        "quantity": amt,
                    }
                )
                prev_green_ml -= amt*100
            
            if(prev_blue_ml>=200):
                amt = min(10-len(potion_list),(prev_blue_ml//100)-1)
                potion_list.append(
                    {
                        "potion_type": [0,0,100,0],
                        "quantity": amt,
                    }
                )
                prev_blue_ml -= amt*100
            
            if(prev_dark_ml>=200):
                amt = min(10-len(potion_list),(prev_dark_ml//100)-1)
                potion_list.append(
                    {
                        "potion_type": [0,0,0,100],
                        "quantity": amt,
                    }
                )
                prev_dark_ml -= amt*100
            break
    
    return potion_list

if __name__ == "__main__":
    print(get_bottle_plan())