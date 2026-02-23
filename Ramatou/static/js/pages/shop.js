import { bindChat } from "../features/chat.js";
import { bindCheckout } from "../features/checkout.js";
import { initCatalogPage } from "./catalogPageBase.js";

const page = initCatalogPage({
  readOnly: false,
  fixedFilter: "all",
  enableProductRating: true,
});

if (page) {
  const checkoutFormEl = document.getElementById("checkout-form");
  const resultEl = document.getElementById("order-result");

  const refreshAll = async () => {
    await page.loadProducts();
  };

  bindCheckout({
    formEl: checkoutFormEl,
    resultEl,
    cartManager: page.cartManager,
    reloadProducts: refreshAll,
  });

  bindChat({
    chatBoxEl: document.getElementById("chat-box"),
    chatFormEl: document.getElementById("chat-form"),
  });

  refreshAll();
}
