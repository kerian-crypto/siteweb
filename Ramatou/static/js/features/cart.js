import { formatMoney } from "../core/format.js";

export function createCartManager({ getProducts, cart, onCartUpdated }) {
  function add(productId) {
    const existing = cart.find((i) => i.product_id === productId);
    if (existing) existing.qty += 1;
    else cart.push({ product_id: productId, qty: 1 });
    onCartUpdated();
  }

  function render(cartListEl, cartTotalEl) {
    if (!cartListEl || !cartTotalEl) return;
    const items = cart
      .map((item) => {
        const product = getProducts().find((p) => p.id === item.product_id);
        if (!product) return null;
        const unit = product.is_free ? 0 : product.price;
        return { ...item, product, amount: unit * item.qty };
      })
      .filter(Boolean);

    if (!items.length) {
      cartListEl.innerHTML = "<p class='muted'>Panier vide.</p>";
      cartTotalEl.textContent = "0 FCFA";
      return;
    }

    cartListEl.innerHTML = items
      .map(
        (item) => `
      <div class="cart-item">
        <span>${item.product.name} x${item.qty}</span>
        <span>${formatMoney(item.amount)}</span>
      </div>
      `
      )
      .join("");

    const total = items.reduce((sum, item) => sum + item.amount, 0);
    cartTotalEl.textContent = formatMoney(total);
  }

  function clear() {
    cart.splice(0, cart.length);
    onCartUpdated();
  }

  function getItems() {
    return cart;
  }

  return { add, render, clear, getItems };
}
