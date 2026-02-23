import { api } from "../core/api.js";
import { readCart, writeCart } from "../core/cartStorage.js";
import { setupCatalog } from "../features/catalog.js";
import { createCartManager } from "../features/cart.js";

export function initCatalogPage({
  readOnly = false,
  fixedFilter = "all",
  enableProductRating = false,
} = {}) {
  const catalogEl = document.getElementById("catalog");
  if (!catalogEl) return null;

  const cart = readCart();
  const filterButtons = Array.from(document.querySelectorAll("[data-filter]"));
  const initialFilter = fixedFilter || catalogEl.dataset.filter || "all";

  const catalog = setupCatalog({
    catalogEl,
    filterButtons,
    readOnly,
    initialFilter,
    enableProductRating,
    onAddToCart: (productId) => cartManager.add(productId),
    onRateProduct: async (ratingPayload) => {
      await api("/api/ratings", {
        method: "POST",
        body: JSON.stringify(ratingPayload),
      });
      await loadProducts();
    },
  });

  const cartManager = createCartManager({
    cart,
    getProducts: () => catalog.getProducts(),
    onCartUpdated: () => {
      writeCart(cart);
      cartManager.render(document.getElementById("cart-list"), document.getElementById("cart-total"));
    },
  });

  async function loadProducts() {
    const products = await api("/api/products");
    catalog.setProducts(products);
    cartManager.render(document.getElementById("cart-list"), document.getElementById("cart-total"));
    return products;
  }

  return { loadProducts, getProducts: () => catalog.getProducts(), cartManager };
}
