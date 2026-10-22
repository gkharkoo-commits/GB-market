/**
 * GB MARKET — Authentication & Session Manager
 */

function updateNavAuthUI() {
  const user = getCurrentUser();
  const token = getAuthToken();

  // Top bar auth slot
  const topAuthSlot = document.getElementById("top-auth-slot");
  if (topAuthSlot) {
    if (user && token) {
      let roleBadge = "";
      if (user.role === "admin") {
        roleBadge = `<a href="/static/admin/index.html" style="color:#facc15; font-weight:700;"><i class="fa-solid fa-gauge"></i> Admin</a>`;
      } else if (user.role === "shopkeeper") {
        roleBadge = `<a href="/static/seller/index.html" style="color:#38bdf8; font-weight:700;"><i class="fa-solid fa-store"></i> Seller Hub</a>`;
      } else if (user.role === "rider") {
        roleBadge = `<a href="/static/rider/index.html" style="color:#4ade80; font-weight:700;"><i class="fa-solid fa-motorcycle"></i> Rider Hub</a>`;
      }

      topAuthSlot.innerHTML = `
        ${roleBadge}
        <a href="/static/account.html"><i class="fa-solid fa-user-circle"></i> ${user.full_name ? user.full_name.split(" ")[0] : "Account"}</a>
        <a href="javascript:void(0)" onclick="handleLogout()"><i class="fa-solid fa-arrow-right-from-bracket"></i> Logout</a>
      `;
    } else {
      topAuthSlot.innerHTML = `
        <a href="/static/login.html"><i class="fa-solid fa-user"></i> Login</a>
        <a href="/static/register.html"><i class="fa-solid fa-user-plus"></i> Register</a>
      `;
    }
  }

  // Header auth slot (fallback for admin/other pages)
  const navContainer = document.getElementById("nav-auth-slot");
  if (navContainer) {
    if (user && token) {
      let roleDashboardLink = "";
      if (user.role === "admin") {
        roleDashboardLink = `<a href="/static/admin/index.html" class="nav-btn-link" style="color:#fbbf24;"><i class="fa-solid fa-gauge"></i> Admin</a>`;
      } else if (user.role === "shopkeeper") {
        roleDashboardLink = `<a href="/static/seller/index.html" class="nav-btn-link" style="color:#38bdf8;"><i class="fa-solid fa-store"></i> Seller Hub</a>`;
      } else if (user.role === "rider") {
        roleDashboardLink = `<a href="/static/rider/index.html" class="nav-btn-link" style="color:#4ade80;"><i class="fa-solid fa-motorcycle"></i> Rider Hub</a>`;
      }

      navContainer.innerHTML = `
        ${roleDashboardLink}
        <a href="/static/account.html" class="nav-btn-link"><i class="fa-solid fa-user-circle"></i> ${(user.full_name || "Account").split(" ")[0]}</a>
        <a href="/static/my-orders.html" class="nav-btn-link"><i class="fa-solid fa-box"></i> Orders</a>
        <button onclick="handleLogout()" class="nav-btn-link" style="background:none;border:none;"><i class="fa-solid fa-arrow-right-from-bracket"></i></button>
      `;
    } else {
      navContainer.innerHTML = `
        <a href="/static/login.html" class="nav-btn-link"><i class="fa-solid fa-arrow-right-to-bracket"></i> Login</a>
        <a href="/static/register.html" class="btn btn-sm btn-success" style="color:white;">Sign Up</a>
      `;
    }
  }

  updateOrdersCountBadge();
}

async function updateOrdersCountBadge() {
  const badge = document.getElementById("orders-count-badge");
  if (!badge) return;
  const user = getCurrentUser();
  const token = getAuthToken();
  if (!user || !token) {
    badge.textContent = "0";
    return;
  }
  try {
    const orders = await apiFetch("/orders/my-orders");
    badge.textContent = Array.isArray(orders) ? orders.length : 0;
  } catch (e) {
    badge.textContent = "0";
  }
}

async function updateCartCountBadge() {
  const badge = document.getElementById("cart-count-badge");
  if (!badge) return;
  try {
    const cart = await apiFetch("/cart/");
    badge.textContent = cart.total_items || 0;
  } catch (e) {
    badge.textContent = 0;
  }
}

function handleLogout() {
  clearAuthToken();
  window.location.href = "/static/index.html";
}

function requireAuth(allowedRoles = []) {
  const user = getCurrentUser();
  const token = getAuthToken();

  const isAdminSection = allowedRoles.includes("admin") || window.location.pathname.includes("/admin/");

  if (!user || !token) {
    if (isAdminSection) {
      window.location.href = `/static/admin/login.html?redirect=${encodeURIComponent(window.location.pathname)}`;
    } else {
      window.location.href = `/static/login.html?redirect=${encodeURIComponent(window.location.pathname)}`;
    }
    return false;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    if (isAdminSection) {
      alert("Access restricted: Administrator privileges required.");
      window.location.href = "/static/admin/login.html";
    } else {
      alert("Access restricted: You do not have permissions for this section.");
      window.location.href = "/static/index.html";
    }
    return false;
  }

  return true;
}

document.addEventListener("DOMContentLoaded", () => {
  updateNavAuthUI();
  updateCartCountBadge();
});
