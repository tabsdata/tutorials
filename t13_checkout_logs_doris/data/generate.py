#
# Copyright 2026 Tabsdata Inc.
#

"""script that generates the dummy checkout logs in this folder, one file per
source per hour, each source logging the same requests with its own field
names, id formats and timestamp formats

    python data/generate.py

the seed is fixed so every run writes the same files
"""

import csv
import json
import pathlib
import random
from datetime import datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
RNG = random.Random(13)

START = datetime(2026, 9, 30, 10, tzinfo=timezone.utc)
HOURS = 6

# checkouts and product page views per hour, lunchtime is busier
CHECKOUTS_PER_HOUR = [240, 280, 330, 310, 290, 250]
BROWSES_PER_HOUR = [420, 480, 560, 540, 500, 440]

# window where the migration's CREATE INDEX holds a lock on the orders table so
# every order insert hits the statement timeout
INCIDENT_START = datetime(2026, 9, 30, 14, 8, 31, 204000, tzinfo=timezone.utc)
INCIDENT_END = datetime(2026, 9, 30, 14, 22, 47, 615000, tzinfo=timezone.utc)

# the checkout from the support ticket
TICKET_USER = 48291
TICKET_CLICK = datetime(2026, 9, 30, 14, 14, 21, 884000, tzinfo=timezone.utc)

HOSTS = {
    "auth": ["auth-5f7b9-2kq7x", "auth-5f7b9-m8d4c"],
    "cart": ["cart-6c8d4-p2vzn", "cart-6c8d4-tq9wl"],
    "catalog": ["catalog-9a1e3-bw5rd", "catalog-9a1e3-kk7mf", "catalog-9a1e3-x2hzs"],
    "checkout": ["checkout-7c9d5-hx2lp", "checkout-7c9d5-r4jmk", "checkout-7c9d5-z8w2b"],
    "orders": ["orders-84bf6-c6nqt", "orders-84bf6-vj3xs"],
}
POD_IPS = {"orders-84bf6-c6nqt": "10.0.3.21", "orders-84bf6-vj3xs": "10.0.3.38"}
MIGRATION_HOST = "orders-migrate-0042-9kx2t"
MIGRATION = "0042_add_orders_created_at_index"
CREATE_INDEX = "CREATE INDEX orders_created_at_idx ON public.orders (created_at);"
INSERT_ORDER = "INSERT INTO orders (id, user_id, request_id, total_cents, created_at) VALUES ($1, $2, $3, $4, now())"

SKUS = [f"SKU-{n}" for n in range(1001, 1121)]
PRICES = {sku: round(RNG.uniform(8, 140), 2) for sku in SKUS}
USERS = RNG.sample([n for n in range(10000, 99999) if n != TICKET_USER], 3500)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
]
DECLINES = {
    "card_declined": "Your card was declined.",
    "insufficient_funds": "Your card has insufficient funds.",
    "expired_card": "Your card has expired.",
    "incorrect_cvc": "Your card's security code is incorrect.",
}
CARD_BRANDS = ["visa", "visa", "visa", "mastercard", "mastercard", "amex", "discover"]

# one list of (time, record) per source, written out by hour at the end
frontend, gateway, services, payments, infra = [], [], [], [], []
sessions: dict[int | None, str] = {}
client_ips: dict[int | None, str] = {}


def ms(low: float, high: float) -> timedelta:
    return timedelta(milliseconds=RNG.uniform(low, high))


def hexid(n: int) -> str:
    return "".join(RNG.choice("0123456789abcdef") for _ in range(n))


def alnum(n: int) -> str:
    return "".join(RNG.choice("ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz0123456789") for _ in range(n))


def session_of(user: int | None) -> str:
    if user is None:
        return "s_" + alnum(16)
    return sessions.setdefault(user, "s_" + alnum(16))


def ip_of(user: int | None) -> str:
    if user is None:
        return f"{RNG.choice([24, 67, 73, 98, 174])}.{RNG.randint(1, 254)}.{RNG.randint(1, 254)}.{RNG.randint(1, 254)}"
    return client_ips.setdefault(user, ip_of(None))


# --- per source writers, each in its own shape --------------------------------

# browser analytics events, camelCase fields and epoch millisecond timestamps
def web(at: datetime, event: str, request: str, user: int | None, page: str, ua: str,
        error_code: str | None = None, error_message: str | None = None) -> None:
    frontend.append((at, {
        "messageId": f"{hexid(8)}-{hexid(4)}-{hexid(4)}-{hexid(4)}-{hexid(12)}",
        "eventType": event,
        "ts": int(at.timestamp() * 1000),
        "requestId": request,
        "userId": user,
        "sessionId": session_of(user),
        "page": page,
        "userAgent": ua,
        "errorCode": error_code,
        "errorMessage": error_message,
    }))


