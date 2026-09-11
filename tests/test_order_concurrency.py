from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from queue import Queue
from threading import Barrier, Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, func, select, text, update
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import MenuItem, Order, OrderItem, Restaurant, User
from app.orders.schemas import OrderCreate
from app.orders.service import OrderProblem, create_order, update_order_status


@pytest.mark.parametrize("advance_again", [False, True])
def test_status_update_does_not_overwrite_concurrent_change(purchase, advance_again):
    engine, customer_id, _, data = purchase
    with Session(engine) as session:
        order, _ = create_order(session, customer_id, "status-test", data)

    with engine.connect() as connection:
        def competing_change(conn, cursor, statement, parameters, context, executemany):
            if statement.startswith("UPDATE orders"):
                # Another connection changes the row after our read, before our write.
                with Session(engine) as competitor:
                    update_order_status(competitor, data.restaurant_id, order.id, "accepted")
                    if advance_again:
                        update_order_status(competitor, data.restaurant_id, order.id, "out_for_delivery")

        event.listen(connection, "before_cursor_execute", competing_change)
        with Session(connection) as session:
            if advance_again:
                with pytest.raises(OrderProblem) as error:
                    update_order_status(session, data.restaurant_id, order.id, "accepted")
                assert error.value.status_code == 409
            else:
                assert update_order_status(session, data.restaurant_id, order.id, "accepted").status == "accepted"
    with engine.connect() as connection:
        assert connection.scalar(select(Order.status).where(Order.id == order.id)) == ("out_for_delivery" if advance_again else "accepted")


def test_simultaneous_status_retries_succeed(purchase):
    engine, customer_id, _, data = purchase
    with Session(engine) as session:
        order, _ = create_order(session, customer_id, "status-retries", data)
    ready = Barrier(2)

    def attempt():
        with engine.connect() as connection:
            def overlap_updates(conn, cursor, statement, parameters, context, executemany):
                if statement.startswith("UPDATE orders"):
                    ready.wait(timeout=5)
            event.listen(connection, "before_cursor_execute", overlap_updates)
            with Session(connection) as session:
                return update_order_status(session, data.restaurant_id, order.id, "accepted")

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert [result.status for result in results] == ["accepted", "accepted"]
    with engine.connect() as connection:
        assert connection.scalar(select(Order.status).where(Order.id == order.id)) == "accepted"

pytestmark = pytest.mark.integration


@pytest.fixture
def purchase():
    engine = get_engine()
    # Committed seed data is necessary for independent database connections.
    with engine.begin() as connection:
        customer_id = connection.scalar(User.__table__.insert().values(
            email=f"concurrency-{uuid4().hex}@example.com", name="Test", role="customer", password_hash="unused",
        ).returning(User.id))
        restaurant_id = connection.scalar(Restaurant.__table__.insert().values(name="Concurrency test", address="Test").returning(Restaurant.id))
        item_id = connection.scalar(MenuItem.__table__.insert().values(
            restaurant_id=restaurant_id, name="Soup", price=Decimal("6.50"), available=True,
        ).returning(MenuItem.id))
    data = OrderCreate(restaurant_id=restaurant_id, delivery_name="Test", delivery_address="Test",
                       items=[{"menu_item_id": item_id, "quantity": 2}])
    try:
        yield engine, customer_id, item_id, data
    finally:
        # Delete only records belonging to this fixture, in foreign-key order.
        with engine.begin() as connection:
            order_ids = select(Order.id).where(Order.customer_id == customer_id)
            connection.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
            connection.execute(delete(Order).where(Order.customer_id == customer_id))
            connection.execute(delete(MenuItem).where(MenuItem.id == item_id))
            connection.execute(delete(Restaurant).where(Restaurant.id == restaurant_id))
            connection.execute(delete(User).where(User.id == customer_id))


