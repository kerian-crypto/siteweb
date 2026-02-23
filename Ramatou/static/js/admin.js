const stateEl = document.getElementById("admin-session-state");
const kpiCardsEl = document.getElementById("kpi-cards");
const lowStockEl = document.getElementById("low-stock-list");
const customersEl = document.getElementById("customers-table");
const ordersEl = document.getElementById("orders-list");
const couponResultEl = document.getElementById("coupon-result");
const threadsEl = document.getElementById("chat-threads");
const adminChatBoxEl = document.getElementById("admin-chat-box");
const adminChatFormEl = document.getElementById("admin-chat-form");

let activeThreadId = null;

function csrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

async function apiAdmin(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { ...(options.headers || {}) };
  const isFormData = options.body instanceof FormData;
  if (!isFormData) headers["Content-Type"] = headers["Content-Type"] || "application/json";
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) headers["X-CSRF-Token"] = csrfToken();

  const response = await fetch(url, { headers, ...options });
  if (!response.ok) {
    let errorMessage = "Erreur API admin";
    try {
      const body = await response.json();
      errorMessage = body.error || body.message || errorMessage;
    } catch (_e) {
      // ignore
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

function formatMoney(value) {
  return `${new Intl.NumberFormat("fr-FR").format(value)} FCFA`;
}

function renderKpis(kpis) {
  kpiCardsEl.innerHTML = `
    <article class="kpi-card"><strong>Chiffre d'affaires</strong><p>${formatMoney(kpis.revenue)}</p></article>
    <article class="kpi-card"><strong>Commandes</strong><p>${kpis.order_count}</p></article>
    <article class="kpi-card"><strong>Panier moyen</strong><p>${formatMoney(kpis.avg_basket)}</p></article>
    <article class="kpi-card"><strong>Top produit</strong><p>${kpis.top_products[0]?.name || "N/A"}</p></article>
  `;
  lowStockEl.innerHTML = kpis.low_stock.length
    ? kpis.low_stock.map((p) => `<p class="warn">${p.name}: stock ${p.stock} (min ${p.min_stock})</p>`).join("")
    : "<p class='muted'>Aucune alerte stock.</p>";
}

function statusClass(status) {
  const normalized = status.toLowerCase();
  if (normalized.includes("livr")) return "livree";
  if (normalized.includes("pret")) return "prete";
  return "preparation";
}

function renderOrders(orders) {
  if (!orders.length) {
    ordersEl.innerHTML = "<p class='muted'>Aucune commande.</p>";
    return;
  }
  ordersEl.innerHTML = orders
    .map(
      (order) => `
      <article class="order-card">
        <p><strong>#${order.id}</strong> ${order.user_name} - ${formatMoney(order.total)}</p>
        <p class="status ${statusClass(order.status)}">${order.status}</p>
        <p>Livraison: ${order.delivery_date || "N/A"} | Paiement: ${order.payment_method}</p>
        <p>Articles: ${order.items.map((i) => `${i.name} x${i.qty}`).join(", ")}</p>
        <form class="inline-form" onsubmit="updateOrder(event, ${order.id})">
          <select name="status">
            <option value="En preparation">En preparation</option>
            <option value="Prete">Prete</option>
            <option value="Livree">Livree</option>
          </select>
          <input type="date" name="delivery_date" value="${order.delivery_date || ""}">
          <button type="submit">Mettre à jour</button>
        </form>
      </article>
    `
    )
    .join("");
}

function renderCustomers(customers) {
  if (!customers.length) {
    customersEl.innerHTML = "<p class='muted'>Aucun client.</p>";
    return;
  }
  customersEl.innerHTML = `
    <table class="table">
      <thead><tr><th>Client</th><th>Email</th><th>Commandes</th><th>CA généré</th><th>Dernière commande</th></tr></thead>
      <tbody>
        ${customers
          .map(
            (c) =>
              `<tr><td>${c.user_name}</td><td>${c.email}</td><td>${c.nb_orders}</td><td>${formatMoney(
                c.revenue_generated
              )}</td><td>${c.last_order ? c.last_order.slice(0, 10) : "N/A"}</td></tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderAttachment(message) {
  if (!message.attachment_url) return "";
  if (message.attachment_kind === "image") {
    return `<p><img src="${message.attachment_url}" alt="${message.attachment_name || "image"}" class="chat-media-image"></p>`;
  }
  if (message.attachment_kind === "video") {
    return `<p><video controls class="chat-media-video" src="${message.attachment_url}"></video></p>`;
  }
  return `<p><a href="${message.attachment_url}" target="_blank" rel="noopener">${message.attachment_name || "Document"}</a></p>`;
}

function moderateButtons(message) {
  if (message.sender_role !== "user") return "";
  const next = message.moderation_status === "hidden" ? "visible" : "hidden";
  const label = next === "hidden" ? "Masquer" : "Rendre visible";
  return `<p><button type="button" data-moderate="${message.id}" data-status="${next}">${label}</button></p>`;
}

function renderAdminMessages(messages) {
  adminChatBoxEl.innerHTML = messages
    .map(
      (m) => `
      <div class="msg ${m.sender_role === "admin" ? "admin" : "client"}">
        <strong>${m.author}</strong> <small>(${m.moderation_status})</small><br>
        ${m.message ? `<span>${m.message}</span>` : ""}
        ${renderAttachment(m)}
        ${moderateButtons(m)}
      </div>
    `
    )
    .join("");
  adminChatBoxEl.scrollTop = adminChatBoxEl.scrollHeight;

  adminChatBoxEl.querySelectorAll("[data-moderate]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await apiAdmin(`/api/admin/chat/messages/${btn.dataset.moderate}/moderate`, {
        method: "PATCH",
        body: JSON.stringify({ moderation_status: btn.dataset.status }),
      });
      if (activeThreadId) await loadThreadMessages(activeThreadId);
    });
  });
}

