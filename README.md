# Sales Order & Inventory Management — Savyant Systems Technical Assignment

A Flask + MySQL web app for a small trading company to manage customers,
products, multi-item sales orders, stock, and sales/stock reports.

## Tech stack
- Python 3.14, Flask 3.1.3
- MySQL 8.0 (MySQL Workbench / Local instance MySQL80)
- HTML / CSS / JavaScript (fetch API, no framework)
- bcrypt, mysql-connector-python, python-dotenv, pytest

## Setup
1. Create the database and load the schema + sample data in MySQL Workbench:
   - Run `schema.sql`
   - Run `seed.sql`
2. Copy `.env.example` to `.env` and set your real MySQL password in it:
