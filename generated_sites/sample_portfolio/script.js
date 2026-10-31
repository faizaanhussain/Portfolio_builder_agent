/**
 * Portfolio Interactive Scripts
 * Handles theme toggling, project filtering, smooth scrolling, and form submission.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle with LocalStorage Persistence
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = themeToggleBtn.querySelector('.theme-icon');
    const storedTheme = localStorage.getItem('faizan-portfolio-theme') || 'dark';

    function applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
        localStorage.setItem('faizan-portfolio-theme', theme);
    }

    applyTheme(storedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });

    // 2. Mobile Navigation Toggle
    const mobileToggle = document.getElementById('mobile-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
            const isOpen = navMenu.classList.contains('open');
            mobileToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        // Close mobile menu when clicking a link
        document.querySelectorAll('.nav-link, .nav-cta').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('open');
            });
        });
    }

    // 3. Smooth Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#' || href === '') return;

            const targetElement = document.querySelector(href);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 4. Interactive Project Filter
    const filterButtons = document.querySelectorAll('.filter-btn');
    const projectCards = document.querySelectorAll('.project-card');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const filterValue = button.getAttribute('data-filter');

            projectCards.forEach(card => {
                const cardCategory = card.getAttribute('data-category');
                if (filterValue === 'all' || cardCategory === filterValue) {
                    card.style.display = 'flex';
                    card.style.animation = 'fadeIn 0.4s ease forwards';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // 5. Contact Form Validation and Simulation
    const contactForm = document.getElementById('contact-form');
    const formFeedback = document.getElementById('form-feedback');

    if (contactForm && formFeedback) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const message = document.getElementById('message').value.trim();

            if (!name || !email || !message) {
                formFeedback.textContent = 'Please fill out all required fields.';
                formFeedback.style.color = '#ef4444';
                return;
            }

            // Simulate form submission
            formFeedback.textContent = 'Sending message...';
            formFeedback.style.color = 'var(--accent-primary)';

            setTimeout(() => {
                formFeedback.textContent = `🚀 Thank you, ${name}! Your message has been sent successfully. I will get back to you within 24 hours.`;
                formFeedback.style.color = '#10b981';
                contactForm.reset();

                setTimeout(() => {
                    formFeedback.textContent = '';
                }, 6000);
            }, 800);
        });
    }

    // 6. Header Background on Scroll
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.borderBottomColor = 'var(--border-bright)';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.borderBottomColor = 'var(--border-subtle)';
            navbar.style.boxShadow = 'none';
        }
    });
});
