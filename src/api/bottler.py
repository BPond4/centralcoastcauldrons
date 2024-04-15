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
    green_potions_amt = 0
    red_potions_amt = 0
    blue_potions_amt = 0
    volume_green = 0
    volume_red = 0
    volume_blue = 0
    for potions in potions_delivered:
        if(potions.potion_type[0]==100):
            red_potions_amt += potions.quantity
        elif(potions.potion_type[1]==100):
            green_potions_amt += potions.quantity
        elif(potions.potion_type[2]==100):
            blue_potions_amt += potions.quantity

        volume_red += (potions.quantity * potions.potion_type[0])
        volume_green += (potions.quantity * potions.potion_type[1])
        volume_blue += (potions.quantity * potions.potion_type[2])

    with db.engine.begin() as connection:
        prev_green_ml = (connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone())[0]
        prev_green_potions = (connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone())[0]

        prev_red_ml = (connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).fetchone())[0]
        prev_red_potions = (connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).fetchone())[0]

        prev_blue_ml = (connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).fetchone())[0]
        prev_blue_potions = (connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).fetchone())[0]

    new_green_ml = prev_green_ml-volume_green
    new_green_potions = prev_green_potions+green_potions_amt

    new_red_ml = prev_red_ml-volume_red
    new_red_potions = prev_red_potions+red_potions_amt

    new_blue_ml = prev_blue_ml-volume_blue
    new_blue_potions = prev_blue_potions+blue_potions_amt

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :new_green_ml, num_green_potions = :new_green_potions, num_red_ml = :new_red_ml, num_red_potions = :new_red_potions, num_blue_ml = :new_blue_ml, num_blue_potions = :new_blue_potions"),
        {"new_green_ml": new_green_ml, "new_green_potions": new_green_potions, "new_red_ml": new_red_ml, "new_red_potions": new_red_potions, "new_blue_ml": new_blue_ml, "new_blue_potions": new_blue_potions})

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

    green_potion_amt = prev_green_ml//100
    blue_potion_amt = prev_blue_ml//100
    red_potion_amt = prev_red_ml//100
    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": green_potion_amt,
            },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": blue_potion_amt,
            },
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": red_potion_amt,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())