document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('form');
  forms.forEach((form) => {
    form.addEventListener('submit', () => {
      const button = form.querySelector('button[type="submit"]');
      if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
      }
    });
  });

  const toggle = document.getElementById('themeToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('dark');
      const isDark = document.body.classList.contains('dark');
      toggle.textContent = isDark ? '☀️' : '🌙';
    });
  }
});
