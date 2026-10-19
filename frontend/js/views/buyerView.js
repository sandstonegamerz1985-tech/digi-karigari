
import { getProducts } from '../api.js';

export async function renderBuyerView(container) {
    container.innerHTML = `
        <div class="buyer-view">
            <h2>Artisan Marketplace</h2>
            <p class="subtitle">Directly supporting rural weavers and artisans with fair-trade pricing.</p>
            <div id="product-grid" class="product-grid">
                <p>Loading handcrafted catalog...</p>
            </div>
        </div>
    `;

    try {
        const products = await getProducts("retail");
        const grid = container.querySelector("#product-grid");
        
        if (!products || products.length === 0) {
            grid.innerHTML = "<p>No products available yet. Check back soon!</p>";
            return;
        }

        grid.innerHTML = products.map(p => `
            <div class="product-card">
                <img src="https://digi-karigari.onrender.com${p.image_url}" alt="${p.title}" onerror="this.src='https://via.placeholder.com/300?text=Handcrafted+Item'">
                <div class="product-info">
                    <h3>${p.title}</h3>
                    <p>${p.description.substring(0, 80)}...</p>
                    <div class="product-price">₹${p.price_rupees || (p.price_paise / 100)}</div>
                    <button class="primary-btn" onclick="handleBuyClick('${p.id}')">Buy Now</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        container.querySelector("#product-grid").innerHTML = `<p style="color:red;">Failed to load products: ${err.message}</p>`;
    }
}

window.handleBuyClick = (productId) => {
    const buyer = localStorage.getItem("buyer_user");
    const loc = localStorage.getItem("buyer_location");
    if (!loc) { alert("Please select your delivery location first."); openLocationModal(); return; }
    if (!buyer) { openBuyerAuthModal(); return; }
    alert(`Checkout initiated for product ID: ${productId}!`);
};
