// login.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
      alert("Please fill all fields.");
      return;
    }

    try {
      const response = await fetch("/api/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: email, password: password })
      });

      const data = await response.json();

      if (response.ok) {
        // Store JWT tokens
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);
        alert("Login successful!");
        window.location.href = "/"; // redirect
      } else {
        alert(data.detail || "Invalid credentials");
      }
    } catch (err) {
      console.error(err);
      alert("Error logging in. Try again.");
    }
  });
});
