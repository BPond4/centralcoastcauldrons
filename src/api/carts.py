from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
            cur_time = connection.execute(sqlalchemy.text("SELECT MAX(id) FROM timestamps")).fetchone()[0]
            cust_id = connection.execute(sqlalchemy.text("INSERT INTO customers (name, level, class) VALUES (:name, :level, :class) RETURNING customer_id"),
                                {"name": new_cart.customer_name, "level": new_cart.level, "class": new_cart.character_class}).fetchone()[0]
            cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id, time_id) VALUES (:customer_id, :time_id) RETURNING id"),
                               {"customer_id":cust_id, "time_id":cur_time}).fetchone()[0]
            
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
            potion_info = connection.execute(sqlalchemy.text("SELECT id, price FROM potions WHERE sku = :item_sku"), {"item_sku":item_sku}).fetchone()
            prod_id = potion_info[0]
            price = potion_info[1]*cart_item.quantity
            cust_id = connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, product_id, quantity, gold_paid) VALUES (:cart_id, :product_id, :quantity, :gold_paid)"),
                                {"cart_id": cart_id, "product_id": prod_id, "quantity": cart_item.quantity, "gold_paid":price})

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    gold_gained = 0
    total_potions = 0
    with db.engine.begin() as connection:
            rows = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id})
            if rows:
                for cart_item in rows:
                    total_potions += cart_item.quantity
                    gold_gained += (connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE id = :prod_id"),{"prod_id": cart_item.product_id}).fetchone()[0])*cart_item.quantity
                
            else:
                raise Exception("No items in cart")

    return {"total_potions_bought": total_potions, "total_gold_paid": gold_gained}
