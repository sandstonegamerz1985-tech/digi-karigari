
import { initRouter } from './router.js';

document.addEventListener("DOMContentLoaded", () => {
    initRouter();
    initLocationState();
    initBuyerAuthState();
});

// Location Modal Controls
window.openLocationModal = () => document.getElementById("location-modal").style.display = "flex";
window.closeLocationModal = () => document.getElementById("location-modal").style.display = "none";
window.saveLocation = () => {
    const input = document.getElementById("location-input").value.trim();
    if (!input) { alert("Please enter your PIN code or city."); return; }
    localStorage.setItem("buyer_location", input);
    document.getElementById("user-location-text").textContent = input;
    closeLocationModal();
};

function initLocationState() {
    const saved = localStorage.getItem("buyer_location");
    if (saved) {
        document.getElementById("user-location-text").textContent = saved;
    } else {
        setTimeout(() => openLocationModal(), 1500);
    }
}

// Buyer Auth Modal Controls
window.openBuyerAuthModal = () => document.getElementById("buyer-auth-modal").style.display = "flex";
window.closeBuyerAuthModal = () => document.getElementById("buyer-auth-modal").style.display = "none";
window.switchBuyerAuthTab = (type) => {
    const mobileForm = document.getElementById("buyer-mobile-form");
    const googleForm = document.getElementById("buyer-google-form");
    document.querySelectorAll("#buyer-auth-modal .tab-btn").forEach(t => t.classList.toggle("active"));
    if (type === 'mobile') {
        mobileForm.style.display = "block";
        googleForm.style.display = "none";
    } else {
        mobileForm.style.display = "none";
        googleForm.style.display = "block";
    }
};

window.handleBuyerMobileLogin = () => {
    const num = document.getElementById("buyer-mobile-input").value.trim();
    if (num.length < 10) { alert("Enter valid 10-digit number."); return; }
    localStorage.setItem("buyer_user", `+91 ${num}`);
    initBuyerAuthState();
    closeBuyerAuthModal();
};

window.handleBuyerGoogleLogin = () => {
    localStorage.setItem("buyer_user", "buyer@gmail.com");
    initBuyerAuthState();
    closeBuyerAuthModal();
};

window.handleBuyerLogout = () => {
    localStorage.removeItem("buyer_user");
    location.reload();
};

function initBuyerAuthState() {
    const buyer = localStorage.getItem("buyer_user");
    if (buyer) {
        document.getElementById("buyer-logged-out").style.display = "none";
        document.getElementById("buyer-logged-in").style.display = "block";
        document.getElementById("buyer-name-display").textContent = `👋 ${buyer}`;
    }
}
