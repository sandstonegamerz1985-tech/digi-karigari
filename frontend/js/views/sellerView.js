
import { uploadProduct, requestArtisanVerification } from '../api.js';

export function renderSellerView(container) {
    const savedUser = localStorage.getItem("artisan_user");

    container.innerHTML = `
        <div class="seller-portal-container">
            <section class="artisan-hero-card">
                <span class="badge">Digital Heritage Initiative</span>
                <h2>Empowering India's Master Artisans & Weavers</h2>
                <p>
                    <strong>Digi-Karigari (कार्यकरी)</strong> bridges the gap between grassroots rural craftsmanship and modern digital markets. 
                    Upload photos of your handlooms, pottery, or metalwork to instantly generate AI listings and connect with buyers globally.
                </p>
                <div class="impact-highlights">
                    <span>✨ Direct Fair-Trade Earnings</span>
                    <span>🤖 Instant AI Cataloging</span>
                </div>
            </section>

            <!-- AUTH SECTION -->
            <div id="auth-section" class="auth-card" style="display: ${savedUser ? 'none' : 'block'};">
                <h3>Artisan Portal Login</h3>
                <p class="subtitle">Access your dashboard to publish crafts</p>
                <div class="auth-tabs">
                    <button class="tab-btn active" onclick="switchSellerTab('mobile')">Mobile Number</button>
                    <button class="tab-btn" onclick="switchSellerTab('google')">Google Email</button>
                </div>
                <div id="seller-mobile-form" class="auth-form-panel">
                    <div class="input-group">
                        <label>Mobile Number (+91)</label>
                        <input type="tel" id="seller-mobile-input" placeholder="10-digit mobile number" maxlength="10">
                    </div>
                    <button class="primary-btn" onclick="handleSellerMobileLogin()">Continue</button>
                </div>
                <div id="seller-google-form" class="auth-form-panel" style="display: none;">
                    <button class="google-btn" onclick="handleSellerGoogleLogin()">
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"> Continue with Google
                    </button>
                </div>
            </div>

            <!-- DASHBOARD SECTION -->
            <div id="dashboard-section" class="dashboard-card" style="display: ${savedUser ? 'block' : 'none'};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h3>Welcome, Artisan Partner</h3>
                        <p id="artisan-identifier" style="color:var(--text-muted); font-size:0.9rem;">Account: ${savedUser || ''}</p>
                    </div>
                    <button class="secondary-btn" onclick="handleSellerLogout()">Logout</button>
                </div>
                <hr class="divider">
                <section class="verification-panel">
                    <h4>Artisan verification</h4>
                    <p>Request a review for the Digi-Karigari Trusted Partner badge. This prototype does not collect or verify government ID documents automatically.</p>
                    <button type="button" class="secondary-btn" id="request-verification-btn">Request verification review</button>
                    <p id="verification-status" aria-live="polite"></p>
                </section>
                <hr class="divider">
                <form id="ai-listing-form" onsubmit="handleProductUpload(event)">
                    <h4>Create New AI Craft Listing</h4>
                    <div class="input-group" style="margin-top:1rem;">
                        <label>Craft Photo</label>
                        <input type="file" id="craft-image" accept="image/*" required>
                    </div>
                    <div class="input-group">
                        <label>Price (in Rupees - ₹)</label>
                        <input type="number" id="craft-price" placeholder="e.g., 1499" min="1" required>
                    </div>
                    <button type="submit" class="primary-btn">Prepare my listing with AI</button>
                </form>
            </div>
        </div>
    `;
    const verificationButton = container.querySelector("#request-verification-btn");
    if (verificationButton) {
        verificationButton.addEventListener("click", async () => {
            const status = container.querySelector("#verification-status");
            verificationButton.disabled = true;
            status.textContent = "Submitting demo request...";
            try {
                const result = await requestArtisanVerification();
                status.textContent = result.message;
            } catch (error) {
                status.textContent = `Could not submit request: ${error.message}`;
            } finally {
                verificationButton.disabled = false;
            }
        });
    }
}

window.switchSellerTab = (type) => {
    const mForm = document.getElementById("seller-mobile-form");
    const gForm = document.getElementById("seller-google-form");
    document.querySelectorAll(".seller-portal-container .tab-btn").forEach(b => b.classList.toggle("active"));
    if (type === 'mobile') { mForm.style.display = 'block'; gForm.style.display = 'none'; }
    else { mForm.style.display = 'none'; gForm.style.display = 'block'; }
};

window.handleSellerMobileLogin = () => {
    const num = document.getElementById("seller-mobile-input").value.trim();
    if (num.length < 10) { alert("Enter valid 10-digit number."); return; }
    localStorage.setItem("artisan_user", `+91 ${num}`);
    renderSellerView(document.getElementById("main-content"));
};

window.handleSellerGoogleLogin = () => {
    localStorage.setItem("artisan_user", "artisan.partner@gmail.com");
    renderSellerView(document.getElementById("main-content"));
};

window.handleSellerLogout = () => {
    localStorage.removeItem("artisan_user");
    renderSellerView(document.getElementById("main-content"));
};

window.handleProductUpload = async (e) => {
    e.preventDefault();
    const file = document.getElementById("craft-image").files[0];
    const price = document.getElementById("craft-price").value;
    if (!file) return;

    const btn = e.target.querySelector("button[type=submit]");
    btn.textContent = "AI is analyzing & publishing...";
    btn.disabled = true;

    try {
        await uploadProduct(file, price);
        alert("Product published successfully with AI listing details!");
        window.location.hash = "#marketplace";
    } catch (err) {
        alert(`Failed to publish: ${err.message}`);
        btn.textContent = "Prepare my listing with AI";
        btn.disabled = false;
    }
};
