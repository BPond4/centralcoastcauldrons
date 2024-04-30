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

    description = (f"Potions delivered: {potions_delivered}")
    print(description)
    
    with db.engine.begin() as connection:
        cur_time = connection.execute(sqlalchemy.text("SELECT MAX(id) FROM timestamps")).fetchone()[0]
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description, timestamp) VALUES (:description, :timestamp) RETURNING id"),
                               {"description":description, "timestamp":cur_time}).fetchone()[0]
        
        for potions in potions_delivered:
            pot_id = connection.execute(sqlalchemy.text("SELECT id FROM potions WHERE red = :red AND green = :green AND blue = :blue AND dark = :dark"),
                                        {"red": potions.potion_type[0], "green": potions.potion_type[1], "blue": potions.potion_type[2], "dark": potions.potion_type[3]}).fetchone()[0]
            result = connection.execute(sqlalchemy.text("INSERT INTO potion_ledgers (transaction_id, potion_id, num_potions) VALUES (:transaction_id, :potion_id, :num_potions)"),
                           {"transaction_id":transaction_id, "potion_id": pot_id, "num_potions":potions.quantity})
            result = connection.execute(sqlalchemy.text("INSERT INTO ml_ledgers (transaction_id, red_ml, green_ml, blue_ml, dark_ml) VALUES (:transaction_id, :red_ml, :green_ml, :blue_ml, :dark_ml)"),
                           {"transaction_id":transaction_id, "red_ml": -(potions.potion_type[0]*potions.quantity), "green_ml":-(potions.potion_type[1]*potions.quantity), "blue_ml":-(potions.potion_type[2]*potions.quantity), "dark_ml":-(potions.potion_type[3]*potions.quantity)})

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

            cur_pots = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers")).fetchone()[0]
            
            white_pots = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers WHERE potion_id = 11")).fetchone()[0]
            yellow_pots = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers WHERE potion_id = 5")).fetchone()[0]
            teal_pots = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers WHERE potion_id = 8")).fetchone()[0]
            purple_pots = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers WHERE potion_id = 6")).fetchone()[0]
            if(not white_pots):
                white_pots=0
            if(not yellow_pots):
                yellow_pots =0
            if(not teal_pots):
                teal_pots=0
            if(not purple_pots):
                purple_pots=0

            barrels_bought = connection.execute(sqlalchemy.text("SELECT SUM(red_ml), SUM(green_ml), SUM(blue_ml), SUM(dark_ml) FROM ml_ledgers")).fetchone()

            prev_red_ml = barrels_bought[0]
            prev_green_ml = barrels_bought[1]
            prev_blue_ml = barrels_bought[2]
            prev_dark_ml = barrels_bought[3]

            pot_cap = (connection.execute(sqlalchemy.text("SELECT potion_capacity FROM capacity")).fetchone())[0]


    
    potion_list = []
    flag = True
    while cur_pots<pot_cap and (prev_blue_ml>100 or prev_red_ml>100 or prev_green_ml>100) and flag:
        if(prev_blue_ml>=34 and prev_red_ml>=33 and prev_green_ml>=33 and white_pots < 10):
            amt = min(min(5,pot_cap-cur_pots),min((prev_blue_ml//34),min((prev_red_ml//33),(prev_green_ml//33))))
            if(amt>0):
                potion_list.append(
                    {
                        "potion_type": [33,33,34,0],
                        "quantity": amt,
                    }
                )
                cur_pots+=amt
                white_pots+=amt
                prev_green_ml -= amt*33
                prev_blue_ml -= amt*34
                prev_red_ml -= amt*33
        elif(prev_red_ml>100 and prev_blue_ml>100 and purple_pots < 10):
            amt = min(min(5,pot_cap-cur_pots),min(prev_blue_ml//50,prev_red_ml//50) - 1)
            if(amt>0):
                potion_list.append(
                    {
                        "potion_type": [50,0,50,0],
                        "quantity": amt,
                    }
                )
                cur_pots+=amt
                purple_pots+=amt
                prev_blue_ml -= amt*50
                prev_red_ml -= amt*50
        elif(prev_green_ml>100 and prev_blue_ml>100 and teal_pots < 10):
            amt = min(min(5,pot_cap-cur_pots),min(prev_blue_ml//50,prev_green_ml//50) - 1)
            if(amt>0):
                potion_list.append(
                    {
                        "potion_type": [0,50,50,0],
                        "quantity": amt,
                    }
                )
                cur_pots+=amt
                teal_pots+=amt
                prev_green_ml -= amt * 50
                prev_blue_ml -= amt * 50
        elif(prev_red_ml>100 and prev_green_ml>100 and yellow_pots < 10):
            amt = min(min(5,pot_cap-cur_pots),min(prev_green_ml//50,prev_red_ml//50) - 1)
            if(amt>0):
                potion_list.append(
                    {
                        "potion_type": [50,50,0,0],
                        "quantity": amt,
                    }
                )
                cur_pots+=amt
                yellow_pots+=amt
                prev_green_ml -= amt*50
                prev_red_ml -= amt*50
        else:
            flag = False
            if(prev_red_ml>=200):
                amt = min(min(10,pot_cap-cur_pots),(prev_red_ml//100)-1)
                if(amt>0):
                    potion_list.append(
                        {
                            "potion_type": [100,0,0,0],
                            "quantity": amt,
                        }
                    )
                    cur_pots+=amt
                    prev_red_ml -= amt*100
            if(prev_green_ml>=200):
                amt = min(min(10,pot_cap-cur_pots),(prev_green_ml//100)-1)
                if(amt>0):
                    potion_list.append(
                        {
                            "potion_type": [0,100,0,0],
                            "quantity": amt,
                        }
                    )
                    cur_pots+=amt
                    prev_green_ml -= amt*100
            
            if(prev_blue_ml>=200):
                amt = min(min(10,pot_cap-cur_pots),(prev_blue_ml//100)-1)
                if(amt>0):
                    potion_list.append(
                        {
                            "potion_type": [0,0,100,0],
                            "quantity": amt,
                        }
                    )
                    cur_pots+=amt
                    prev_blue_ml -= amt*100
            
            if(prev_dark_ml>=200):
                amt = min(min(10,pot_cap-cur_pots),(prev_dark_ml//100)-1)
                if(amt>0):
                    potion_list.append(
                        {
                            "potion_type": [0,0,0,100],
                            "quantity": amt,
                        }
                    )
                    cur_pots+=amt
                    prev_dark_ml -= amt*100
            
        
    print(potion_list)
    return potion_list

if __name__ == "__main__":
    print(get_bottle_plan())