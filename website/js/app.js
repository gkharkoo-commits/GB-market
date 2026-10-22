/**
 * GB MARKET — Main Application Frontend Logic
 * Version 3.0 — Enhanced Responsive Marketplace System
 */

let currentCategoryId = null;
let currentCity = "";
let currentSearch = "";
let currentSort = "newest";

// ==============================================================================
// 1. Wishlist System (Local Storage with Live Counter & Drawer)
// ==============================================================================

function getWishlist() {
  try {
    const list = localStorage.getItem("gbm_wishlist");
    return list ? JSON.parse(list) : [];
  } catch (e) {
    return [];
  }
}

function saveWishlist(items) {
  localStorage.setItem("gbm_wishlist", JSON.stringify(items));
  updateWishlistUI();
}

function isWishlisted(productId) {
  const list = getWishlist();
  return list.some(item => Number(item.id) === Number(productId));
}

function toggleWishlist(product) {
  if (!product || !product.id) return;
  let list = getWishlist();
  const exists = list.some(item => Number(item.id) === Number(product.id));

  if (exists) {
    list = list.filter(item => Number(item.id) !== Number(product.id));
    saveWishlist(list);
    showToast("Removed from your Wishlist");
  } else {
    list.push({
      id: product.id,
      title: product.title || "Gilgit-Baltistan Product",
      price: product.price || 0,
      slug: product.slug || "",
      image: product.image || "/GB-market/static/assets/prod-almonds.jpg",
      shop_name: product.shop_name || "Verified Local Shop"
    });
    saveWishlist(list);
    showToast("Saved to your Wishlist!");
  }

  // Update any visible heart buttons
  updateHeartButtons();
}

function updateWishlistUI() {
  const list = getWishlist();
  const count = list.length;

  // Header badges
  const badges = document.querySelectorAll("#wishlist-count-badge, .wishlist-count-badge");
  badges.forEach(b => {
    b.textContent = count;
  });

  const drawerCount = document.getElementById("wishlist-drawer-count");
  if (drawerCount) drawerCount.textContent = count;

  renderWishlistDrawerItems();
  updateHeartButtons();
}

function updateHeartButtons() {
  const list = getWishlist();
  const wishlistedIds = new Set(list.map(i => Number(i.id)));

  document.querySelectorAll("[data-wishlist-id]").forEach(btn => {
    const id = Number(btn.getAttribute("data-wishlist-id"));
    const icon = btn.querySelector("i");
    if (wishlistedIds.has(id)) {
      btn.classList.add("active");
      if (icon) {
        icon.className = "fa-solid fa-heart";
      }
    } else {
      btn.classList.remove("active");
      if (icon) {
        icon.className = "fa-regular fa-heart";
      }
    }
  });
}

function openWishlistDrawer() {
  const drawer = document.getElementById("wishlist-drawer");
  const backdrop = document.getElementById("wishlist-drawer-backdrop");
  if (drawer && backdrop) {
    drawer.classList.add("open");
    backdrop.style.display = "block";
    renderWishlistDrawerItems();
  }
}

function closeWishlistDrawer() {
  const drawer = document.getElementById("wishlist-drawer");
  const backdrop = document.getElementById("wishlist-drawer-backdrop");
  if (drawer && backdrop) {
    drawer.classList.remove("open");
    backdrop.style.display = "none";
  }
}

