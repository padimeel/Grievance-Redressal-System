// static/js/register.js
document.addEventListener('DOMContentLoaded', function () {
  const pw1 = document.querySelector('[name="password1"]');
  const pw2 = document.querySelector('[name="password2"]');
  if (!pw1 || !pw2) return;

  // create inline error node appended after confirm input (if not exists)
  let errNode = document.getElementById('pw-match-error');
  if (!errNode) {
    errNode = document.createElement('p');
    errNode.id = 'pw-match-error';
    errNode.className = 'text-red-600 text-sm mt-1 hidden';
    pw2.parentNode.appendChild(errNode);
  }

  function check() {
    if (pw1.value === '' && pw2.value === '') {
      errNode.classList.add('hidden'); errNode.textContent = ''; return true;
    }
    if (pw1.value !== pw2.value) {
      errNode.textContent = 'Passwords do not match.'; errNode.classList.remove('hidden'); return false;
    }
    errNode.classList.add('hidden'); errNode.textContent = ''; return true;
  }

  pw1.addEventListener('input', check);
  pw2.addEventListener('input', check);

  const form = pw1.closest('form');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (!check()) { e.preventDefault(); pw2.focus(); }
    });
  }
});








