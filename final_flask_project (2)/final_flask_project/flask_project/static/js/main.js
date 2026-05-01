/**
 * UniReg — main.js
 * Enhanced JS for modern UI interactions.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Auto-dismiss alerts after 5 seconds with smooth animation
  document.querySelectorAll('.alert').forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Alert close button functionality
  document.querySelectorAll('.alert-close').forEach((closeBtn) => {
    closeBtn.addEventListener('click', function(e) {
      e.preventDefault();
      const alert = this.parentElement;
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(() => alert.remove(), 300);
    });
  });

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Enhanced form interactions
  document.querySelectorAll('.form-control').forEach((input) => {
    // Add focus effects
    input.addEventListener('focus', function() {
      this.parentElement.classList.add('focused');
    });

    input.addEventListener('blur', function() {
      this.parentElement.classList.remove('focused');
    });

    // Auto-resize textareas
    if (input.tagName === 'TEXTAREA') {
      input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
      });
    }
  });

  // Button ripple effect
  document.querySelectorAll('.btn').forEach((button) => {
    button.addEventListener('click', function(e) {
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;

      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.classList.add('ripple-effect');

      this.appendChild(ripple);

      setTimeout(() => ripple.remove(), 600);
    });
  });

  // Table row hover effects
  document.querySelectorAll('.table tbody tr').forEach((row) => {
    row.addEventListener('mouseenter', function() {
      this.style.transform = 'scale(1.01)';
    });

    row.addEventListener('mouseleave', function() {
      this.style.transform = 'scale(1)';
    });
  });

  // Course card hover animations
  document.querySelectorAll('.course-card').forEach((card) => {
    card.addEventListener('mouseenter', function() {
      const icon = this.querySelector('.course-code');
      if (icon) {
        icon.style.transform = 'scale(1.05)';
        icon.style.transition = 'transform 0.3s ease';
      }
    });

    card.addEventListener('mouseleave', function() {
      const icon = this.querySelector('.course-code');
      if (icon) {
        icon.style.transform = 'scale(1)';
      }
    });
  });

  // Search input enhancement
  const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search" i]');
  searchInputs.forEach((input) => {
    input.addEventListener('input', function() {
      if (this.value.length > 0) {
        this.classList.add('has-content');
      } else {
        this.classList.remove('has-content');
      }
    });
  });

  // Loading states for forms
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', function() {
      const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading">⏳</span> Processing...';
      }
    });
  });

  // Progressive enhancement for navigation
  const navLinks = document.querySelectorAll('.nav-links a');
  navLinks.forEach((link) => {
    link.addEventListener('click', function() {
      // Remove active class from all links
      navLinks.forEach(l => l.classList.remove('active'));
      // Add active class to clicked link
      this.classList.add('active');
    });
  });

  // Keyboard navigation improvements
  document.addEventListener('keydown', function(e) {
    // Close alerts with Escape key
    if (e.key === 'Escape') {
      const alerts = document.querySelectorAll('.alert');
      alerts.forEach(alert => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        alert.style.transition = 'all 0.3s ease';
        setTimeout(() => alert.remove(), 300);
      });
    }
  });

  // Intersection Observer for fade-in animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, observerOptions);

  // Apply fade-in to cards and sections
  document.querySelectorAll('.course-card, .stat-card, .detail-card').forEach((el) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });

  // Theme toggle (if needed in future)
  // const themeToggle = document.createElement('button');
  // themeToggle.innerHTML = '🌓';
  // themeToggle.className = 'theme-toggle';
  // document.querySelector('.navbar').appendChild(themeToggle);
});
