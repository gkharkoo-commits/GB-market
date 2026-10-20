/**
 * GB MARKET — Authentication & Session Manager
 */

function updateNavAuthUI() {
  const navContainer = document.getElementById("nav-auth-slot");
  if (!navContainer) return;

  const user = getCurrentUser();
  const token = getAuthToken();

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
      <a href="/static/account.html" class="nav-btn-link"><i class="fa-solid fa-user-circle"></i> ${user.full_name.split(" ")[0]}</a>
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

  if (!user || !token) {
    window.location.href = `/static/login.html?redirect=${encodeURIComponent(window.location.pathname)}`;
    return false;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    alert("Access restricted: You do not have permissions for this section.");
    window.location.href = "/static/index.html";
    return false;
  }

  return true;
}

document.addEventListener("DOMContentLoaded", () => {
  updateNavAuthUI();
  updateCartCountBadge();
});
