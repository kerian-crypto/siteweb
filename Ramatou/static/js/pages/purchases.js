import { api } from "../core/api.js";
import { formatMoney } from "../core/format.js";

const purchasesEl = document.getElementById("purchases-list");

async function loadPurchases() {
  if (!purchasesEl) return;
  try {
    const orders = await api("/api/my-purchases");
    if (!orders.length) {
      purchasesEl.innerHTML = "<p class='muted'>Aucun achat pour le moment.</p>";
      return;
    }

    purchasesEl.innerHTML = orders
      .map((order) => {
        const items = order.items.map((i) => `<li>${i.name} x${i.qty}</li>`).join("");
        const downloads = order.downloads.length
          ? `<ul>${order.downloads.map((d) => `<li><a href="${d.url}">${d.product}</a></li>`).join("")}</ul>`
          : "<p class='muted'>Aucun téléchargement.</p>";
        const coupon = order.coupon
          ? `<p>Coupon: <strong>${order.coupon.code}</strong></p><img src="${order.coupon.qr_path}" alt="QR coupon" width="130">`
          : "<p class='muted'>Pas de coupon kiosque.</p>";
        return `
        <article class="order-card">
          <p><strong>Commande #${order.id}</strong> - ${order.created_at.slice(0, 10)}</p>
          <p>Statut: <span class="status">${order.status}</span> | Total: ${formatMoney(order.total)}</p>
          <h4>Produits</h4>
          <ul>${items}</ul>
          <h4>Fiches / contenus numériques</h4>
          ${downloads}
          <h4>Coupons retrait</h4>
          ${coupon}
        </article>
        `;
      })
      .join("");
  } catch (_error) {
    purchasesEl.innerHTML = "<p class='warn'>Impossible de charger vos achats.</p>";
  }
}

loadPurchases();