function renderWishlistDrawerItems() {
  const container = document.getElementById("wishlist-items-container");
  if (!container) return;

  const list = getWishlist();
  if (list.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding: 48px 16px; color: var(--text-muted);">
        <i class="fa-regular fa-heart fa-3x" style="color: #cbd5e1; margin-bottom: 12px; display:block;"></i>
        <h4 style="color: var(--primary-dark); font-weight:700;">Your Wishlist is Empty</h4>
        <p style="font-size:0.85rem; margin-top:6px; color:#64748b;">Save products you love from Skardu, Gilgit, Hunza and valleys.</p>
        <button class="btn btn-primary btn-sm" style="margin-top:16px;" onclick="closeWishlistDrawer(); scrollToSection('products-section');">
          Explore Products
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = list.map(item => `
    <div class="wishlist-item-card">
      <img src="${item.image}" alt="${item.title}" onerror="this.src='/GB-market/static/assets/prod-almonds.jpg'" class="wishlist-item-img">
      <div class="wishlist-item-details">
        <a href="/GB-market/static/product-detail.html?slug=${item.slug}" class="wishlist-item-title">${item.title}</a>
        <div class="wishlist-item-shop"><i class="fa-solid fa-store"></i> ${item.shop_name}</div>
        <div class="wishlist-item-price">PKR ${(item.price || 0).toLocaleString()}</div>
        <div class="wishlist-item-actions">
          <button class="btn-wishlist-cart" onclick="moveWishlistToCart(${item.id})">
            <i class="fa-solid fa-cart-shopping"></i> Add to Cart
          </button>
          <button class="btn-wishlist-remove" onclick="removeWishlistItem(${item.id})" title="Remove item">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </div>
    </div>
  `).join("");
}

async function moveWishlistToCart(productId) {
  try {
    await addToCart(productId, 1);
    removeWishlistItem(productId);
    showToast("Moved item to cart!");
  } catch (err) {
    console.error("Move to cart error:", err);
  }
}

function removeWishlistItem(productId) {
  let list = getWishlist();
  list = list.filter(item => Number(item.id) !== Number(productId));
  saveWishlist(list);
}


// ==============================================================================
// 2. Hero Banner Slider (Auto-Slide, Touch Swipe, Arrows, Indicators)
// ==============================================================================

let currentSlideIndex = 0;
let slideInterval = null;
const SLIDE_DURATION = 5000;

function initHeroSlider() {
  const slider = document.getElementById("gbm-hero-slider");
  const track = document.getElementById("gbm-slider-track");
  const slides = document.querySelectorAll(".gbm-slide");
  const dots = document.querySelectorAll(".gbm-dot");
  const prevBtn = document.getElementById("slider-prev-btn");
  const nextBtn = document.getElementById("slider-next-btn");

  if (!slider || !track || slides.length === 0) return;

  function goToSlide(index) {
    if (index < 0) {
      currentSlideIndex = slides.length - 1;
    } else if (index >= slides.length) {
      currentSlideIndex = 0;
    } else {
      currentSlideIndex = index;
    }

    track.style.transform = `translateX(-${currentSlideIndex * 100}%)`;

    slides.forEach((slide, i) => {
      slide.classList.toggle("active", i === currentSlideIndex);
    });

    dots.forEach((dot, i) => {
      dot.classList.toggle("active", i === currentSlideIndex);
    });
  }

  function nextSlide() {
    goToSlide(currentSlideIndex + 1);
  }

  function prevSlide() {
    goToSlide(currentSlideIndex - 1);
  }

  function startAutoPlay() {
    stopAutoPlay();
    slideInterval = setInterval(nextSlide, SLIDE_DURATION);
  }

  function stopAutoPlay() {
    if (slideInterval) {
      clearInterval(slideInterval);
      slideInterval = null;
    }
  }

  // Arrow controls
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      nextSlide();
      startAutoPlay();
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      prevSlide();
      startAutoPlay();
    });
  }

  // Dot controls
  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => {
      goToSlide(i);
      startAutoPlay();
    });
  });

  // Pause on hover
  slider.addEventListener("mouseenter", stopAutoPlay);
  slider.addEventListener("mouseleave", startAutoPlay);

  // Touch / Swipe gestures for mobile & tablets
  let startX = 0;
  let startY = 0;
  let isSwiping = false;

  slider.addEventListener("touchstart", (e) => {
    stopAutoPlay();
    if (e.touches.length === 1) {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      isSwiping = true;
    }
  }, { passive: true });

  slider.addEventListener("touchmove", (e) => {
    if (!isSwiping || e.touches.length !== 1) return;
    const currentX = e.touches[0].clientX;
    const currentY = e.touches[0].clientY;
    const diffX = startX - currentX;
    const diffY = startY - currentY;

    // Prevent vertical interference if horizontal swipe is dominant
    if (Math.abs(diffX) > Math.abs(diffY)) {
      e.preventDefault();
    }
  }, { passive: false });

  slider.addEventListener("touchend", (e) => {
    if (!isSwiping) return;
    isSwiping = false;
    const endX = e.changedTouches[0].clientX;
    const diffX = startX - endX;
    const threshold = 40; // minimum pixels to count as swipe

    if (diffX > threshold) {
      nextSlide();
    } else if (diffX < -threshold) {
      prevSlide();
    }
    startAutoPlay();
  }, { passive: true });

  // Keyboard navigation when slider area is in view
  document.addEventListener("keydown", (e) => {
    const rect = slider.getBoundingClientRect();
    const inView = rect.top < window.innerHeight && rect.bottom > 0;
    if (!inView) return;

    if (e.key === "ArrowLeft") {
      prevSlide();
      startAutoPlay();
    } else if (e.key === "ArrowRight") {
      nextSlide();
      startAutoPlay();
    }
  });

  goToSlide(0);
  startAutoPlay();
}


