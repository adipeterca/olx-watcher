#!/usr/bin/python3

import argparse
import requests
import json

import matplotlib.pyplot as plt

from bs4 import BeautifulSoup
from datetime import datetime

import dbctrl

VERSION = "1.0.0"

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

def get_price_history(db: dbctrl.DBController, data: dict):
    rows = db.get_price_history(data["id"])

    if len(rows) == 0:
            print(f"[INFO] No prior data for product ID '{id}'.")
            return
        
    print("Prices are order from oldest to newest:")
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

    parser = argparse.ArgumentParser(description="OLX Watcher CLI tool.\nCheck out more at https://github.com/adipeterca/olx-watcher")
    parser.add_argument("--url", required=True, help="URL to fetch")
    parser.add_argument("--version", action="version", version=f"OLX Watcher {VERSION}")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--add", action="store_true", help="Add product to database")
    group.add_argument("--update", action="store_true", help="Update price for product")
    group.add_argument("--price-history", action="store_true", help="Check product price history in string format")
    group.add_argument("--price-graph", action="store_true", help="Create a price history graph for the product")

    args = parser.parse_args()

    response = requests.get(args.url)
    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find("script", {"type": "text/javascript", "id": "olx-init-config"})
    if not script_tag:
        print("Script tag not found")
        exit()
    script_content = script_tag.string or script_tag.text

    json_str = script_content.split('"{\\"ad\\":{\\"ad\\":')[1].split(',\\"fragments')[0]
    
    json_str = json_str.replace('\\"', '"')

    try:
        data = json.loads(json_str)

    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)

    # Do stuff with the parsed data
    db = dbctrl.DBController()

    if args.add:
        add_product(db, data)
    elif args.update:
        update_price(db, data)
    elif args.price_history:
        get_price_history(db, data)
    elif args.price_graph:
        get_price_graph(db, data)

if __name__ == "__main__":
    main()


'''
Known bugs & future features:
1. Non existing items will throw errors.
    1.1. How to fix:
        * add a parameter called "--clean-up" which will query items to delete all non-active ones.
        * experiment on an empty product page to see what the HTML looks like
2. Add a "--graph" parameter which will generate a graph image for a product
'''