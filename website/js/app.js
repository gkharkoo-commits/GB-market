/**
 * GB MARKET — Main Application Frontend Logic
 */

let currentCategoryId = null;
let currentCity = "";
let currentSearch = "";
let currentSort = "newest";

async function loadCategories() {
  const container = document.getElementById("categories-container");
  if (!container) return;

  try {
    const categories = await apiFetch("/categories/");
    if (!categories || categories.length === 0) {
      container.innerHTML = `<p class="text-muted" style="padding:10px;">No categories available.</p>`;
      return;
    }

    container.innerHTML = categories.map(cat => `
      <div class="category-card ${currentCategoryId === cat.id ? 'active' : ''}" onclick="selectCategory(${cat.id})">
        <div class="category-icon">
          <i class="fa-solid ${cat.icon || 'fa-tag'}"></i>
        </div>
        <h4>${cat.name}</h4>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

async function loadProducts() {
  const grid = document.getElementById("products-grid");
  const countSpan = document.getElementById("products-count");
  if (!grid) return;

  grid.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
      <i class="fa-solid fa-spinner fa-spin fa-2x" style="color:var(--secondary);"></i>
      <p style="margin-top:10px; color:var(--text-muted);">Loading authentic Gilgit-Baltistan products...</p>
    </div>
  `;

  try {
    let url = `/products/?sort_by=${currentSort}&limit=24`;
    if (currentCategoryId) url += `&category_id=${currentCategoryId}`;
    if (currentCity) url += `&city=${encodeURIComponent(currentCity)}`;
    if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;

    const res = await apiFetch(url);
    const products = res.items || [];

    if (countSpan) countSpan.textContent = `${res.total || 0} products found`;

    if (products.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding: 40px; background:white; border-radius:var(--radius-md); border:1px dashed var(--border-color);">
          <i class="fa-solid fa-box-open fa-3x" style="color:var(--text-light); margin-bottom:12px;"></i>
          <h3>No products found</h3>
          <p class="text-muted" style="font-size:0.9rem; margin-top:6px;">Try adjusting your search terms or clearing the city filter.</p>
          <button class="btn btn-outline btn-sm" style="margin-top:14px;" onclick="resetFilters()">Reset Filters</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = products.map(p => {
      const img = p.images && p.images.length > 0 
        ? p.images[0].image_url 
        : 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80';
      
      const isOutOfStock = p.stock_quantity <= 0;

      return `
        <div class="product-card">
          <a href="/static/product-detail.html?slug=${p.slug}" class="product-img-wrapper">
            <img src="${img}" alt="${p.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80'">
            ${p.is_featured ? `<span class="badge-featured">Featured</span>` : ''}
            <span class="badge-stock">${isOutOfStock ? 'Out of Stock' : `${p.stock_quantity} in stock`}</span>
          </a>
          <div class="product-info">
            <span class="product-shop-name"><i class="fa-solid fa-store"></i> ${p.shop_name || 'Verified Vendor'}</span>
            <a href="/static/product-detail.html?slug=${p.slug}" class="product-title">${p.title}</a>
            <div class="product-price-row">
              <span class="price-pkr">PKR ${p.price.toLocaleString()}</span>
              ${p.original_price ? `<span class="original-price">PKR ${p.original_price.toLocaleString()}</span>` : ''}
            </div>
            <button class="btn-add-cart" ${isOutOfStock ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''} onclick="addToCart(${p.id})">
              <i class="fa-solid fa-cart-plus"></i> ${isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load products:", err);
    grid.innerHTML = `<p style="color:red; grid-column:1/-1;">Error loading products: ${err.message}</p>`;
  }
}

async function loadApprovedShops() {
  const grid = document.getElementById("shops-grid");
  if (!grid) return;

  try {
    const shops = await apiFetch("/shops/?limit=8");
    if (!shops || shops.length === 0) {
      grid.innerHTML = `<p class="text-muted">No shops registered yet.</p>`;
      return;
    }

    grid.innerHTML = shops.map(s => `
      <div class="shop-card">
        <img class="shop-cover" src="${s.exterior_image}" alt="${s.name}" onerror="this.src='https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=80'">
        <div class="shop-body">
          <h3 class="shop-title"><a href="/static/shop-detail.html?slug=${s.slug}">${s.name}</a></h3>
          <div class="shop-location"><i class="fa-solid fa-location-dot" style="color:var(--secondary);"></i> ${s.locality}, ${s.city}</div>
          <p class="shop-desc">${s.owner_name} &bull; Open: ${s.opening_hours}</p>
          <div class="shop-footer">
            <span><i class="fa-solid fa-shield-halved" style="color:var(--secondary);"></i> Verified Seller</span>
            <a href="/static/shop-detail.html?slug=${s.slug}" style="color:var(--primary); font-weight:600;">Visit Shop &rarr;</a>
          </div>
        </div>
      </div>
    `).join("");
  } catch (e) {
    console.error("Failed to load shops:", e);
  }
}

async function addToCart(productId, quantity = 1) {
  try {
    await apiFetch("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity })
    });
    updateCartCountBadge();
    showToast("Product added to cart!");
  } catch (err) {
    alert(err.message || "Could not add item to cart");
  }
}

function selectCategory(catId) {
  currentCategoryId = (currentCategoryId === catId) ? null : catId;
  loadCategories();
  loadProducts();
}

function handleSearch(e) {
  if (e) e.preventDefault();
  const searchInput = document.getElementById("search-input");
  const citySelect = document.getElementById("city-select");
  if (searchInput) currentSearch = searchInput.value.trim();
  if (citySelect) currentCity = citySelect.value;
  loadProducts();
}

function resetFilters() {
  currentCategoryId = null;
  currentCity = "";
  currentSearch = "";
  const searchInput = document.getElementById("search-input");
  const citySelect = document.getElementById("city-select");
  if (searchInput) searchInput.value = "";
  if (citySelect) citySelect.value = "";
  loadCategories();
  loadProducts();
}

function showToast(message) {
  let toast = document.getElementById("app-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "app-toast";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #0f172a;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 0.9rem;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      border-left: 4px solid #10b981;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: opacity 0.3s ease;
    `;
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<i class="fa-solid fa-check-circle" style="color:#10b981;"></i> ${message}`;
  toast.style.opacity = "1";
  setTimeout(() => {
    toast.style.opacity = "0";
  }, 2500);
}

document.addEventListener("DOMContentLoaded", () => {
  loadCategories();
  loadProducts();
  loadApprovedShops();

  const searchForm = document.getElementById("search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", handleSearch);
  }
  const citySelect = document.getElementById("city-select");
  if (citySelect) {
    citySelect.addEventListener("change", handleSearch);
  }
});
