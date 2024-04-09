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
    green_potions_amt = 0
    volume_potions = 0
    for potions in potions_delivered:
        green_potions_amt += potions.quantity
        volume_potions += (potions.quantity * 100)

    with db.engine.begin() as connection:
        prev_green_ml = (connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone())[0]

    with db.engine.begin() as connection:
        prev_green_potions = (connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone())[0]

    new_ml = prev_green_ml-volume_potions
    new_potions = prev_green_potions+green_potions_amt

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :new_ml, num_green_potions = :new_potions"),
        {"new_ml": new_ml, "new_potions": new_potions})

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

    potion_amt = prev_green_ml//100
    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": potion_amt,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())