# GB MARKET — Comprehensive User & Operational Guide

This guide describes the user journeys and responsibilities for all four marketplace roles: **Visitors / Customers**, **Shopkeepers (Merchants)**, **Delivery Riders**, and the **Administrator**.

---

## 1. For Customers & Visitors

### Browsing & Searching:
1. Open the homepage: [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html).
2. Filter by your district (e.g., Gilgit, Skardu, Hunza) or select a category card (e.g. Dry Fruits, Handicrafts).
3. Click any product card to view detailed photos, stock availability, and shopkeeper information.

### Shopping & Placing Orders:
1. Click **Add to Cart** or choose your desired quantity on the product page.
2. Open your Cart by clicking the Cart icon in the navbar.
3. Review item quantities and subtotal, then click **Proceed to Checkout**.
4. Enter your delivery recipient name, mobile number, city, locality, and complete physical address.
5. Select **Cash on Delivery (COD)** and click **Confirm & Place Order**.
6. You will receive an immediate confirmation and Order ID (e.g. `GBM-20261020-001`).

### Order Tracking & Cancellation:
1. Navigate to **My Orders** ([/static/my-orders.html](http://127.0.0.1:8000/static/my-orders.html)).
2. Click **Track & Details** on any order to view the chronological timeline:
   - `Pending Confirmation` -> `Confirmed` -> `Preparing` -> `Packed` -> `Ready for Pickup` -> `Out for Delivery` -> `Delivered`.
3. If you placed an order in error, click **Request Cancellation** before the order is dispatched. If the order is still `Pending Confirmation`, cancellation is processed immediately and stock is released back to the store.

---

## 2. For Shopkeepers (Vendors)

### Registering Your Shop:
1. Create a user account at [Register](http://127.0.0.1:8000/static/register.html) selecting "Sell products as a Shopkeeper".
2. Go to **Register Your Shop** ([/static/shop-register.html](http://127.0.0.1:8000/static/shop-register.html)).
3. Enter your Shop Name, Owner Full Name, Mobile Contact, Category, City, Bazar, Address, and Description.
4. Upload a clear photograph of your **Shop Front / Exterior Signboard** (mandatory for verification).
5. Accept platform terms and click **Submit Shop Registration for Review**.
6. Your application status will display as `Pending`.

### Adding Products (After Approval):
1. Once approved by the administrator, navigate to **Seller Hub** ([/static/seller/index.html](http://127.0.0.1:8000/static/seller/index.html)).
2. Go to **Manage Products** ([/static/seller/products.html](http://127.0.0.1:8000/static/seller/products.html)).
3. Click **Add New Product**.
4. Enter Product Title, Category, Price in PKR, Available Stock Quantity, Unit, and upload a product photo.
5. Click **Save Product**. Your product is now live in the marketplace!

### Processing Customer Orders:
1. When a customer orders your product, it appears in **Customer Orders** ([/static/seller/orders.html](http://127.0.0.1:8000/static/seller/orders.html)).
2. Click **Update Status** as you fulfill the order:
   - Select `Confirmed` to accept the order.
   - Select `Preparing` when gathering items.
   - Select `Packed` when items are boxed and sealed.
   - Select `Ready for Pickup` when awaiting rider collection.
3. Review your **Seller Net Payout** (Subtotal minus platform commission).

---

## 3. For Delivery Riders

### Operating Deliveries:
1. Log in to the **Rider Portal** ([/static/rider/index.html](http://127.0.0.1:8000/static/rider/index.html)).
2. Review your assigned orders:
   - **Pickup Location**: Shopkeeper's address and contact number.
   - **Drop-off Destination**: Customer's address and phone number.
3. Click **Update**:
   - Select `Picked Up` after receiving the package from the merchant.
   - Select `Out for Delivery` while on your way.
   - Select `Delivered` upon handing the package to the customer and collecting COD payment.
   - If unreachable or road blocked, select `Delivery Failed` and record the reason.

---

## 4. For Administrators

### Accessing the Control Center:
1. Log in using your administrator credentials at [Login](http://127.0.0.1:8000/static/login.html).
2. Open the **Admin Control Center** ([/static/admin/index.html](http://127.0.0.1:8000/static/admin/index.html)).

### Key Administrative Actions:
- **Review Shop Applications** ([/static/admin/shops.html](http://127.0.0.1:8000/static/admin/shops.html)):
  - Inspect submitted storefront exterior images and merchant phone numbers.
  - Click **Review & Decision** -> Choose `Approve`, `Reject`, or `Suspend` with a note.
- **Review Cancellations** ([/static/admin/orders.html](http://127.0.0.1:8000/static/admin/orders.html)):
  - Review customer cancellation reasons.
  - Approve cancellation (which automatically restores item inventory back into the store).
- **Manage Users & Roles** ([/static/admin/users.html](http://127.0.0.1:8000/static/admin/users.html)):
  - Change user roles between `Customer`, `Shopkeeper`, `Rider`, and `Admin`.
  - Suspend or reactivate user accounts.
- **Platform Configuration** ([/static/admin/settings.html](http://127.0.0.1:8000/static/admin/settings.html)):
  - Adjust platform sales commission percentage.
  - Set default delivery fee and configure regional delivery fees per district.
