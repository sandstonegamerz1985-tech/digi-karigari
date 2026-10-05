import { getImpact, getProducts, placeOrder, uploadProduct } from "./api.js";

const productGrid = document.querySelector("#product-grid");
const emptyState = document.querySelector("#empty-state");
const uploadForm = document.querySelector("#upload-form");
const uploadButton = document.querySelector("#upload-submit");
const uploadStatus = document.querySelector("#upload-status");
const imageInput = document.querySelector("#product-image");
const imagePreview = document.querySelector("#image-preview");
const toast = document.querySelector("#toast");
let buyerType = "retail";
let toastTimer;

function money(paise) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderProducts(products) {
  productGrid.replaceChildren();
  emptyState.hidden = products.length !== 0;
  for (const product of products) {
    const card = element("article", "product-card");
    const imageWrap = element("div", "product-image-wrap");
    const image = element("img", "product-image");
    image.src = product.image_url;
    image.alt = product.title;
    image.loading = "lazy";
    imageWrap.append(image);
    if (product.is_marginalized) {
      imageWrap.append(element("span", "product-community", "Community maker"));
    }

    const details = element("div", "product-details");
    details.append(element("p", "product-category", product.category));
    details.append(element("h3", "product-title", product.title));
    details.append(element("p", "product-maker", `Made by ${product.artisan_name}`));
    details.append(element("p", "product-description", product.description));
    const buyRow = element("div", "product-buy-row");
    buyRow.append(element("strong", "product-price", money(product.price_paise)));
    const controls = element("div", "buy-controls");
    const quantity = element("input", "quantity-input");
    quantity.type = "number";
    quantity.min = buyerType === "wholesale" ? "5" : "1";
    quantity.max = String(product.stock);
    quantity.value = buyerType === "wholesale" ? "5" : "1";
    quantity.setAttribute("aria-label", `Quantity for ${product.title}`);
    const buy = element("button", "buy-button", buyerType === "wholesale" ? "Request 5+" : "Buy this");
    buy.type = "button";
    buy.dataset.productId = product.id;
    buy.dataset.title = product.title;
    buy.dataset.stock = String(product.stock);
    controls.append(quantity, buy);
    buyRow.append(controls);
    details.append(buyRow);
    card.append(imageWrap, details);
    productGrid.append(card);
  }
}

async function refreshProducts() {
  try {
    renderProducts(await getProducts(buyerType));
  } catch (error) {
    showToast(error.message);
  }
}

async function refreshImpact() {
  try {
    const impact = await getImpact();
    document.querySelector("#metric-earnings").textContent = money(impact.artisan_earnings_paise);
    document.querySelector("#metric-reach").textContent = String(impact.artisans_reached);
    document.querySelector("#metric-share").textContent = `${impact.marginalized_earnings_share_percent}%`;
    document.querySelector("#metric-orders").textContent = `${impact.orders_count} orders`;
  } catch (error) {
    showToast(error.message);
  }
}

document.querySelectorAll("[data-buyer]").forEach((button) => {
  button.addEventListener("click", () => {
    buyerType = button.dataset.buyer;
    document.querySelectorAll("[data-buyer]").forEach((option) => {
      const selected = option === button;
      option.classList.toggle("active", selected);
      option.setAttribute("aria-pressed", String(selected));
    });
    refreshProducts();
  });
});

imageInput.addEventListener("change", () => {
  const image = imageInput.files?.[0];
  if (!image) return;
  imagePreview.src = URL.createObjectURL(image);
  imagePreview.hidden = false;
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const image = imageInput.files?.[0];
  const price = Number(document.querySelector("#price-input").value);
  if (!image || !Number.isInteger(price) || price < 1) return;

  uploadButton.disabled = true;
  uploadStatus.textContent = "Preparing your photo and listing…";
  try {
    const product = await uploadProduct(image, price);
    uploadStatus.textContent = `Ready: ${product.title}`;
    uploadForm.reset();
    imagePreview.removeAttribute("src");
    imagePreview.hidden = true;
    await Promise.all([refreshProducts(), refreshImpact()]);
    document.querySelector("#market").scrollIntoView({ behavior: "smooth" });
    showToast("Your piece is now in the market.");
  } catch (error) {
    uploadStatus.textContent = error.message;
  } finally {
    uploadButton.disabled = false;
  }
});

productGrid.addEventListener("click", async (event) => {
  const button = event.target.closest(".buy-button");
  if (!button) return;
  const quantityInput = button.closest(".buy-controls").querySelector(".quantity-input");
  const quantity = Number(quantityInput.value);
  const stock = Number(button.dataset.stock);
  if (!Number.isInteger(quantity) || quantity < Number(quantityInput.min) || quantity > stock) {
    showToast(`Choose a quantity from ${quantityInput.min} to ${stock}.`);
    quantityInput.focus();
    return;
  }

  button.disabled = true;
  try {
    const order = await placeOrder({
      product_id: button.dataset.productId,
      quantity,
      buyer_name: "Marketplace buyer",
      buyer_type: buyerType,
    });
    showToast(`Order placed. Demo payment ${order.payment_reference}. No money was charged.`);
    await Promise.all([refreshProducts(), refreshImpact()]);
  } catch (error) {
    showToast(error.message);
    button.disabled = false;
  }
});

document.querySelector("#voice-button").addEventListener("click", () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    showToast("Voice input is not available in this browser. You can still use the buttons.");
    return;
  }
  const recognition = new Recognition();
  recognition.lang = "en-IN";
  recognition.onresult = (event) => {
    const command = event.results[0][0].transcript.toLowerCase();
    if (command.includes("impact") || command.includes("earn")) {
      document.querySelector("#impact").scrollIntoView({ behavior: "smooth" });
    } else if (command.includes("upload") || command.includes("share")) {
      document.querySelector("#share").scrollIntoView({ behavior: "smooth" });
    } else {
      document.querySelector("#market").scrollIntoView({ behavior: "smooth" });
    }
  };
  recognition.onerror = () => showToast("I could not hear that. Please try again.");
  recognition.start();
});

refreshProducts();
refreshImpact();