# nginx access log lines with the request id and user id appended, nginx writes
# the line when the response goes out so the time is the end of the request
def access(end: datetime, start: datetime, method: str, path: str, status: int, request: str,
           user: int | None, ua: str, referrer: str) -> None:
    size = RNG.randint(380, 2400) if status < 400 else RNG.randint(150, 240)
    uid = user if user is not None else "-"
    gateway.append((end, (
        f'{ip_of(user)} - - [{end.strftime("%d/%b/%Y:%H:%M:%S +0000")}] "{method} {path} HTTP/1.1" '
        f'{status} {size} "{referrer}" "{ua}" rt={(end - start).total_seconds():.3f} req_id={request} uid={uid}'
    )))


# structured service logs, snake_case fields, lowercase levels and ISO timestamps
def log(at: datetime, service: str, level: str, event: str, msg: str, request: str | None,
        user: int | None, duration: float | None = None, host: str | None = None) -> None:
    services.append((at, {
        "timestamp": at.strftime("%Y-%m-%dT%H:%M:%S.") + f"{at.microsecond // 1000:03d}Z",
        "level": level,
        "service": service,
        "host": host or RNG.choice(HOSTS[service]),
        "request_id": request,
        "user_id": str(user) if user is not None else None,
        "event": event,
        "msg": msg,
        "duration_ms": round(duration, 1) if duration is not None else None,
    }))


# payment provider webhook events as stored in the payments database, the
# request id is inside the idempotency key and timestamps are MM/DD/YY
def payment(at: datetime, event: str, request: str, user: int, cents: int, brand: str,
            failure: str | None = None) -> None:
    payments.append((at, {
        "event_id": "evt_" + alnum(24),
        "created": at.strftime("%m/%d/%y %H:%M:%S"),
        "event_type": event,
        "transaction_request": f"checkout-{request}",
        "customer_ref": f"cus_{user}",
        "amount_cents": cents,
        "currency": "usd",
        "card_brand": brand,
        "failure_code": failure or "",
        "failure_message": DECLINES[failure] if failure else "",
    }))


# postgres log lines from the orders database as exported from cloudwatch, the
# line prefix is the rds default of time, client, user@db and pid
def pg(at: datetime, severity: str, text: str, pid: int, client: str = "", who: str = "@") -> None:
    infra.append((at, {
        "eventId": "".join(RNG.choice("0123456789") for _ in range(56)),
        "logStreamName": "orders-db-primary",
        "timestamp": int(at.timestamp() * 1000),
        "ingestionTime": int((at + ms(300, 1800)).timestamp() * 1000),
        "message": f"{at.strftime('%Y-%m-%d %H:%M:%S')} UTC:{client}:{who}:[{pid}]:{severity}:  {text}",
    }))


# --- traffic ------------------------------------------------------------------

def browse(at: datetime) -> None:
    user = None if RNG.random() < 0.3 else RNG.choice(USERS)
    request, sku, ua = hexid(12), RNG.choice(SKUS), RNG.choice(USER_AGENTS)
    web(at, "page_view", request, user, f"/products/{sku.lower()}", ua)
    hit = RNG.random() < 0.8
    took = RNG.uniform(1, 6) if hit else RNG.uniform(18, 60)
    fetched = at + ms(20, 45)
    source = "cache hit" if hit else "cache miss, loaded from catalog-db"
    log(fetched + timedelta(milliseconds=took), "catalog", "info", "product_fetched",
        f"fetched product {sku} ({source})", request, user, took)
    access(fetched + ms(2, 6) + timedelta(milliseconds=took), fetched, "GET", f"/api/products/{sku}", 200,
           request, user, ua, f"https://shop.example.com/products/{sku.lower()}")