def wait_for_blocked(engine, pids):
    # Observe actual PostgreSQL lock waits instead of assuming thread timing.
    deadline = monotonic() + 5
    with engine.connect() as observer:
        while monotonic() < deadline:
            if all(observer.scalar(text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": pid}) for pid in pids):
                return
            sleep(0.01)
    pytest.fail("Expected database lock wait was not observed")


def run_purchase(engine, customer_id, key, data, pids):
    with engine.connect() as connection:
        pids.put(connection.scalar(text("SELECT pg_backend_pid()")))
        # End the diagnostic query's transaction; the service owns its transaction.
        connection.commit()
        with Session(connection) as session:
            try:
                return create_order(session, customer_id, key, data)
            except OrderProblem as error:
                return error


@pytest.mark.parametrize("different_request", [False, True])
def test_overlapping_requests_share_one_customer_key(purchase, different_request):
    engine, customer_id, _, data = purchase
    other = data.model_copy(update={"delivery_address": "Different"}) if different_request else data
    pids = Queue()
    with ThreadPoolExecutor(max_workers=2) as pool, engine.connect() as blocker:
        blocker.execute(select(User.id).where(User.id == customer_id).with_for_update())
        futures = [pool.submit(run_purchase, engine, customer_id, "same-key", request, pids) for request in (data, other)]
        try:
            wait_for_blocked(engine, [pids.get(timeout=5), pids.get(timeout=5)])
        finally:
            blocker.rollback()
        results = [future.result(timeout=10) for future in futures]
    successes = [result for result in results if not isinstance(result, OrderProblem)]
    if different_request:
        errors = [result for result in results if isinstance(result, OrderProblem)]
        assert len(successes) == len(errors) == 1
        assert errors[0].status_code == 409
        assert successes[0][1] is True
    else:
        assert len(successes) == 2
        assert sorted(created for _, created in successes) == [False, True]
        assert successes[0][0] == successes[1][0]
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(Order).where(Order.customer_id == customer_id)) == 1
        assert connection.scalar(select(func.count()).select_from(OrderItem).join(Order).where(Order.customer_id == customer_id)) == 1


@pytest.mark.parametrize("unavailable", [False, True])
def test_menu_edit_first_is_used_by_waiting_order(purchase, unavailable):
    engine, customer_id, item_id, data = purchase
    pids = Queue()
    with ThreadPoolExecutor(max_workers=1) as pool, engine.connect() as editor:
        editor.execute(update(MenuItem).where(MenuItem.id == item_id).values(price=Decimal("8.00"), available=not unavailable))
        future = pool.submit(run_purchase, engine, customer_id, "edit-first", data, pids)
        try:
            wait_for_blocked(engine, [pids.get(timeout=5)])
            editor.commit()
        finally:
            editor.rollback()
        result = future.result(timeout=10)
    if unavailable:
        assert isinstance(result, OrderProblem) and result.status_code == 409
        with engine.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(Order).where(Order.customer_id == customer_id)) == 0
    else:
        response, created = result
        assert created
        assert response.total == Decimal("16.00")
        assert response.items[0].unit_price == Decimal("8.00")


def test_order_holds_menu_lock_until_commit(purchase):
    engine, customer_id, item_id, data = purchase
    order_ready, finish_order = Event(), Event()
    pids = Queue()

    def place_paused_order():
        with engine.connect() as connection:
            def pause_after_menu_locks(conn, cursor, statement, parameters, context, executemany):
                if statement.startswith("INSERT INTO orders"):
                    order_ready.set()
                    if not finish_order.wait(5):
                        raise RuntimeError("Test did not release order")
            event.listen(connection, "before_cursor_execute", pause_after_menu_locks)
            with Session(connection) as session:
                return create_order(session, customer_id, "order-first", data)

    def edit_menu():
        with engine.begin() as connection:
            pids.put(connection.scalar(text("SELECT pg_backend_pid()")))
            connection.execute(update(MenuItem).where(MenuItem.id == item_id).values(price=Decimal("9.00")))

    with ThreadPoolExecutor(max_workers=2) as pool:
        order_future = pool.submit(place_paused_order)
        try:
            assert order_ready.wait(5)
            edit_future = pool.submit(edit_menu)
            wait_for_blocked(engine, [pids.get(timeout=5)])
        finally:
            finish_order.set()
        response, created = order_future.result(timeout=10)
        edit_future.result(timeout=10)
    assert created and response.total == Decimal("13.00")
    with engine.connect() as connection:
        assert connection.scalar(select(MenuItem.price).where(MenuItem.id == item_id)) == Decimal("9.00")
        assert connection.scalar(select(OrderItem.unit_price).where(OrderItem.order_id == response.id)) == Decimal("6.50")
