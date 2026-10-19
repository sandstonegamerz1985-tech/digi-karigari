
import { getProducts, placeOrder, trackOrder, getSupport } from '../api.js';

let allProducts = [];
let buyerType = "retail";
const escapeHtml = (value = "") => String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[ch]));

export async function renderBuyerView(container) {
    container.innerHTML = `
        <div class="buyer-view">
            <section class="marketplace-hero">
                <span class="badge">Made by India's artisans</span>
                <h2>Crafts with a story. Makers with a future.</h2>
                <p class="subtitle">Discover handcrafted products, learn about the artisan behind each piece, and support fairer direct-to-buyer trade.</p>
                <div class="search-box-container"><input type="search" id="marketplace-search-input" placeholder="Search pottery, handlooms, brassware..." aria-label="Search products"></div>
                <div class="marketplace-controls">
                    <label for="buyer-type-select">Shopping as</label>
                    <select id="buyer-type-select"><option value="retail">Retail buyer</option><option value="wholesale">Wholesale buyer</option></select>
                    <span class="trust-note">Product and artisan details are shown transparently.</span>
                </div>
            </section>
            <section class="catalog-section"><h3>Explore the catalogue</h3><div id="product-grid" class="product-grid"><p>Loading handcrafted catalog...</p></div></section>
            <section class="order-tools">
                <div class="auth-card"><h3>Track your order</h3><p class="subtitle">Enter the demo tracking ID shown after placing an order.</p>
                    <form id="tracking-form"><div class="input-group"><label for="tracking-reference">Tracking ID or order ID</label><input id="tracking-reference" required placeholder="e.g. DEMO-ABC123"></div><button class="primary-btn" type="submit">Find order</button></form><div id="tracking-result" aria-live="polite"></div>
                </div>
                <div class="auth-card"><h3>Need help?</h3><p>Questions about a product or order? View the customer-care information configured for this prototype.</p><button class="secondary-btn" id="support-button" type="button">View support information</button><div id="support-result" aria-live="polite"></div></div>
            </section>
        </div>
        <div id="product-detail-modal" class="modal-backdrop" style="display:none;" role="dialog" aria-modal="true"><div class="modal-card product-detail-card"><button class="close-btn" id="close-product-detail" aria-label="Close">&times;</button><div id="product-detail-content"></div></div></div>`;

    container.querySelector("#marketplace-search-input").addEventListener("input", filterProducts);
    container.querySelector("#buyer-type-select").addEventListener("change", async event => { buyerType = event.target.value; await loadProducts(container); });
    container.querySelector("#tracking-form").addEventListener("submit", handleTracking);
    container.querySelector("#support-button").addEventListener("click", showSupport);
    container.querySelector("#close-product-detail").addEventListener("click", closeProductDetails);
    container.querySelector("#product-detail-modal").addEventListener("click", e => { if (e.target.id === "product-detail-modal") closeProductDetails(); });
    await loadProducts(container);
}

