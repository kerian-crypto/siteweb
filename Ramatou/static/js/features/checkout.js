import { api } from "../core/api.js";
import { formatMoney } from "../core/format.js";

export function bindCheckout({ formEl, resultEl, cartManager, reloadProducts }) {
  if (!formEl) return;

  formEl.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!cartManager.getItems().length) {
      resultEl.innerHTML = "<p class='warn'>Ajoutez des produits avant paiement.</p>";
      return;
    }

    const formData = new FormData(formEl);
    const payload = {
      phone: formData.get("phone"),
      payment_method: formData.get("payment_method"),
      items: cartManager.getItems(),
    };

    try {
      const order = await api("/api/checkout", { method: "POST", body: JSON.stringify(payload) });
      const downloads = order.downloads.length
        ? `<ul>${order.downloads.map((d) => `<li><a href="${d.url}">${d.product}</a></li>`).join("")}</ul>`
        : "<p>Aucun produit numérique.</p>";
      const coupon = order.coupon
        ? `<p>Coupon QR: <strong>${order.coupon.code}</strong><br><img src="${order.coupon.qr_path}" alt="QR coupon" width="140"></p>`
        : "<p>Pas de retrait kiosque requis.</p>";

      resultEl.innerHTML = `
        <h3>Commande #${order.id} validée</h3>
        <p>Statut: ${order.status}, livraison: ${order.delivery_date}</p>
        <p>Total payé: <strong>${formatMoney(order.total)}</strong></p>
        <h4>Téléchargements immédiats</h4>${downloads}
        <h4>Retrait kiosque</h4>${coupon}
      `;

      cartManager.clear();
      await reloadProducts();
    } catch (error) {
      resultEl.innerHTML = `<p class="warn">${error.message}</p>`;
    }
  });
}
