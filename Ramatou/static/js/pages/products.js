import { initCatalogPage } from "./catalogPageBase.js";

const catalogEl = document.getElementById("catalog");
const fixedFilter = catalogEl?.dataset.filter || "all";
const page = initCatalogPage({
  readOnly: false,
  fixedFilter,
  enableProductRating: true,
});
if (page) {
  page.loadProducts();
}
