
import { renderBuyerView } from './views/buyerView.js';
import { renderSellerView } from './views/sellerView.js';
import { renderImpactView } from './views/impactView.js';

export function initRouter() {
    const mainContainer = document.getElementById('main-content');

    const routes = {
        '#marketplace': renderBuyerView,
        '#seller': renderSellerView,
        '#impact': renderImpactView
    };

    function navigate() {
        const hash = window.location.hash || '#marketplace';
        mainContainer.innerHTML = '';
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === hash);
        });

        const viewRenderer = routes[hash] || renderBuyerView;
        viewRenderer(mainContainer);
    }

    window.addEventListener('hashchange', navigate);
    window.addEventListener('DOMContentLoaded', navigate);
}

window.switchView = function(viewName) {
    window.location.hash = `#${viewName}`;
};
