// Frontend client script for Certificate Request Management System

// Generate standard UUIDv4 for idempotency
function generateUUID() {
  if (crypto && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Switch simulated account
async function switchAccount(userId) {
  try {
    const res = await fetch(`/api/auth/select/${userId}`, { method: 'POST' });
    if (res.ok) {
      window.location.reload();
    } else {
      const err = await res.json();
      alert(`Error switching account: ${err.detail || 'Unknown error'}`);
    }
  } catch (e) {
    alert(`Network error switching account: ${e.message}`);
  }
}

// Initialize Create Request Form handlers
document.addEventListener('DOMContentLoaded', () => {
  const reqForm = document.getElementById('createRequestForm');
  const serviceSelect = document.getElementById('resource_id');
  const baseValueInput = document.getElementById('base_value');
  const chargeDisplay = document.getElementById('chargeDisplay');
  const chargeExplanation = document.getElementById('chargeExplanation');
  const capacityDisplay = document.getElementById('capacityDisplay');
  const statusBadge = document.getElementById('statusBadge');
  const idempotencyInput = document.getElementById('idempotency_key');
  const submitBtn = document.getElementById('submitBtn');
  const errorAlert = document.getElementById('formErrorAlert');

  // If on Create Request screen
  if (reqForm && idempotencyInput) {
    if (!idempotencyInput.value) {
      idempotencyInput.value = 'REQ-KEY-' + generateUUID();
    }

    async function updatePreview() {
      const resourceId = serviceSelect ? serviceSelect.value : null;
      if (!resourceId) return;

      const opt = serviceSelect.options[serviceSelect.selectedIndex];
      const capacity = opt.getAttribute('data-capacity');
      const status = opt.getAttribute('data-status');
      const chargeApplicable = opt.getAttribute('data-charge') === 'true';

      if (capacityDisplay) capacityDisplay.textContent = `${capacity} units available`;
      if (statusBadge) {
        statusBadge.textContent = status;
        statusBadge.className = status === 'ACTIVE' ? 'badge bg-success' : 'badge bg-danger';
      }

      const baseVal = parseFloat(baseValueInput.value) || 0;
      try {
        const res = await fetch('/api/requests/preview-charge', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resource_id: resourceId, base_value: baseVal })
        });
        if (res.ok) {
          const data = await res.json();
          if (chargeDisplay) chargeDisplay.textContent = `₹${parseFloat(data.calculated_charge).toFixed(2)}`;
          if (chargeExplanation) chargeExplanation.textContent = data.explanation;
        }
      } catch (err) {
        console.error('Error fetching charge preview:', err);
      }
    }

    if (serviceSelect) serviceSelect.addEventListener('change', updatePreview);
    if (baseValueInput) baseValueInput.addEventListener('input', updatePreview);

    // Initial update
    updatePreview();

    // Handle form submit with client validation and idempotency guard
    reqForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (errorAlert) errorAlert.classList.add('d-none');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
      }

      const payload = {
        resource_id: serviceSelect.value,
        name: document.getElementById('name').value.trim(),
        phone: document.getElementById('phone').value.trim(),
        description: document.getElementById('description').value.trim(),
        reference: document.getElementById('reference').value.trim(),
        base_value: parseFloat(baseValueInput.value) || 0,
        idempotency_key: idempotencyInput.value
      };

      try {
        const res = await fetch('/api/requests/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const created = await res.json();
          window.location.href = `/requests/${created.id}?submitted=true`;
        } else {
          const err = await res.json();
          if (errorAlert) {
            errorAlert.textContent = err.detail || 'Validation error occurred.';
            errorAlert.classList.remove('d-none');
          }
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Request';
          }
        }
      } catch (err) {
        if (errorAlert) {
          errorAlert.textContent = `Network connection failure: ${err.message}`;
          errorAlert.classList.remove('d-none');
        }
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Submit Request';
        }
      }
    });
  }
});
