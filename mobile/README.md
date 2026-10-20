# GB MARKET — Android Application Architecture & API Guide

This directory contains the specifications, integration guidelines, and architecture for the future **GB MARKET Android Application**.

## 1. Architecture Overview

The backend of GB MARKET is built using **FastAPI** with RESTful endpoints, JSON request/response contracts, and standard JWT Bearer token authentication. Because of this decoupled architecture, the exact same backend, database, and business logic serve both the web frontend and mobile applications.

## 2. Recommended Mobile Technology Stack

- **Framework**: React Native with Expo (Managed Workflow)
- **Language**: TypeScript / JavaScript
- **Networking**: Axios or native `fetch`
- **State & Cache**: Redux Toolkit or Zustand + TanStack Query
- **Secure Storage**: `expo-secure-store` (for JWT access token storage in Android KeyStore)
- **UI Components**: React Native Paper or Tailwind (NativeWind)

## 3. Configurable API Endpoints

> [!IMPORTANT]
> Never hardcode `http://localhost:8000` inside an Android application APK. On Android emulators, `10.0.2.2:8000` maps to the host machine. On physical Android devices connected via local Wi-Fi, use your PC's LAN IP (e.g., `http://192.168.1.10:8000`). For public production, use your configured HTTPS domain.

### Environment Variable (`app.config.js` / `.env`):
```javascript
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "https://api.gbmarket.pk/api/v1";
```

## 4. Key Endpoints for Mobile Integration

### Authentication
- `POST /api/v1/auth/login`: `{ identifier, password }` -> `{ access_token, user_id, role, full_name }`
- `POST /api/v1/auth/register`: `{ full_name, email, phone, password, password_confirm, role }`
- `GET /api/v1/auth/me`: Validates JWT token and fetches user record.

### Catalog & Search
- `GET /api/v1/categories/`: Returns list of marketplace categories with icon and slug.
- `GET /api/v1/products/`: Parameters: `search`, `category_id`, `city`, `sort_by`, `page`, `limit`.
- `GET /api/v1/products/detail/{slug}`: Product details, image gallery, and seller information.
- `GET /api/v1/shops/`: List approved shops.
- `GET /api/v1/shops/detail/{slug}`: Shop profile and inventory.

### Cart & Checkout
- `GET /api/v1/cart/`: Cart items, quantities, and subtotal.
- `POST /api/v1/cart/items`: `{ product_id, quantity }`.
- `PUT /api/v1/cart/items/{id}`: `{ quantity }`.
- `DELETE /api/v1/cart/items/{id}`: Remove item.
- `POST /api/v1/orders/checkout`: Place order with Cash on Delivery (COD).

### Customer Orders & Tracking
- `GET /api/v1/orders/my-orders`: List user's orders with current status.
- `GET /api/v1/orders/{id}`: Order details, items snapshot, and chronological status history.
- `POST /api/v1/orders/cancel-request`: Request cancellation with reason.

### Merchant & Rider Operations
- `GET /api/v1/products/seller/my-products`: Merchant catalog management.
- `POST /api/v1/products/`: Merchant add product with multi-image upload.
- `GET /api/v1/orders/seller/my-orders`: Merchant fulfillment dashboard.
- `PUT /api/v1/orders/seller/order-groups/{id}/status`: Transition status: Confirmed -> Preparing -> Packed -> Ready for Pickup.
- `GET /api/v1/deliveries/my-deliveries`: Rider delivery assignments.
- `PUT /api/v1/deliveries/{id}/status`: Rider transition: Picked Up -> Out for Delivery -> Delivered.

## 5. Building and Distributing APK Without Google Play Fees

1. Initialize Expo project:
   ```bash
   npx create-expo-app@latest gb-market-mobile --template blank-typescript
   ```
2. Build an Android standalone APK (debug/testing) using EAS:
   ```bash
   npx eas-cli build -p android --profile preview
   ```
3. Direct Distribution:
   - The resulting `.apk` file can be downloaded directly and installed onto any Android device.
   - Share via USB cable, Bluetooth, or local network file transfer.
