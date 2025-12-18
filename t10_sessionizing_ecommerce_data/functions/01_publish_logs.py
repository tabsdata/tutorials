import os
from pathlib import Path

import tabsdata as td
import tabsdata.tableframe as tdf
from tabsdata import LogFormat

web_pattern = (
    r"%{TIMESTAMP_ISO8601:timestamp} "
    r"event_id=%{UUID:event_id} "
    r"type=%{WORD:type} "
    r"user_id=%{WORD:user_id} "
    r"path=%{URIPATHPARAM:path} "
    r"referrer=%{URIPATHPARAM:referrer} "
    r'user_agent="%{DATA:user_agent}"'
)

web_schema = {
    "timestamp": tdf.Column("timestamp", td.String),
    "event_id": tdf.Column("event_id", td.String),
    "type": tdf.Column("event_type", td.String),
    "user_id": tdf.Column("user_id", td.String),
    "path": tdf.Column("path", td.String),
    "referrer": tdf.Column("referrer", td.String),
    "user_agent": tdf.Column("user_agent", td.String),
}

purchase_pattern = (
    r"%{TIMESTAMP_ISO8601:timestamp} "
    r"event_id=%{UUID:event_id} "
    r"type=%{WORD:type} "
    r"user_id=%{WORD:user_id} "
    r"cart_id=%{WORD:cart_id} "
    r"order_id=%{WORD:order_id} "
    r"total=%{NUMBER:total} "
    r"currency=%{WORD:currency} "
    r"payment_method=%{WORD:payment_method}"
)

purchase_schema = {
    "timestamp": tdf.Column("timestamp", td.String),
    "event_id": tdf.Column("event_id", td.String),
    "type": tdf.Column("event_type", td.String),
    "user_id": tdf.Column("user_id", td.String),
    "cart_id": tdf.Column("cart_id", td.String),
    "order_id": tdf.Column("order_id", td.String),
    "total": tdf.Column("total_amount", td.Float64),
    "currency": tdf.Column("currency", td.String),
    "payment_method": tdf.Column("payment_method", td.String),
}

cart_pattern = (
    r"%{TIMESTAMP_ISO8601:timestamp} "
    r"event_id=%{UUID:event_id} "
    r"type=%{WORD:type} "
    r"user_id=%{WORD:user_id} "
    r"cart_id=%{WORD:cart_id} "
    r"action=%{WORD:action} "
    r"product_id=%{INT:product_id} "
    r"quantity=%{INT:quantity} "
    r"price=%{NUMBER:price}"
)

cart_schema = {
    "timestamp": tdf.Column("timestamp", td.String),
    "event_id": tdf.Column("event_id", td.String),
    "type": tdf.Column("event_type", td.String),
    "user_id": tdf.Column("user_id", td.String),
    "cart_id": tdf.Column("cart_id", td.String),
    "action": tdf.Column("cart_action", td.String),
    "product_id": tdf.Column("product_id", td.Int32),
    "quantity": tdf.Column("quantity", td.Int32),
    "price": tdf.Column("price", td.Float64),
}


path = Path(__file__).resolve().parent.parent / "logs"


@td.publisher(
    source=td.LocalFileSource(
        [
            os.path.join(path, "cart_*.log"),
            os.path.join(path, "purchase_*.log"),
            os.path.join(path, "web_*.log"),
        ],
        format=LogFormat(),
    ),
    tables=["cart_log", "purchase_log", "web_log"],
)
def publish_logs(
    cart: list[tdf.TableFrame],
    purchase: list[tdf.TableFrame],
    web: list[tdf.TableFrame],
):
    cart = td.concat(cart).grok("message", cart_pattern, cart_schema)
    purchase = td.concat(purchase).grok("message", purchase_pattern, purchase_schema)
    web = td.concat(web).grok("message", web_pattern, web_schema)
    return cart, purchase, web
