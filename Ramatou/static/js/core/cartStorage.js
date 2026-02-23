const CART_KEY = "unknow_cart";

export function readCart() {
  return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
}

export function writeCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}