def checkout(click: datetime, user: int, random_failures: bool = True) -> None:
    request, ua = hexid(12), RNG.choice(USER_AGENTS)
    web(click, "checkout_clicked", request, user, "/checkout", ua)
    received = click + ms(25, 60)
    t = received

    def fail(status: int, code: str, text: str) -> None:
        end = t + ms(3, 12)
        access(end, received, "POST", "/api/checkout", status, request, user, ua, "https://shop.example.com/checkout")
        web(end + ms(40, 160), "checkout_error_shown", request, user, "/checkout", ua, code, text)

    # validates the session token
    took = RNG.uniform(2, 6)
    t += timedelta(milliseconds=took)
    if RNG.random() < 0.02 and random_failures:
        log(t, "auth", "warning", "token_expired", f"session token expired for user {user}", request, user, took)
        fail(401, "SESSION_EXPIRED", "Your session expired. Please sign in again.")
        return
    log(t, "auth", "info", "token_validated", f"session token valid for user {user}", request, user, took)

    # loads the cart and totals it
    items = RNG.sample(SKUS, RNG.choice([1, 1, 2, 2, 2, 3, 3, 4, 5]))
    subtotal = sum(PRICES[sku] for sku in items)
    total = round(subtotal * 1.06, 2)
    cents = int(round(total * 100))
    took = RNG.uniform(6, 25)
    t += ms(3, 8) + timedelta(milliseconds=took)
    log(t, "cart", "info", "cart_loaded", f"loaded cart with {len(items)} item(s), subtotal {subtotal:.2f} USD",
        request, user, took)
    t += ms(2, 6)
    log(t, "checkout", "info", "checkout_started", f"checkout started for {len(items)} item(s), total {total:.2f} USD",
        request, user)

    # reserves inventory
    took = RNG.uniform(12, 60)
    t += timedelta(milliseconds=took)
    if RNG.random() < 0.015 and random_failures:
        sku = RNG.choice(items)
        log(t, "checkout", "warning", "out_of_stock", f"item {sku} out of stock, checkout aborted", request, user, took)
        fail(409, "OUT_OF_STOCK", "One of the items in your cart is no longer available.")
        return
    log(t, "checkout", "info", "inventory_reserved", f"reserved {len(items)} item(s) in warehouse us-east-2",
        request, user, took)

    # charges the card through the payment provider
    brand = RNG.choice(CARD_BRANDS)
    t += ms(3, 8)
    log(t, "checkout", "info", "payment_requested", f"requesting charge of {cents} cents from payment provider",
        request, user)
    payment(t + ms(80, 220), "payment_intent.created", request, user, cents, brand)
    charged = t + ms(350, 1400)
    if RNG.random() < 0.045 and random_failures:
        failure = RNG.choice(list(DECLINES))
        payment(charged, "charge.failed", request, user, cents, brand, failure)
        t = charged + ms(30, 90)
        log(t, "checkout", "warning", "payment_declined", f"charge declined by payment provider: {failure}",
            request, user)
        fail(402, "PAYMENT_DECLINED", DECLINES[failure])
        return
    payment(charged, "charge.succeeded", request, user, cents, brand)
    charge = "ch_" + alnum(24)
    t = charged + ms(30, 90)
    log(t, "checkout", "info", "payment_captured", f"payment captured, charge {charge}", request, user)

    # creates the order, the insert waits on the table lock during the incident
    host = RNG.choice(HOSTS["orders"])
    inserted = t + ms(4, 10)
    if INCIDENT_START <= inserted <= INCIDENT_END:
        pid = RNG.randint(23000, 29999)
        client = f"{POD_IPS[host]}({RNG.randint(40000, 60999)})"
        pg(inserted + timedelta(milliseconds=1000.1), "LOG",
           f"process {pid} still waiting for RowExclusiveLock on relation 16421 of database 16384 after "
           f"{RNG.uniform(1000.05, 1000.4):.3f} ms", pid, client, "orders_svc@orders")
        pg(inserted + timedelta(milliseconds=1000.1), "DETAIL",
           f"Process holding the lock: 22987. Wait queue: {pid}.", pid, client, "orders_svc@orders")
        pg(inserted + timedelta(milliseconds=5000.2), "ERROR", "canceling statement due to statement timeout",
           pid, client, "orders_svc@orders")
        pg(inserted + timedelta(milliseconds=5000.2), "STATEMENT", INSERT_ORDER, pid, client, "orders_svc@orders")
        t = inserted + ms(5002, 5008)
        log(t, "orders", "error", "order_insert_failed",
            "insert into orders failed: canceling statement due to statement timeout after 5000 ms",
            request, user, 5000.0, host)
        t += ms(1, 4)
        log(t, "checkout", "error", "checkout_failed",
            f"order creation failed after payment {charge} was captured, returning 500, charge not refunded",
            request, user)
        fail(500, "ORDER_FAILED", "Something went wrong placing your order. You have not been charged.")
        return
    took = RNG.uniform(4, 18)
    order = "ord_" + hexid(10)
    t = inserted + timedelta(milliseconds=took)
    log(t, "orders", "info", "order_created", f"created order {order} with {len(items)} item(s)",
        request, user, took, host)
    t += ms(2, 6)
    log(t, "checkout", "info", "checkout_completed", f"checkout completed, order {order} placed for {total:.2f} USD",
        request, user)
    end = t + ms(2, 8)
    access(end, received, "POST", "/api/checkout", 200, request, user, ua, "https://shop.example.com/checkout")
    web(end + ms(150, 450), "order_confirmation_viewed", request, user, f"/orders/{order}", ua)


