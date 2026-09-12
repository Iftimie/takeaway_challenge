"""Destructively replace all application records with demo data in the configured DB."""
import argparse
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.auth.service import password_hasher
from app.config import Settings
from app.db import get_engine
from app.models import User, Restaurant, StaffAssignment, MenuItem, Order, OrderItem
from app.orders.schemas import OrderCreate
from app.orders.service import request_fingerprint

DEMO_PASSWORD = 'password'
ACCOUNTS = [
    ('admin@example.com', 'Demo Admin', 'admin'),
    ('staff@example.com', 'Demo Staff', 'staff'),
    ('staff2@example.com', 'Second Staff', 'staff'),
    ('customer@example.com', 'Demo Customer', 'customer'),
    ('customer2@example.com', 'Second Customer', 'customer'),
]


def reset_and_seed(session: Session) -> None:
    # Caller owns the transaction: any failure rolls back deletes AND inserts.
    for model in (OrderItem, Order, StaffAssignment, MenuItem, Restaurant, User):
        session.execute(delete(model))
    users = []
    for email, name, role in ACCOUNTS:
        user = User(email=email, name=name, role=role,
                    password_hash=password_hasher.hash(DEMO_PASSWORD),
                    default_address='10 Demo Street' if role == 'customer' else None)
        session.add(user)
        users.append(user)
    restaurants = [Restaurant(name=name, address=address) for name, address in [
        ('Corner Pizza', '1 Market Street'), ('Green Bowl', '22 Garden Road'),
        ('Sunday Kitchen', '8 Station Square'),
    ]]
    session.add_all(restaurants)
    session.flush()
    session.add_all([StaffAssignment(staff_id=users[index + 1].id, restaurant_id=restaurants[index].id)
                     for index in range(2)])
    menus = []
    for restaurant, names in zip(restaurants, [
        ['Margherita', 'Mushroom Pizza', 'Garlic Bread', 'Tiramisu'],
        ['Falafel Bowl', 'Roasted Vegetable Bowl', 'Lentil Soup', 'Lemon Cake'],
        ['Grilled Chicken', 'Vegetable Curry', 'Roast Potatoes', 'Apple Pie'],
    ]):
        items = [MenuItem(restaurant_id=restaurant.id, name=name, price=Decimal(price), available=index != 3)
                 for index, (name, price) in enumerate(zip(names, ['12.50', '14.00', '5.50', '6.00']))]
        session.add_all(items)
        menus.append(items)
    session.flush()
    for index, status in enumerate(['pending', 'accepted', 'out_for_delivery', 'delivered', 'pending']):
        restaurant_index = 0 if index < 4 else 1
        customer = users[3 if index < 4 else 4]
        items = menus[restaurant_index][:2]
        data = OrderCreate(restaurant_id=restaurants[restaurant_index].id,
                           delivery_name=customer.name, delivery_address=customer.default_address,
                           items=[{'menu_item_id': item.id, 'quantity': 1} for item in items])
        order = Order(customer_id=customer.id, restaurant_id=data.restaurant_id,
                      delivery_name=data.delivery_name, delivery_address=data.delivery_address,
                      status=status, total=sum((item.price for item in items), Decimal('0.00')),
                      currency='EUR', idempotency_key=f'demo-order-{index}',
                      request_fingerprint=request_fingerprint(data))
        session.add(order)
        session.flush()
        session.add_all([OrderItem(order_id=order.id, menu_item_id=item.id, name=item.name,
                                   unit_price=item.price, quantity=1) for item in items])
    session.flush()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yes-delete-all-data', action='store_true',
                        help='Delete every application record in the .env/environment database.')
    args = parser.parse_args(argv)
    if not args.yes_delete_all_data:
        parser.error('This deletes ALL application data. Pass --yes-delete-all-data to proceed.')
    settings = Settings()
    print(f'Resetting {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}')
    with Session(get_engine()) as session, session.begin():
        reset_and_seed(session)
    print('Created 5 users, 3 restaurants, 12 menu items, 2 assignments and 5 orders.')
    print('Demo accounts: ' + ', '.join(email for email, _, _ in ACCOUNTS))
    print(f'Password for every demo account: {DEMO_PASSWORD}')
    print('Clear browser session storage before logging in again. IDs are not reset.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
