from flask import Flask, request, jsonify
from models import db, Company, Warehouse, Product, Inventory, InventoryLog
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stockflow.db'
db.init_app(app)

# PART 1 & 2: PRODUCT CREATION WITH ATOMICITY
@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    required = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity', 'company_id']
    
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        sku = str(data['sku']).strip().upper()
        price = Decimal(str(data['price']))
        initial_qty = int(data['initial_quantity'])

        new_product = Product(
            name=data['name'].strip(),
            sku=sku,
            price=price,
            company_id=data['company_id']
        )
        db.session.add(new_product)
        db.session.flush() 

        new_inventory = Inventory(
            product_id=new_product.id,
            warehouse_id=data['warehouse_id'],
            quantity=initial_qty
        )
        db.session.add(new_inventory)
        db.session.commit()
        
        return jsonify({"message": "Success", "product_id": new_product.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "SKU Collision"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# PART 3: LOW STOCK ALERTS WITH PREDICTIVE LOGIC
@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):
    lookback_days = 30
    activity_cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    try:
        # Core query joining Inventory and Product
        results = db.session.query(Inventory, Product, Warehouse)\
            .join(Product, Inventory.product_id == Product.id)\
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)\
            .filter(Warehouse.company_id == company_id)\
            .filter(Inventory.quantity <= Product.low_stock_threshold).all()

        alerts_list = []
        for inv, prod, wh in results:
            # Calculate Velocity
            total_sales = db.session.query(func.abs(func.sum(InventoryLog.change_amount)))\
                .filter(InventoryLog.inventory_id == inv.id)\
                .filter(InventoryLog.change_amount < 0)\
                .filter(InventoryLog.created_at >= activity_cutoff).scalar() or 0
            
            daily_velocity = total_sales / lookback_days
            days_remaining = int(inv.quantity / daily_velocity) if daily_velocity > 0 else 999

            alerts_list.append({
                "product_name": prod.name,
                "current_stock": inv.quantity,
                "days_until_stockout": days_remaining,
                "warehouse": wh.name
            })

        return jsonify({"alerts": alerts_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Initialize SQLite DB
    app.run(debug=True)