# background postgres logs, checkpoints every 5 minutes, a few autovacuums and
# the slow order history query the migration's index is meant to fix
def database_noise() -> None:
    for minute in range(0, HOURS * 60, 5):
        began = START + timedelta(minutes=minute, seconds=RNG.uniform(0, 0.3))
        pg(began, "LOG", "checkpoint starting: time", 412)
        took = RNG.uniform(150, 270)
        buffers = RNG.randint(900, 2600)
        pg(began + timedelta(seconds=took), "LOG",
           f"checkpoint complete: wrote {buffers} buffers ({buffers / 163.84:.1f}%); 0 WAL file(s) added, 0 removed, "
           f"1 recycled; write={took - 0.02:.3f} s, sync=0.012 s, total={took:.3f} s", 412)
    for _ in range(HOURS * 2):
        at = START + timedelta(seconds=RNG.uniform(0, HOURS * 3600))
        table = RNG.choice(["order_items", "orders", "order_events"])
        pg(at, "LOG", f'automatic vacuum of table "orders.public.{table}": index scans: 1, pages: 0 removed, '
                      f"{RNG.randint(4000, 30000)} remain, tuples: {RNG.randint(200, 4000)} removed", RNG.randint(1000, 9999))
    for _ in range(HOURS * 3):
        at = START + timedelta(seconds=RNG.uniform(0, HOURS * 3600))
        host = RNG.choice(HOSTS["orders"])
        pid = RNG.randint(23000, 29999)
        pg(at, "LOG", f"duration: {RNG.uniform(1100, 2400):.3f} ms  statement: SELECT o.id, o.status, o.total_cents "
                      "FROM orders o WHERE o.user_id = $1 ORDER BY o.created_at DESC LIMIT 20",
           pid, f"{POD_IPS[host]}({RNG.randint(40000, 60999)})", "orders_svc@orders")


# the migration job that builds the index without CONCURRENTLY and blocks writes
def migration() -> None:
    log(INCIDENT_START - timedelta(milliseconds=412), "orders", "info", "migration_started",
        f"running migration {MIGRATION}", None, None, host=MIGRATION_HOST)
    pg(INCIDENT_START, "LOG", f"statement: {CREATE_INDEX}", 22987, "10.0.3.44(51876)", "migrator@orders")
    took = (INCIDENT_END - INCIDENT_START).total_seconds() * 1000
    pg(INCIDENT_END, "LOG", f"duration: {took:.3f} ms  statement: {CREATE_INDEX}", 22987, "10.0.3.44(51876)",
       "migrator@orders")
    log(INCIDENT_END + timedelta(milliseconds=208), "orders", "info", "migration_finished",
        f"migration {MIGRATION} finished in {took / 1000:.1f} s", None, None, took, MIGRATION_HOST)


def write() -> None:
    for folder in ["frontend", "gateway", "services", "payments", "infra"]:
        (HERE / folder).mkdir(exist_ok=True)
        for old in (HERE / folder).iterdir():
            old.unlink()
    for hour in range(HOURS):
        begin = START + timedelta(hours=hour)
        end = begin + timedelta(hours=1)
        stamp = begin.strftime("%Y%m%d_%H")

        def rows(records: list) -> list:
            return [record for at, record in sorted(records, key=lambda item: item[0]) if begin <= at < end]

        with open(HERE / "frontend" / f"web_events_{stamp}.jsonl", "w") as f:
            f.writelines(json.dumps(record) + "\n" for record in rows(frontend))
        with open(HERE / "gateway" / f"access_{stamp}.log", "w") as f:
            f.writelines(line + "\n" for line in rows(gateway))
        with open(HERE / "services" / f"app_{stamp}.jsonl", "w") as f:
            f.writelines(json.dumps(record) + "\n" for record in rows(services))
        with open(HERE / "payments" / f"payment_events_{stamp}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(payments[0][1]))
            writer.writeheader()
            writer.writerows(rows(payments))
        with open(HERE / "infra" / f"orders_db_{stamp}.jsonl", "w") as f:
            f.writelines(json.dumps(record) + "\n" for record in rows(infra))


def main() -> None:
    for hour in range(HOURS):
        begin = START + timedelta(hours=hour)
        for _ in range(BROWSES_PER_HOUR[hour]):
            browse(begin + timedelta(seconds=RNG.uniform(0, 3595)))
        for _ in range(CHECKOUTS_PER_HOUR[hour]):
            checkout(begin + timedelta(seconds=RNG.uniform(0, 3595)), RNG.choice(USERS))
    checkout(TICKET_CLICK, TICKET_USER, random_failures=False)
    database_noise()
    migration()
    write()
    counts = {name: len(records) for name, records in
              [("frontend", frontend), ("gateway", gateway), ("services", services), ("payments", payments),
               ("infra", infra)]}
    print(f"wrote {HOURS} hours of logs to {HERE}: {counts}")


if __name__ == "__main__":
    main()
