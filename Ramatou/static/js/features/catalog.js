import { formatMoney } from "../core/format.js";

export function setupCatalog({
  catalogEl,
  filterButtons = [],
  readOnly = false,
  initialFilter = "all",
  onAddToCart = () => {},
  enableProductRating = false,
  onRateProduct = async () => {},
}) {
  let products = [];
  let activeFilter = initialFilter;

  function filteredProducts() {
    return products.filter((p) => activeFilter === "all" || p.category === activeFilter);
  }

  function render() {
    if (!catalogEl) return;
    catalogEl.innerHTML = filteredProducts()
      .map(
        (p) => `
      <article class="card">
        <img src="${p.image_url}" alt="${p.name}" loading="lazy">
        <div class="body">
          <span class="badge">${p.category === "digital" ? "Numérique" : "Physique"}</span>
          <h3>${p.name}</h3>
          <p>${p.description}</p>
          <p class="price">${p.is_free ? "Gratuit" : formatMoney(p.price)}</p>
          <p>⭐ ${p.avg_stars} (${p.rating_count} avis)</p>
          ${p.category === "physical" ? `<p>Stock: ${p.stock}</p>` : ""}
          ${
            !readOnly && enableProductRating
              ? `
            <form class="product-rating-form" data-rate-form="${p.id}">
              <select name="stars" required>
                <option value="5">★★★★★</option>
                <option value="4">★★★★☆</option>
                <option value="3">★★★☆☆</option>
                <option value="2">★★☆☆☆</option>
                <option value="1">★☆☆☆☆</option>
              </select>
              <input type="text" name="comment" placeholder="Votre avis sur ce produit" required>
              <button type="submit">Noter ce produit</button>
              <p class="muted rating-feedback" data-rate-feedback="${p.id}"></p>
            </form>
            `
              : ""
          }
          ${
            readOnly
              ? `<button type="button" disabled>Visualisation seule</button>`
              : `<button type="button" data-add-cart="${p.id}">Ajouter au panier</button>`
          }
        </div>
      </article>
      `
      )
      .join("");

    catalogEl.querySelectorAll("[data-add-cart]").forEach((btn) => {
      btn.addEventListener("click", () => onAddToCart(Number(btn.dataset.addCart)));
    });

    catalogEl.querySelectorAll("[data-rate-form]").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const productId = Number(form.dataset.rateForm);
        const data = new FormData(form);
        const stars = Number(data.get("stars"));
        const comment = String(data.get("comment") || "").trim();
        const feedback = form.querySelector(`[data-rate-feedback="${productId}"]`);

        if (!stars || !comment) return;
        try {
          await onRateProduct({ product_id: productId, stars, comment });
          if (feedback) {
            feedback.textContent = "Avis enregistré.";
            feedback.classList.remove("warn");
          }
          form.reset();
        } catch (error) {
          if (feedback) {
            feedback.textContent = error.message;
            feedback.classList.add("warn");
          }
        }
      });
    });
  }

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((b) => b.classList.remove("active"));
      button.classList.add("active");
      activeFilter = button.dataset.filter || "all";
      render();
    });
  });

  return {
    setProducts(nextProducts) {
      products = nextProducts;
      render();
    },
    getProducts() {
      return products;
    },
  };
}
