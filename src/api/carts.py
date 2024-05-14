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
    
    
    sql_query = """SELECT ci.quantity, ci.gold_paid, p.sku, c.name, t.time FROM cart_items ci JOIN potions p ON ci.product_id = p.id JOIN carts ca ON ci.cart_id = ca.id JOIN customers c ON ca.customer_id = c.customer_id JOIN timestamps t ON ca.time_id = t.id WHERE c.name LIKE :name AND p.sku LIKE :potionsku ORDER BY {order_col} {sort_direction}"""
    
    correct_col = ""
    if(sort_col.value == "timestamp"):
         correct_col = "t.time"
    elif(sort_col.value == "customer_name"):
         correct_col = "c.name"
    elif(sort_col.value == "item_sku"):
         correct_col = "p.sku"
    elif(sort_col.value == "line_item_total"):
         correct_col = "ci.gold_paid"
    # Define the parameters for the query
    params = {
        "name": f'%{customer_name}%',
        "potionsku": f'%{potion_sku}%',
        "order_col": correct_col,  # This should be the column name to order by
        "sort_direction": sort_order.upper()  # Convert sort_order to uppercase ('ASC' or 'DESC')
    }

    # Construct the formatted SQL query with placeholders filled
    formatted_sql_query = sql_query.format(order_col=params["order_col"], sort_direction=params["sort_direction"])
    

    # Execute the query using connection.execute() with sqlalchemy.text()
    with db.engine.begin() as connection:
        rows = connection.execute(sqlalchemy.text(formatted_sql_query), params).fetchall()
    
    rowlist = []
    i = 0
    for row in rows:
         
         i+=1
         rowlist.append({
              "line_item_id": i,
              "item_sku": f"{row[0]} {row[2]}",
              "customer_name": row[3],
              "line_item_total": row[1],
              "timestamp": row[4]
         })
    if search_page == "":
         previous = ""
         pagenum = 1
    elif int(search_page)<5:
         previous = ""
         pagenum = int(search_page)
    else:
         previous = str(int(search_page)-5)
         pagenum = int(search_page)

    if search_page == "":
         if(len(rowlist)<=5):
              next = ""
         else:
              next= 5
    elif(len(rowlist)>(int(search_page)+5)):
         next = str(int(search_page)+5)
    else:
         next = ""

    returnlist = []
    count = 0
    while count<5 and (pagenum<=len(rowlist)):
         count+=1
         returnlist.append(rowlist[pagenum-1])
         pagenum+=1
    return {
        "previous": previous,
        "next": next,
        "results": returnlist
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
    description = (f"Cart Checkout with id: {cart_id}")
    with db.engine.begin() as connection:
            cur_time = connection.execute(sqlalchemy.text("SELECT MAX(id) FROM timestamps")).fetchone()[0]
            transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description, timestamp) VALUES (:description, :timestamp) RETURNING id"),
                               {"description":description, "timestamp":cur_time}).fetchone()[0]
            rows = connection.execute(sqlalchemy.text("SELECT product_id, quantity, gold_paid FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id}).fetchall()
            if rows:
                for cart_item in rows:
                    total_potions += cart_item[1]
                    gold_gained += cart_item[2]
                    potion_id = cart_item[0]
                    connection.execute(sqlalchemy.text("INSERT INTO potion_ledgers (transaction_id, potion_id, num_potions) VALUES (:transaction_id, :potion_id, :num_potions)"),
                           {"transaction_id":transaction_id, "potion_id":potion_id, "num_potions":-total_potions})
                    connection.execute(sqlalchemy.text("INSERT INTO gold_ledgers (transaction_id, gold_diff) VALUES (:transaction_id, :gold_diff)"),
                           {"transaction_id":transaction_id, "gold_diff":gold_gained})
                
            else:
                raise Exception("No items in cart")

    return {"total_potions_bought": total_potions, "total_gold_paid": gold_gained}
