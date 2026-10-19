
import { getImpact } from '../api.js';

export async function renderImpactView(container) {
    container.innerHTML = `
        <div class="impact-view" style="max-width:800px; margin: 0 auto; text-align:center;">
            <h2>Social Impact & Transparency</h2>
            <p class="subtitle">Tracking fair-trade earnings and rural artisan empowerment in real-time.</p>
            <div id="impact-stats" style="display:grid; grid-template-columns:repeat(3,1fr); gap:1.5rem; margin-top:2rem;">
                <div class="auth-card"><h3>Loading...</h3><p>Total Earnings</p></div>
                <div class="auth-card"><h3>Loading...</h3><p>Orders Placed</p></div>
                <div class="auth-card"><h3>Loading...</h3><p>Artisans Reached</p></div>
            </div>
        </div>
    `;

    try {
        const data = await getImpact();
        const stats = container.querySelector("#impact-stats");
        stats.innerHTML = `
            <div class="auth-card"><h3 style="color:var(--primary);">₹${data.earnings_paise ? (data.earnings_paise / 100).toFixed(2) : '0.00'}</h3><p>Total Earnings</p></div>
            <div class="auth-card"><h3 style="color:var(--primary);">${data.orders_count || 0}</h3><p>Orders Placed</p></div>
            <div class="auth-card"><h3 style="color:var(--primary);">${data.artisans_reached || 1}</h3><p>Artisans Reached</p></div>
        `;
    } catch (err) {
        container.querySelector("#impact-stats").innerHTML = `<p style="color:red;">Failed to load impact metrics.</p>`;
    }
}