function renderThreads(threads) {
  if (!threads.length) {
    threadsEl.innerHTML = "<p class='muted'>Aucune discussion.</p>";
    return;
  }
  threadsEl.innerHTML = threads
    .map(
      (t) => `
      <button type="button" class="thread-item ${activeThreadId === t.id ? "active" : ""}" data-thread-id="${t.id}">
        <strong>${t.user_name}</strong><br>
        <small>${t.user_email}</small><br>
        <small>${t.last_message_preview || "-"}</small>
        ${t.unread_count ? `<span class="thread-badge">${t.unread_count}</span>` : ""}
      </button>
    `
    )
    .join("");

  threadsEl.querySelectorAll("[data-thread-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeThreadId = Number(btn.dataset.threadId);
      loadThreadMessages(activeThreadId);
      loadThreads();
    });
  });
}

async function loadThreads() {
  const threads = await apiAdmin("/api/admin/chat/threads");
  renderThreads(threads);
}

async function loadThreadMessages(threadId) {
  const payload = await apiAdmin(`/api/admin/chat/threads/${threadId}/messages`);
  renderAdminMessages(payload.messages || []);
}

async function refreshDashboard() {
  try {
    const [kpis, orders, customers] = await Promise.all([
      apiAdmin("/api/admin/kpis"),
      apiAdmin("/api/admin/orders"),
      apiAdmin("/api/admin/customers"),
    ]);
    renderKpis(kpis);
    renderOrders(orders);
    renderCustomers(customers);
    await loadThreads();
    if (activeThreadId) await loadThreadMessages(activeThreadId);
    stateEl.textContent = "Session admin active.";
  } catch (error) {
    stateEl.textContent = error.message;
  }
}

document.getElementById("product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(event.target);
  const payload = {
    name: data.get("name"),
    description: data.get("description"),
    price: Number(data.get("price")),
    image_url: data.get("image_url"),
    category: data.get("category"),
    is_free: Boolean(data.get("is_free")),
    stock: Number(data.get("stock")),
    min_stock: Number(data.get("min_stock")),
  };
  await apiAdmin("/api/products", { method: "POST", body: JSON.stringify(payload) });
  event.target.reset();
  await refreshDashboard();
});

window.updateOrder = async function updateOrder(event, orderId) {
  event.preventDefault();
  const data = new FormData(event.target);
  await apiAdmin(`/api/admin/orders/${orderId}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: data.get("status"),
      delivery_date: data.get("delivery_date"),
    }),
  });
  await refreshDashboard();
};

document.getElementById("coupon-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(event.target);
  try {
    const result = await apiAdmin("/api/admin/validate-coupon", {
      method: "POST",
      body: JSON.stringify({ code: data.get("code") }),
    });
    couponResultEl.innerHTML = `<p>${result.message}</p><p>Horodatage: ${result.used_at}</p>`;
    event.target.reset();
    await refreshDashboard();
  } catch (error) {
    couponResultEl.innerHTML = `<p class="warn">${error.message}</p>`;
  }
});

adminChatFormEl?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeThreadId) {
    alert("Sélectionnez une discussion d'abord.");
    return;
  }
  const data = new FormData(adminChatFormEl);
  const text = String(data.get("message") || "").trim();
  const attachment = data.get("attachment");
  if (!text && !(attachment && attachment.name)) return;

  await apiAdmin(`/api/admin/chat/threads/${activeThreadId}/messages`, {
    method: "POST",
    body: data,
  });
  adminChatFormEl.reset();
  await loadThreadMessages(activeThreadId);
  await loadThreads();
});

refreshDashboard();
setInterval(refreshDashboard, 6000);
