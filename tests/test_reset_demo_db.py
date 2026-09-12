import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.service import password_hasher
from app.config import Settings
from app.db import get_engine
from app.models import User, Restaurant, MenuItem, StaffAssignment, Order, OrderItem
from scripts import reset_demo_db as command


def test_reset_requires_explicit_flag_before_opening_database(monkeypatch):
    monkeypatch.setattr(command, 'get_engine', lambda: pytest.fail('Must not open DB'))
    with pytest.raises(SystemExit) as error:
        command.main([])
    assert error.value.code == 2


@pytest.mark.integration
def test_reset_replaces_data_repeatably_and_rolls_back():
    # This destructive-script test is restricted to the disposable browser DB.
    settings = Settings()
    if (settings.postgres_host, settings.postgres_port, settings.postgres_db) != (
        '127.0.0.1', 55432, 'takeaway_browser_test'
    ):
        pytest.skip('Run against the disposable browser database')
    with get_engine().connect() as connection:
        transaction = connection.begin()
        with Session(connection, join_transaction_mode='create_savepoint') as session:
            session.add(Restaurant(name='Old record', address='Old address'))
            session.commit()
        try:
            with pytest.raises(RuntimeError), Session(connection, join_transaction_mode='create_savepoint') as session, session.begin():
                command.reset_and_seed(session)
                raise RuntimeError('Simulated failure before commit')
            assert connection.scalar(select(Restaurant.id).where(Restaurant.name == 'Old record'))
            with Session(connection, join_transaction_mode='create_savepoint') as session, session.begin():
                for _ in range(2):
                    command.reset_and_seed(session)
                    for model, count in [(User, 5), (Restaurant, 3), (MenuItem, 12),
                                         (StaffAssignment, 2), (Order, 5), (OrderItem, 10)]:
                        assert session.scalar(select(func.count()).select_from(model)) == count
                assert session.scalar(select(Restaurant.id).where(Restaurant.name == 'Old record')) is None
                for user in session.scalars(select(User)):
                    assert password_hasher.verify(command.DEMO_PASSWORD, user.password_hash)
                assert set(session.scalars(select(Order.status))) == {'pending', 'accepted', 'out_for_delivery', 'delivered'}
                for order in session.scalars(select(Order)):
                    total = session.scalar(select(func.sum(OrderItem.unit_price * OrderItem.quantity)).where(OrderItem.order_id == order.id))
                    assert order.total == total
        finally:
            transaction.rollback()
