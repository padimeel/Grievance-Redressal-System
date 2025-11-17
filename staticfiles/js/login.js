// login.js & register.js

document.addEventListener("DOMContentLoaded", function() {
  // Toggle password visibility
  const passwordFields = document.querySelectorAll("input[type='password']");
  
  passwordFields.forEach(field => {
    const toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.innerHTML = "👁";
    toggleBtn.className = "absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700";
    toggleBtn.style.background = "none";
    toggleBtn.style.border = "none";
    toggleBtn.style.cursor = "pointer";
    
    field.parentElement.style.position = "relative";
    field.parentElement.appendChild(toggleBtn);
    
    toggleBtn.addEventListener("click", () => {
      if(field.type === "password") {
        field.type = "text";
      } else {
        field.type = "password";
      }
    });
  });
});