// ==============================================================================
// 3. Category System & Navigation
// ==============================================================================

async function loadCategories() {
  const container = document.getElementById("categories-container");
  const sidebarContainer = document.getElementById("sidebar-categories-container");
  const dropdownContainer = document.getElementById("dropdown-categories-container");

  try {
    const categories = await apiFetch("/categories/");
    if (!categories || categories.length === 0) {
      if (container) container.innerHTML = `<p class="text-muted" style="padding:10px;">No categories available.</p>`;
      return;
    }

    // Horizontal category scroll bar
    if (container) {
      container.innerHTML = categories.map(cat => `
        <div class="category-card ${currentCategoryId === cat.id ? 'active' : ''}" onclick="selectCategory(${cat.id})">
          <div class="category-icon">
            <i class="fa-solid ${cat.icon || 'fa-tag'}"></i>
          </div>
          <h4>${cat.name}</h4>
        </div>
      `).join("");
    }

    // Left Column Sidebar categories
    if (sidebarContainer) {
      sidebarContainer.innerHTML = categories.map(cat => `
        <a href="javascript:void(0)" onclick="selectCategory(${cat.id})" class="gbm-cat-link ${currentCategoryId === cat.id ? 'active' : ''}">
          <div class="gbm-cat-left">
            <span class="gbm-cat-icon"><i class="fa-solid ${cat.icon || 'fa-tag'}"></i></span>
            <span>${cat.name}</span>
          </div>
          <i class="fa-solid fa-chevron-right"></i>
        </a>
      `).join("");
    }

    // Subnav dropdown categories (for mobile or all-cats toggle)
    if (dropdownContainer) {
      dropdownContainer.innerHTML = categories.map(cat => `
        <a href="javascript:void(0)" onclick="selectCategory(${cat.id}); toggleCategoryMenu(false);" class="gbm-dropdown-cat-item">
          <i class="fa-solid ${cat.icon || 'fa-tag'}"></i>
          <span>${cat.name}</span>
        </a>
      `).join("");
    }

  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

function selectCategory(catId) {
  currentCategoryId = (currentCategoryId === catId) ? null : catId;
  loadCategories();
  loadProducts();
  updateActiveFilterTags();
  scrollToSection("products-section");
}

function toggleCategoryMenu(forceState) {
  const menu = document.getElementById("gbm-category-dropdown");
  if (!menu) return;
  if (typeof forceState === "boolean") {
    menu.classList.toggle("open", forceState);
  } else {
    menu.classList.toggle("open");
  }
}


// ==============================================================================
// 4. Featured Products Block (Center Column)
// ==============================================================================

async function loadFeaturedProducts() {
  const container = document.getElementById("featured-products-grid");
  if (!container) return;

  try {
    const res = await apiFetch("/products/?limit=4");
    const products = res.items || [];

    if (products.length === 0) {
      return; // Keep existing static placeholders if empty
    }

    container.innerHTML = products.map(p => {
      const img = p.images && p.images.length > 0
        ? p.images[0].image_url
        : "/GB-market/static/assets/prod-almonds.jpg";
      const isOutOfStock = p.stock_quantity <= 0;
      const isSaved = isWishlisted(p.id);

      return `
        <div class="gbm-product-card">
          <div class="gbm-product-img-box">
            <a href="/GB-market/static/product-detail.html?slug=${p.slug}">
              <img src="${img}" alt="${p.title}" loading="lazy" onerror="this.src='/GB-market/static/assets/prod-almonds.jpg'">
            </a>
            <button type="button" class="btn-wishlist ${isSaved ? 'active' : ''}" data-wishlist-id="${p.id}" onclick="handleWishlistClick(event, ${p.id}, '${escapeQuote(p.title)}', ${p.price}, '${p.slug}', '${img}', '${escapeQuote(p.shop_name || '')}')" title="Save to Wishlist">
              <i class="${isSaved ? 'fa-solid' : 'fa-regular'} fa-heart"></i>
            </button>
          </div>
          <div class="gbm-product-body">
            <a href="/GB-market/static/product-detail.html?slug=${p.slug}" class="gbm-prod-title" title="${p.title}">${p.title}</a>
            <span class="gbm-prod-cat"><i class="fa-solid fa-store"></i> ${p.shop_name || 'Verified Merchant'}</span>
            <div class="gbm-prod-rating">
              <i class="fa-solid fa-star"></i> 4.8 <span>(${p.stock_quantity} in stock)</span>
            </div>
            <div class="gbm-prod-price">PKR ${p.price.toLocaleString()}</div>
            <button class="gbm-btn-add" ${isOutOfStock ? 'disabled style="opacity:0.6;cursor:not-allowed;"' : ''} onclick="addToCart(${p.id})">
              <i class="fa-solid fa-cart-shopping"></i> ${isOutOfStock ? 'Sold Out' : 'Add to Cart'}
            </button>
          </div>
        </div>
      `;
    }).join("");

    updateHeartButtons();
  } catch (err) {
    console.warn("Could not load dynamic featured products, falling back:", err);
  }
}

function handleWishlistClick(event, id, title, price, slug, image, shop_name) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  toggleWishlist({ id, title, price, slug, image, shop_name });
}

function escapeQuote(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}


// ==============================================================================
// 5. Complete Marketplace Catalog (Dynamic Grid)
// ==============================================================================

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
    let url = `/products/?sort_by=${currentSort}&limit=32`;
    if (currentCategoryId) url += `&category_id=${currentCategoryId}`;
    if (currentCity) url += `&city=${encodeURIComponent(currentCity)}`;
    if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;

    const res = await apiFetch(url);
    const products = res.items || [];

    if (countSpan) countSpan.textContent = `${res.total || 0} products available`;

    if (products.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding: 50px 20px; background:white; border-radius:var(--radius-md); border:1px dashed var(--border-color);">
          <i class="fa-solid fa-box-open fa-3x" style="color:var(--text-light); margin-bottom:12px;"></i>
          <h3 style="color:var(--primary-dark); font-weight:700;">No products match your criteria</h3>
          <p class="text-muted" style="font-size:0.9rem; margin-top:6px;">Try clearing filters or search with another term.</p>
          <button class="btn btn-outline btn-sm" style="margin-top:14px;" onclick="resetFilters()">Reset All Filters</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = products.map(p => {
      const img = p.images && p.images.length > 0 
        ? p.images[0].image_url 
        : '/GB-market/static/assets/prod-almonds.jpg';
      
      const isOutOfStock = p.stock_quantity <= 0;
      const isSaved = isWishlisted(p.id);

      return `
        <div class="product-card">
          <div class="product-img-wrapper">
            <a href="/GB-market/static/product-detail.html?slug=${p.slug}">
              <img src="${img}" alt="${p.title}" loading="lazy" onerror="this.src='/GB-market/static/assets/prod-almonds.jpg'">
            </a>
            ${p.is_featured ? `<span class="badge-featured"><i class="fa-solid fa-star"></i> Featured</span>` : ''}
            <span class="badge-stock ${isOutOfStock ? 'out-of-stock' : ''}">${isOutOfStock ? 'Out of Stock' : `${p.stock_quantity} in stock`}</span>
            <button type="button" class="btn-wishlist ${isSaved ? 'active' : ''}" data-wishlist-id="${p.id}" onclick="handleWishlistClick(event, ${p.id}, '${escapeQuote(p.title)}', ${p.price}, '${p.slug}', '${img}', '${escapeQuote(p.shop_name || '')}')" title="Save to Wishlist">
              <i class="${isSaved ? 'fa-solid' : 'fa-regular'} fa-heart"></i>
            </button>
          </div>
          <div class="product-info">
            <span class="product-shop-name"><i class="fa-solid fa-store"></i> ${p.shop_name || 'Verified Vendor'}</span>
            <a href="/GB-market/static/product-detail.html?slug=${p.slug}" class="product-title">${p.title}</a>
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

    updateHeartButtons();
  } catch (err) {
    console.error("Failed to load products:", err);
    grid.innerHTML = `<p style="color:red; grid-column:1/-1; text-align:center; padding:30px;">Error loading products: ${err.message}</p>`;
  }
}

function updateActiveFilterTags() {
  const container = document.getElementById("active-filters-bar");
  if (!container) return;

  let tags = [];
  if (currentCategoryId) {
    tags.push(`
      <span class="filter-pill">
        Category Active
        <button onclick="selectCategory(${currentCategoryId})" aria-label="Clear Category">&times;</button>
      </span>
    `);
  }
  if (currentCity) {
    tags.push(`
      <span class="filter-pill">
        City: ${currentCity}
        <button onclick="clearCityFilter()" aria-label="Clear City">&times;</button>
      </span>
    `);
  }
  if (currentSearch) {
    tags.push(`
      <span class="filter-pill">
        Search: "${currentSearch}"
        <button onclick="clearSearchFilter()" aria-label="Clear Search">&times;</button>
      </span>
    `);
  }

  if (tags.length > 0) {
    container.style.display = "flex";
    container.innerHTML = `
      <span style="font-size:0.8rem; font-weight:700; color:var(--text-muted);">Active Filters:</span>
      ${tags.join("")}
      <button class="btn-clear-all" onclick="resetFilters()">Clear All</button>
    `;
  } else {
    container.style.display = "none";
    container.innerHTML = "";
  }
}

function clearCityFilter() {
  currentCity = "";
  const citySelect = document.getElementById("city-select");
  if (citySelect) citySelect.value = "";
  loadProducts();
  updateActiveFilterTags();
}

function clearSearchFilter() {
  currentSearch = "";
  const searchInput = document.getElementById("search-input");
  if (searchInput) searchInput.value = "";
  loadProducts();
  updateActiveFilterTags();
}


// ==============================================================================
// 6. Featured Shops Section
// ==============================================================================

async function loadApprovedShops() {
  const grid = document.getElementById("shops-grid");
  if (!grid) return;

  try {
    const shops = await apiFetch("/shops/?limit=8");
    if (!shops || shops.length === 0) {
      grid.innerHTML = `<p class="text-muted" style="grid-column:1/-1; text-align:center; padding:20px;">No registered shops found.</p>`;
      return;
    }

    grid.innerHTML = shops.map(s => `
      <div class="shop-card">
        <img class="shop-cover" src="${s.exterior_image || '/GB-market/static/assets/hero-banner-gb.jpg'}" alt="${s.name}" onerror="this.src='/GB-market/static/assets/hero-banner-gb.jpg'">
        <div class="shop-body">
          <h3 class="shop-title"><a href="/GB-market/static/shop-detail.html?slug=${s.slug}">${s.name}</a></h3>
          <div class="shop-location"><i class="fa-solid fa-location-dot" style="color:var(--secondary);"></i> ${s.locality}, ${s.city}</div>
          <p class="shop-desc">${s.owner_name} &bull; Open: ${s.opening_hours || '9:00 AM - 9:00 PM'}</p>
          <div class="shop-footer">
            <span><i class="fa-solid fa-shield-halved" style="color:var(--secondary);"></i> Verified Seller</span>
            <a href="/GB-market/static/shop-detail.html?slug=${s.slug}" style="color:var(--primary); font-weight:700;">Visit Shop &rarr;</a>
          </div>
        </div>
      </div>
    `).join("");
  } catch (e) {
    console.error("Failed to load shops:", e);
  }
}


// ==============================================================================
// 7. Cart & Orders Actions
// ==============================================================================

async function addToCart(productId, quantity = 1) {
  try {
    await apiFetch("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity })
    });
    if (typeof updateCartCountBadge === "function") {
      updateCartCountBadge();
    }
    showToast("Product added to your cart!");
  } catch (err) {
    showToast(err.message || "Could not add item to cart", "error");
  }
}

function handleSearch(e) {
  if (e) e.preventDefault();
  const searchInput = document.getElementById("search-input");
  const citySelect = document.getElementById("city-select");
  if (searchInput) currentSearch = searchInput.value.trim();
  if (citySelect) currentCity = citySelect.value;
  loadProducts();
  updateActiveFilterTags();
  scrollToSection("products-section");
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
  updateActiveFilterTags();
}


// ==============================================================================
// 8. Interactive Modals (FAQ, Shipping, Return, About, Contact)
// ==============================================================================

function openModal(title, contentHtml) {
  let modal = document.getElementById("gbm-info-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "gbm-info-modal";
    modal.className = "gbm-modal";
    modal.onclick = (e) => {
      if (e.target === modal) closeInfoModal();
    };
    modal.innerHTML = `
      <div class="gbm-modal-dialog">
        <div class="gbm-modal-header">
          <h3 id="gbm-modal-title" class="gbm-modal-title"></h3>
          <button type="button" class="gbm-modal-close" onclick="closeInfoModal()" aria-label="Close modal">&times;</button>
        </div>
        <div id="gbm-modal-body" class="gbm-modal-body"></div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  document.getElementById("gbm-modal-title").textContent = title;
  document.getElementById("gbm-modal-body").innerHTML = contentHtml;
  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeInfoModal() {
  const modal = document.getElementById("gbm-info-modal");
  if (modal) {
    modal.style.display = "none";
    document.body.style.overflow = "";
  }
}

function openFAQModal() {
  const content = `
    <div class="modal-faq-list">
      <div class="modal-faq-item">
        <h4><i class="fa-solid fa-circle-question" style="color:var(--secondary);"></i> How does Cash on Delivery (COD) work?</h4>
        <p>You pay in cash only when your order is delivered to your designated address in Gilgit-Baltistan. No credit card or advance bank transfer is required.</p>
      </div>
      <div class="modal-faq-item">
        <h4><i class="fa-solid fa-circle-question" style="color:var(--secondary);"></i> How are local vendors verified?</h4>
        <p>Every shopkeeper must provide their physical storefront photo, CNIC, and location in Skardu, Gilgit, Hunza, Nagar, etc. An administrator manually reviews and verifies their store before activation.</p>
      </div>
      <div class="modal-faq-item">
        <h4><i class="fa-solid fa-circle-question" style="color:var(--secondary);"></i> What is the standard delivery timeframe?</h4>
        <p>Deliveries within the same district (e.g. Gilgit to Jutial or Skardu to Bazar) typically arrive within 24 hours. Inter-district shipments take 1-2 days.</p>
      </div>
      <div class="modal-faq-item">
        <h4><i class="fa-solid fa-circle-question" style="color:var(--secondary);"></i> Can I cancel my order?</h4>
        <p>Yes. You can cancel your order directly from your <a href="/GB-market/static/my-orders.html" style="color:var(--secondary); font-weight:700;">My Orders</a> page as long as the merchant has not yet dispatched it.</p>
      </div>
    </div>
  `;
  openModal("Frequently Asked Questions", content);
}

function openShippingModal() {
  const content = `
    <div style="font-size:0.92rem; line-height:1.6; color:#334155;">
      <p style="margin-bottom:14px;"><strong>GB MARKET</strong> operates an integrated regional logistics and rider delivery network spanning all 10 districts of Gilgit-Baltistan.</p>
      
      <div style="background:#f1f5f9; padding:14px; border-radius:8px; margin-bottom:16px;">
        <h5 style="color:var(--primary-dark); font-weight:700; margin-bottom:8px;">Standard Delivery Rates</h5>
        <ul style="padding-left:20px; font-size:0.85rem;">
          <li><strong>Gilgit City & Jutial:</strong> PKR 150 (Estimated 24 hours)</li>
          <li><strong>Skardu City & Bazar:</strong> PKR 150 (Estimated 24 hours)</li>
          <li><strong>Hunza, Nagar & Ghizer:</strong> PKR 200 - 250 (Estimated 1-2 days)</li>
          <li><strong>Diamer, Astore, Ghanche, Shigar:</strong> PKR 250 - 300 (Estimated 2 days)</li>
        </ul>
      </div>

      <p><i class="fa-solid fa-gift" style="color:var(--secondary);"></i> <strong>Free Shipping:</strong> All orders with a subtotal above <strong>PKR 5,000</strong> receive 100% free delivery across Gilgit-Baltistan.</p>
    </div>
  `;
  openModal("Shipping & Delivery Policy", content);
}

function openReturnModal() {
  const content = `
    <div style="font-size:0.92rem; line-height:1.6; color:#334155;">
      <h4 style="color:var(--primary-dark); margin-bottom:8px; font-weight:700;">7-Day Easy Return Policy</h4>
      <p style="margin-bottom:12px;">Customer satisfaction is our highest priority. If an item arrives damaged, expired, or does not match its catalog description:</p>
      
      <ol style="padding-left:20px; margin-bottom:16px; font-size:0.88rem;">
        <li style="margin-bottom:6px;">Contact our regional support helpline at <strong>0349 8188394</strong> within 7 days of package receipt.</li>
        <li style="margin-bottom:6px;">Provide your Order ID and a clear photo of the delivered item.</li>
        <li>Our delivery rider will collect the item and provide an immediate exchange or full cash refund upon inspection.</li>
      </ol>

      <p style="background:#ecfdf5; border-left:4px solid #059669; padding:10px 14px; font-size:0.85rem; color:#065f46;">
        <i class="fa-solid fa-circle-check"></i> Authentic Gilgit-Baltistan sourcing guarantees fresh organic products.
      </p>
    </div>
  `;
  openModal("Return & Exchange Policy", content);
}

function openAboutModal() {
  const content = `
    <div style="font-size:0.92rem; line-height:1.6; color:#334155;">
      <p style="margin-bottom:12px;"><strong>GB MARKET</strong> is the dedicated multi-vendor digital commerce marketplace created specifically for the region of <strong>Gilgit-Baltistan, Pakistan</strong>.</p>
      <p style="margin-bottom:12px;">Our goal is to connect local shopkeepers, mountain farmers, and traditional artisans in Skardu, Gilgit, Hunza, Nagar, Ghizer, Diamer, Astore, Shigar, Kharmang, and Ghanche directly with buyers across the region and country.</p>
      <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 16px; margin-top:14px; font-size:0.85rem;">
        <div><strong>Lead Developer:</strong> Abdul Sattar</div>
        <div><strong>Headquarters:</strong> Gilgit-Baltistan, Pakistan</div>
        <div><strong>Support:</strong> sattar.kharkoo@gmail.com &bull; 0349 8188394</div>
      </div>
    </div>
  `;
  openModal("About GB MARKET", content);
}

function openContactModal() {
  const content = `
    <div style="font-size:0.92rem; line-height:1.6; color:#334155;">
      <p style="margin-bottom:16px;">Have questions about placing an order, registering as a merchant, or tracking a package? Contact our dedicated support team:</p>
      <div style="display:flex; flex-direction:column; gap:12px;">
        <a href="tel:03498188394" class="btn btn-outline" style="display:flex; align-items:center; gap:10px; justify-content:center;">
          <i class="fa-solid fa-phone" style="color:var(--secondary);"></i> Call Helpline: 0349 8188394
        </a>
        <a href="https://wa.me/923498188394" target="_blank" class="btn btn-success" style="display:flex; align-items:center; gap:10px; justify-content:center; color:white;">
          <i class="fa-brands fa-whatsapp"></i> Chat on WhatsApp
        </a>
        <a href="mailto:sattar.kharkoo@gmail.com" class="btn btn-outline" style="display:flex; align-items:center; gap:10px; justify-content:center;">
          <i class="fa-solid fa-envelope"></i> Email: sattar.kharkoo@gmail.com
        </a>
      </div>
    </div>
  `;
  openModal("Customer Support & Contact", content);
}


// ==============================================================================
// 9. Toast Notifications & Utility Helpers
// ==============================================================================

function showToast(message, type = "success") {
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
      z-index: 100000;
      box-shadow: 0 6px 16px rgba(0,0,0,0.2);
      border-left: 4px solid #10b981;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: opacity 0.3s ease, transform 0.3s ease;
      transform: translateY(20px);
      opacity: 0;
      pointer-events: none;
    `;
    document.body.appendChild(toast);
  }

  const isErr = type === "error";
  toast.style.borderLeftColor = isErr ? "#ef4444" : "#10b981";
  toast.innerHTML = `<i class="fa-solid ${isErr ? 'fa-circle-exclamation' : 'fa-check-circle'}" style="color:${isErr ? '#ef4444' : '#10b981'};"></i> ${message}`;
  
  toast.style.pointerEvents = "auto";
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(20px)";
    toast.style.pointerEvents = "none";
  }, 2800);
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function parseUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const cat = params.get("cat");
  const city = params.get("city");
  const search = params.get("search");

  if (cat) currentCategoryId = parseInt(cat);
  if (city) {
    currentCity = city;
    const citySelect = document.getElementById("city-select");
    if (citySelect) citySelect.value = city;
  }
  if (search) {
    currentSearch = search;
    const searchInput = document.getElementById("search-input");
    if (searchInput) searchInput.value = search;
  }
}


// ==============================================================================
// 10. Initialization
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
  parseUrlParams();
  initHeroSlider();
  loadCategories();
  loadFeaturedProducts();
  loadProducts();
  loadApprovedShops();
  updateWishlistUI();

  // Search form handler
  const searchForm = document.getElementById("search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", handleSearch);
  }

  // City dropdown handler
  const citySelect = document.getElementById("city-select");
  if (citySelect) {
    citySelect.addEventListener("change", handleSearch);
  }

  // Close dropdowns on outside click
  document.addEventListener("click", (e) => {
    const dropdown = document.getElementById("gbm-category-dropdown");
    const allCatsBtn = document.querySelector(".gbm-all-cats-btn");
    if (dropdown && dropdown.classList.contains("open")) {
      if (!dropdown.contains(e.target) && !allCatsBtn.contains(e.target)) {
        dropdown.classList.remove("open");
      }
    }
  });
});

