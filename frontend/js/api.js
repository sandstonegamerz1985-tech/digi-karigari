const API_ROOT = "https://digi-karigari.onrender.com";

async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Something went wrong. Please try again.");
  }
  return payload;
}

export function getProducts(buyerType = "retail") {
  return request(`/products?buyer_type=${encodeURIComponent(buyerType)}`);
}

export function uploadProduct(image, priceRupees) {
  const form = new FormData();
  form.append("image", image);
  return request(`/products?price_rupees=${encodeURIComponent(priceRupees)}`, {
    method: "POST",
    body: form,
  });
}

export function placeOrder(order) {
  return request("/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order),
  });
}

export function getImpact() {
  return request("/impact");
}
