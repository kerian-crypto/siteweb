import { initCatalogPage } from "./catalogPageBase.js";

const page = initCatalogPage({ readOnly: true, fixedFilter: "all" });
if (page) {
  page.loadProducts();
}
