/**
 * Smart Campus Placement Management System
 * Interactive Client-side Script
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Toggle
  const navToggle = document.getElementById('navToggle');
  const navMenu = document.getElementById('navMenu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', !isExpanded);
      navMenu.classList.toggle('open');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
        navMenu.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // 2. Flash Alert Dismiss Buttons & Auto-Dismiss
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 300);
      }
    });
  });

  // Auto dismiss success alerts after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert-success');
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.transition = 'opacity 0.4s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 400);
      }
    }, 6000);
  });

  // 3. Password Visibility Toggles
  const passwordToggles = document.querySelectorAll('.password-toggle-btn');
  passwordToggles.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        btn.textContent = isPassword ? 'Hide' : 'Show';
        btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      }
    });
  });

  // 4. File Upload Drag & Drop and Preview
  const fileBoxes = document.querySelectorAll('.file-upload-box');
  fileBoxes.forEach((box) => {
    const input = box.querySelector('input[type="file"]');
    const label = box.querySelector('.file-upload-name') || box.querySelector('p');

    if (!input) return;

    box.addEventListener('click', (e) => {
      if (e.target !== input) {
        input.click();
      }
    });

    box.addEventListener('dragover', (e) => {
      e.preventDefault();
      box.classList.add('drag-over');
    });

    box.addEventListener('dragleave', () => {
      box.classList.remove('drag-over');
    });

    box.addEventListener('drop', (e) => {
      e.preventDefault();
      box.classList.remove('drag-over');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        input.files = e.dataTransfer.files;
        updateFileLabel(input, label);
      }
    });

    input.addEventListener('change', () => {
      updateFileLabel(input, label);
    });
  });

  function updateFileLabel(input, labelElem) {
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      const maxBytes = 5 * 1024 * 1024; // 5 MB

      if (file.size > maxBytes) {
        alert('File size exceeds the 5MB limit. Please choose a smaller PDF/DOC file.');
        input.value = '';
        if (labelElem) labelElem.textContent = 'Choose or drag your resume (PDF, DOC, DOCX up to 5MB)';
        return;
      }

      const sizeKb = (file.size / 1024).toFixed(1);
      if (labelElem) {
        labelElem.innerHTML = `<strong>Selected:</strong> ${escapeHtml(file.name)} (${sizeKb} KB)`;
      }
    }
  }

  // 5. Delete Confirmations
  const confirmForms = document.querySelectorAll('form[data-confirm]');
  confirmForms.forEach((form) => {
    form.addEventListener('submit', (e) => {
      const msg = form.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});

