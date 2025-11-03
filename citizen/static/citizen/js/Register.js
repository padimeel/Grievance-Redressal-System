document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  form.addEventListener("submit", (e) => {
    const pass = form.password.value;
    const confirm = form.confirmPassword.value;
    if (pass !== confirm) {
      e.preventDefault();
      alert("Passwords do not match!");
    }
  });
});
