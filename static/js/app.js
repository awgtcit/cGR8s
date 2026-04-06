/**
 * cGR8s – Main Application JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    const backdrop = document.getElementById('sidebarBackdrop');
    const isMobile = () => window.innerWidth < 576;

    // Restore sidebar state from localStorage (desktop only)
    if (!isMobile() && sidebar) {
        const saved = localStorage.getItem('cgr8s-sidebar-collapsed');
        if (saved === 'true') {
            sidebar.classList.add('collapsed');
        }
    }

    // Sidebar toggle
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            if (isMobile()) {
                sidebar.classList.toggle('show');
            } else {
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('cgr8s-sidebar-collapsed', sidebar.classList.contains('collapsed'));
            }
        });
    }

    // Close sidebar on backdrop click (mobile)
    if (backdrop && sidebar) {
        backdrop.addEventListener('click', () => {
            sidebar.classList.remove('show');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }, 300);
        }, 5000);
    });

    // Scroll-to-top button
    const scrollBtn = document.getElementById('scrollTopBtn');
    if (scrollBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollBtn.classList.add('visible');
            } else {
                scrollBtn.classList.remove('visible');
            }
        });
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Confirm delete actions
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', (e) => {
            if (!confirm(el.dataset.confirm || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });
});

// HTMX event listeners
document.body.addEventListener('htmx:beforeRequest', (e) => {
    const target = e.detail.target;
    if (target) {
        target.classList.add('htmx-loading');
    }
    const bar = document.getElementById('pageLoadingBar');
    if (bar) bar.style.display = 'block';
});

document.body.addEventListener('htmx:afterRequest', (e) => {
    const target = e.detail.target;
    if (target) {
        target.classList.remove('htmx-loading');
    }
    const bar = document.getElementById('pageLoadingBar');
    if (bar) bar.style.display = 'none';
});

// Number formatting helper
function formatNumber(val, decimals = 4) {
    if (val === null || val === undefined || val === '') return '';
    return parseFloat(val).toFixed(decimals);
}

// Status badge class helper
function getStatusBadgeClass(status) {
    const map = {
        'Draft': 'badge-draft',
        'Calculated': 'badge-calculated',
        'QA Pending': 'badge-qa-pending',
        'QA Updated': 'badge-qa-updated',
        'Completed': 'badge-completed',
        'Report Generated': 'badge-report-generated',
    };
    return map[status] || 'bg-secondary';
}
