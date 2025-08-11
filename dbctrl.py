#!/usr/bin/python3

import sqlite3
import logging
from datetime import datetime

class DBController:
    def __init__(self, db_path: str = "main.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;") 
        
        cursor = self.conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            active BOOLEAN NOT NULL
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id TEXT NOT NULL,
            price INTEGER NOT NULL,
            currency TEXT NOT NULL,
            timestamp TEXT NOT NULL, -- ISO 8601 datetime string
            PRIMARY KEY (id, timestamp),
            FOREIGN KEY (id) REFERENCES products(id)
        );
        ''')

        self.conn.commit()

    def add_product(self, id: int, title: str, description: str, url: str, active: bool, fail_on_existance: bool = False):
        product = {
            "id": id,
            "title": title,
            "description": description,
            "url": url,
            "active": active
        }

        cursor = self.conn.cursor()

        try:
            cursor.execute(
                '''
                INSERT INTO products (id, title, description, url, active)
                VALUES (:id, :title, :description, :url, :active)
                ''',
                product
            )

            self.conn.commit()
        except sqlite3.IntegrityError as err:
            if fail_on_existance:
                raise err
            else:
                logging.warning(f"Product '{title}' already exists!")
        
    def track_price(self, id: int, price: int, currency: str):
        '''
        Will add a new price only if the current one is different from the last one added, in chronological order.
        '''

        price_entry = {
            "id": id,
            "price": price,
            "currency": currency,
            "timestamp": datetime.now().isoformat()
        }

        cursor = self.conn.cursor()

        cursor.execute(
            '''
            SELECT price FROM price_history
            WHERE id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            ''',
            (id,)
        )
        row = cursor.fetchone()
        if row is None or row[0] != price:

            cursor.execute(
                '''
                INSERT INTO price_history (id, price, currency, timestamp)
                VALUES (:id, :price, :currency, :timestamp)
                ''',
                price_entry
            )

            self.conn.commit()

            logging.info(f"Added new price entry of '{price}' '{currency}' for product ID '{id}'.")
        else:
            print("should print")
            logging.debug(f"Price not changed for product with ID '{id}'.")
    
    def mark_product_as_sold(self, id: int):
        '''
        @id: product ID

        Marks a product's "active" column as "0", meaning the item was sold.
        Thus, no new price updates will be queried for this product.
        '''
        cursor = self.conn.cursor()

        cursor.execute(
            '''
            UPDATE products
            SET active = 0
            WHERE id = ?
            ''',
            (id,)
        )

        if cursor.rowcount == 0:
            logging.warning(f"Could not mark item with ID '{id}' as sold because it does not exist.")

    def get_price_history(self, id: int) -> list:

        cursor = self.conn.cursor()

        cursor.execute(
            '''
            SELECT price, currency, timestamp FROM price_history
            WHERE id = ?
            ORDER BY timestamp ASC
            ''',
            (id,)
        )

        rows = cursor.fetchall()
        return rows

    def get_all_products(self) -> list[list]:
        '''
        Returns all product rows.

        Each row is organized in ID, TITLE, DESCRIPTION, URL, ACTIVE.
        '''

        cursor = self.conn.cursor()
        cursor.execute(
            '''
            SELECT id, title, description, url, active
            FROM products
            '''
        )

        rows = cursor.fetchall()

        if len(rows) == 0:
            raise RuntimeError("No products in the database.")

        return rows 