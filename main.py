#!/usr/bin/python3

import argparse
import logging

import matplotlib.pyplot as plt

from datetime import datetime

import dbctrl
import utils

VERSION = "1.2.7"

def add_product(db: dbctrl.DBController, data: dict):
    db.add_product(
        id=data["id"],
        title=data["title"],
        description=data["description"],
        url=rf'{data["url"]}'.encode("utf-8").decode("unicode_escape").replace('\\/', '/'),
        active=data["isActive"]
    )
    db.track_price(
        id=data["id"],
        price=data["price"]["regularPrice"]["value"],
        currency=data["price"]["regularPrice"]["currencyCode"]
    )

def update_price(db: dbctrl.DBController, data: dict):
    db.track_price(
        id=data["id"],
        price=data["price"]["regularPrice"]["value"],
        currency=data["price"]["regularPrice"]["currencyCode"]
    )

def update_all_prices(db: dbctrl.DBController):
    rows = db.get_all_products()
    for row in rows:
        url = row[3]

        try:
            data = utils.parse_url(url)
        except utils.OlxProductNotFound:
            continue
        
        db.track_price(
            id=data["id"],
            price=data["price"]["regularPrice"]["value"],
            currency=data["price"]["regularPrice"]["currencyCode"]
        )

def get_price_history(db: dbctrl.DBController, data: dict):
    '''
    Output is intentionally handled by "print" - it must always show to the user, 
    regardless of verbosity.
    '''
    rows = db.get_price_history(data["id"])

    if len(rows) == 0:
            print(f"No prior data for product ID '{id}'.")
            return
        
    print("Prices are ordered from oldest to newest:")
    for row in rows:
        print(f"{row[0]} {row[1]} - {row[2]}")

def get_price_graph(db: dbctrl.DBController, data: dict):
    rows = db.get_price_history(data["id"])

    if len(rows) == 0:
        raise RuntimeError(f'No available price information for product id {data["id"]}')
    
    # Row format:
    # PRICE,CURRENCY,TIMESTAMP
    currency = rows[0][1]

    prices = [row[0] for row in rows]
    dates = [datetime.fromisoformat(row[2]).strftime("%H:%M %d-%m-%y") for row in rows]

    plt.plot(dates, prices, marker="o")
    plt.title(f'Product history for {data["title"]} (prices in {currency})')
    plt.xlabel("Dates")
    plt.ylabel("Prices")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'graphs/{data["id"]}.png')
    plt.close()

def main():

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # 
    # Parser setup
    # 
    parser = argparse.ArgumentParser(description="OLX Watcher CLI tool.\nCheck out more at https://github.com/adipeterca/olx-watcher") 
    parser.add_argument("--version", action="version", version=f"OLX Watcher {VERSION}")
    parser.add_argument("--verbosity", default="info", help="Verbosity level: debug / info / warning / error")

    main_group = parser.add_mutually_exclusive_group(required=True)
    main_group.add_argument("--update-all-prices", action="store_true", help="Update all product prices")

    main_group.add_argument("--url", help="URL to fetch")


    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--add", action="store_true", help="Add product to database")
    action_group.add_argument("--update", action="store_true", help="Update price for product")
    action_group.add_argument("--price-history", action="store_true", help="Check product price history in string format")
    action_group.add_argument("--price-graph", action="store_true", help="Create a price history graph for the product")

    args = parser.parse_args()

    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    
    level = None
    if args.verbosity == "debug": level = logging.DEBUG
    elif args.verbosity == "info": level = logging.INFO
    elif args.verbosity == "warning": level = logging.WARNING
    else: level = logging.ERROR

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    db = dbctrl.DBController()

    if args.url:
        if not (args.add or args.update or args.price_history or args.price_graph):
            parser.error("--url requires one of --add, --update, --price-history, or --price-graph")

        try:
            data = utils.parse_url(args.url)
        except utils.OlxProductNotFound:
            print("Sorry, this item does not exist!")
            exit(200)

        if args.add:
            add_product(db, data)
        elif args.update:
            update_price(db, data)
        elif args.price_history:
            get_price_history(db, data)
        elif args.price_graph:
            get_price_graph(db, data)
    elif args.update_all_prices:
        update_all_prices(db)

if __name__ == "__main__":
    main()