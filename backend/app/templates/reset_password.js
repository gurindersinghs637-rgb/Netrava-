"use strict";
const fragment = new URLSearchParams(location.hash.slice(1));
let tokenHash = fragment.get("token_hash");
history.replaceState(null, "", location.pathname);
const form = document.getElementById("reset");
const button = document.getElementById("submit");
const message = document.getElementById("message");
if (!tokenHash) {
  message.textContent = "This reset link is invalid. Request a new link from Forgot Password in NETRAVA.";
  button.disabled = true;
}
form.addEventListener("submit", async event => {
  event.preventDefault();
  const password = document.getElementById("password");
  const confirmation = document.getElementById("confirmation");
  if (password.value !== confirmation.value) {
    message.textContent = "Passwords do not match."; return;
  }
  button.disabled = true;
  try {
    const response = await fetch(location.pathname, {method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({token_hash: tokenHash, password: password.value, confirm_password: confirmation.value})});
    const result = await response.json();
    message.textContent = response.ok ? result.message : (result.detail?.message || result.message || "Password reset failed. Request a new link.");
    if (response.ok) { tokenHash = null; form.hidden = true; }
  } catch (_) { message.textContent = "Unable to connect. Try logging in before requesting a new reset link."; }
  finally { password.value = ""; confirmation.value = ""; if (tokenHash) button.disabled = false; }
});
