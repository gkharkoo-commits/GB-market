from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    SHOPKEEPER = "shopkeeper"
    RIDER = "rider"
    ADMIN = "admin"

class ShopVerificationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    ARCHIVED = "archived"

class OrderStatus(str, Enum):
    PENDING_CONFIRMATION = "Pending Confirmation"
    CONFIRMED = "Confirmed"
    PREPARING = "Preparing"
    PACKED = "Packed"
    READY_FOR_PICKUP = "Ready for Pickup"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLATION_REQUESTED = "Cancellation Requested"
    CANCELLED = "Cancelled"
    DELIVERY_FAILED = "Delivery Failed"

class PaymentMethod(str, Enum):
    COD = "Cash on Delivery"

class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"

class CancellationStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class ComplaintStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