async function loadProducts(container) {
    const grid = container.querySelector("#product-grid");
    grid.innerHTML = "<p>Loading products...</p>";
    try { allProducts = await getProducts(buyerType); filterProducts(); }
    catch (err) { grid.innerHTML = `<p class="error-message">Could not load products: ${escapeHtml(err.message)}. Check that the backend is running.</p>`; }
}
function filterProducts() {
    const grid = document.getElementById("product-grid");
    const input = document.getElementById("marketplace-search-input");
    if (!grid || !input) return;
    const query = input.value.toLowerCase().trim();
    const filtered = allProducts.filter(p => [p.title, p.description, p.category, ...(p.tags || [])].some(value => String(value || "").toLowerCase().includes(query)));
    if (!filtered.length) { grid.innerHTML = "<p>No products found. Try a different search or check back later.</p>"; return; }
    grid.innerHTML = filtered.map(p => `
        <article class="product-card">
            <img src="${escapeHtml(String(p.image_url || "").startsWith("http") ? p.image_url : `https://digi-karigari.onrender.com${p.image_url || ""}`)}" alt="${escapeHtml(p.title)}" onerror="this.style.display='none'">
            <div class="product-info"><span class="badge">${escapeHtml(p.category || "Handcrafted")}</span><h3>${escapeHtml(p.title)}</h3>
                <p>${escapeHtml((p.description || "").slice(0, 115))}${(p.description || "").length > 115 ? "…" : ""}</p>
                <p class="artisan-line">Made by ${escapeHtml(p.artisan_name || "Independent artisan")}</p>
                <div class="product-price">₹${Number(p.price_rupees ?? (p.price_paise / 100)).toLocaleString("en-IN")}</div>
                <p class="stock-note">${Number(p.stock ?? 0)} available</p>
                <div class="product-actions"><button class="secondary-btn" data-details="${escapeHtml(p.id)}">View details</button><button class="primary-btn" data-buy="${escapeHtml(p.id)}">Buy now</button></div>
            </div>
        </article>`).join("");
    grid.querySelectorAll("[data-details]").forEach(button => button.addEventListener("click", () => showProductDetails(button.dataset.details)));
    grid.querySelectorAll("[data-buy]").forEach(button => button.addEventListener("click", () => buyProduct(button.dataset.buy)));
}
function findProduct(id) { return allProducts.find(p => String(p.id) === String(id)); }
function showProductDetails(id) {
    const p = findProduct(id); if (!p) return;
    document.getElementById("product-detail-content").innerHTML = `
        <span class="badge">${escapeHtml(p.category || "Handcrafted")}</span><h2>${escapeHtml(p.title)}</h2><p>${escapeHtml(p.description || "Description not provided.")}</p>
        <div class="artisan-transparency"><h3>Artisan information</h3><p><strong>Maker:</strong> ${escapeHtml(p.artisan_name || "Independent artisan")}</p>
        <p><strong>Community:</strong> ${escapeHtml(p.community || "Not provided")}</p>
        <p><strong>Verification:</strong> ${p.is_verified ? "Verified artisan" : "Verification not confirmed in this demo"}</p>
        <p><strong>Product provenance:</strong> Blockchain certificate integration is not connected in this prototype.</p></div>
        <p class="product-price">₹${Number(p.price_rupees ?? (p.price_paise / 100)).toLocaleString("en-IN")}</p><button class="primary-btn" id="detail-buy-button">Buy now</button>`;
    document.getElementById("product-detail-modal").style.display = "flex";
    document.getElementById("detail-buy-button").addEventListener("click", () => { closeProductDetails(); buyProduct(id); });
}
function closeProductDetails() { const modal = document.getElementById("product-detail-modal"); if (modal) modal.style.display = "none"; }

async function buyProduct(id) {
    const p = findProduct(id); if (!p) return;
    const quantityInput = prompt(`Quantity to order (available: ${p.stock ?? "unknown"}):`, "1");
    if (quantityInput === null) return;
    const quantity = Number(quantityInput);
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) { alert("Enter a whole-number quantity between 1 and 1000."); return; }
    const buyerName = prompt("Your name for the order:", localStorage.getItem("buyer_user") || "Marketplace buyer");
    if (buyerName === null || !buyerName.trim()) return;
    try {
        const order = await placeOrder({ product_id: p.id, quantity, buyer_name: buyerName.trim(), buyer_type: buyerType });
        alert(`Demo order placed!\nOrder ID: ${order.id}\nTracking ID: ${order.tracking_reference}\nTotal: ₹${(order.total_paise / 100).toLocaleString("en-IN")}\n\nPayment is simulated in this prototype; no real money was charged.`);
        const trackingInput = document.getElementById("tracking-reference"); if (trackingInput) trackingInput.value = order.tracking_reference;
    } catch (err) { alert(`Could not place order: ${err.message}`); }
}
async function handleTracking(event) {
    event.preventDefault();
    const result = document.getElementById("tracking-result");
    result.innerHTML = "<p>Looking up order...</p>";
    try {
        const order = await trackOrder(document.getElementById("tracking-reference").value.trim());
        result.innerHTML = `<div class="tracking-card"><h4>${escapeHtml(order.product_title)}</h4><p><strong>Status:</strong> ${escapeHtml(order.status)}</p><p><strong>Tracking ID:</strong> ${escapeHtml(order.tracking_reference)}</p><p><strong>Quantity:</strong> ${Number(order.quantity)}</p><p><strong>Total:</strong> ₹${(Number(order.total_paise) / 100).toLocaleString("en-IN")}</p><p class="subtitle">${escapeHtml(order.tracking_note)}</p></div>`;
    } catch (err) { result.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`; }
}
async function showSupport() {
    const result = document.getElementById("support-result"); result.innerHTML = "<p>Loading support details...</p>";
    try { const support = await getSupport(); result.innerHTML = `<p>${escapeHtml(support.service)}</p><p class="subtitle">${escapeHtml(support.message)}</p>`; }
    catch (err) { result.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`; }
}
