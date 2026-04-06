# StockFlow B2B Inventory Management System
**Developer:** Rajesh Salunkhe  
**Case Study:** High-Performance Backend Engineering & Database Design

---

## Project Overview
StockFlow is a production-grade B2B Inventory Management solution designed to solve the common pitfalls of "happy-path" development. This project demonstrates the transition from a vulnerable prototype to a robust, multi-tenant SaaS architecture focusing on **Data Integrity**, **Atomicity**, and **Predictive Analytics**.

---

## Part 1: Code Review & Debugging (The "Production-Ready" Pivot)

### The Problem
A legacy implementation suffered from several critical production risks:
* **Atomic Failure:** Separate `commit()` calls led to "Ghost Products" (Catalog entry exists, but inventory record failed).
* **Floating Point Errors:** Using standard floats for currency caused accounting discrepancies.
* **SKU Collisions:** Lack of validation allowed duplicate SKUs, corrupting stock tracking.

### The Solution (Optimized API)
I refactored the product creation logic to guarantee reliability:
* **`db.session.flush()`:** Used to retrieve the new Product ID without finishing the transaction, maintaining ACID properties.
* **Decimal Arithmetic:** Switched to `Decimal` for 100% financial accuracy.
* **Input Sanitization:** Implemented `.strip().upper()` for SKUs to prevent human entry errors.

---

## 🗄 Part 2: Database Architecture (Relational Schema)

The system uses a highly normalized schema designed for SaaS scale.



### Strategic Design Decisions:
1. **Multi-Tenancy:** Applied `company_id` across all core tables for strict data isolation.
2. **Audit Trails:** Implemented `inventory_logs` to track every stock movement (Sales, Restocks, Returns) for financial compliance.
3. **Composite Constraints:** Used `UNIQUE(company_id, sku)`—allowing different companies to use the same SKU while preventing internal collisions.
4. **Bundle Logic:** A self-referencing `bundle_items` table allows for recursive "kits" (bundles inside bundles).

---

## Part 3: Predictive API & Business Logic

### The "Killer Feature": Stockout Prediction
Instead of a simple reactive dashboard, I built a proactive alerting system.

**Endpoint:** `GET /api/companies/<id>/alerts/low-stock`

**Logic Flow:**
* **Recent Activity Filter:** Only alerts on items with sales in the last 30 days to avoid "dead stock" clutter.
* **Sales Velocity Calculation:** Uses `func.abs(func.sum(InventoryLog.change_amount))` over a 30-day window.
* **Prediction:** Calculates `days_until_stockout` (Current Stock / Daily Velocity).

### Implementation Excellence:
* **N+1 Prevention:** Used complex joins and subqueries to pull Inventory, Product, Warehouse, and Supplier data in a single database hit.
* **Database Filtering:** Performed "Recent Sales" logic via a SQL subquery rather than in Python memory, ensuring performance scales with data growth.

---

##  Technical Stack
* **Language:** Python 3.x
* **Framework:** Flask (REST API)
* **ORM:** SQLAlchemy (Complex Joins & Transactions)
* **Database:** SQLite (Local) / PostgreSQL Ready (DDL included)
* **Data Handling:** Decimal Precision, Subqueries, Type Enforcement

---

## How to Run
1. **Environment Setup:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install flask flask-sqlalchemy