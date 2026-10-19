import { getProducts } from '../api.js';

let allProducts = [];

export async function renderBuyerView(container) {
    container.innerHTML = `
        <div class="buyer-view">
            <div class="marketplace-hero">
                <h2>Artisan Marketplace</h2>
                <p class="subtitle">Directly supporting rural weavers and artisans with fair-trade pricing.</p>
                
                <!-- SEARCH HEADER FOR BUYERS -->
                <div class="search-box-container">
                    <input type="text" id="marketplace-search-input" placeholder="Search handcrafted pottery, handlooms, brassware..." oninput="handleMarketplaceSearch(event)">
                </div>
            </div>

            <div id="product-grid" class="product-grid">
                <p>Loading handcrafted catalog...</p>
            </div>
        </div>
    `;

    try {
        allProducts = await getProducts("retail");
        renderProductGrid(allProducts);
    } catch (err) {
        container.querySelector("#product-grid").innerHTML = `<p style="color:red;">Failed to load products: ${err.message}</p>`;
    }
}

function renderProductGrid(products) {
    const grid = document.getElementById("product-grid");
    if (!grid) return;

    if (!products || products.length === 0) {
        grid.innerHTML = "<p>No handcrafted products found matching your search.</p>";
        return;
    }

    grid.innerHTML = products.map(p => `
        <div class="product-card">
            <img src="https://digi-karigari.onrender.com${p.image_url}" alt="${p.title}" onerror="this.src='https://via.placeholder.com/300?text=Handcrafted+Item'">
            <div class="product-info">
                <h3>${p.title}</h3>
                <p>${(p.description || '').substring(0, 90)}...</p>
                <div class="product-price">₹${p.price_rupees || (p.price_paise / 100)}</div>
                <button class="primary-btn" onclick="handleBuyClick('${p.id}')">Buy Now</button>
            </div>
        </div>
    `).join('');
}

window.handleMarketplaceSearch = (e) => {
    const query = e.target.value.toLowerCase().trim();
    if (!query) {
        renderProductGrid(allProducts);
        return;
    }
    const filtered = allProducts.filter(p => 
        (p.title && p.title.toLowerCase().includes(query)) ||
        (p.description && p.description.toLowerCase().includes(query)) ||
        (p.category && p.category.toLowerCase().includes(query)) ||
        (p.tags && p.tags.some(tag => tag.toLowerCase().includes(query)))
    );
    renderProductGrid(filtered);
};
