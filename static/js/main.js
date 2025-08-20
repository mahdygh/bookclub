// BookClub - Simple & Fast JavaScript

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('📚 BookClub loaded');
    initializeApp();
});

// Main initialization
function initializeApp() {
    setupBasicFeatures();
    setupTooltips();
}

// Setup basic features
function setupBasicFeatures() {
    // Mobile menu
    const navToggler = document.querySelector('.navbar-toggler');
    if (navToggler) {
        navToggler.addEventListener('click', toggleMobileMenu);
    }
    
    // Simple animations on scroll
    setupScrollAnimations();
    
    // Form loading states
    setupFormLoading();
}

// Mobile menu toggle
function toggleMobileMenu() {
    const navCollapse = document.querySelector('.navbar-collapse');
    if (navCollapse) {
        navCollapse.classList.toggle('show');
    }
}

// Simple scroll animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe cards
    document.querySelectorAll('.card, .stats-card, .stage-card').forEach(el => {
        observer.observe(el);
    });
}

// Form loading states
function setupFormLoading() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>در حال پردازش...';
                submitBtn.disabled = true;
            }
        });
    });
}

// Setup Bootstrap tooltips
function setupTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Simple notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Help function
function showHelp() {
    showNotification('برای دریافت راهنما با مدیر تماس بگیرید', 'info');
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for global use
window.BookClub = {
    showNotification,
    showHelp
};