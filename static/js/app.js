// Mayda UX yordamchilari (masalan, auto-hide messages)
document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".message");
  setTimeout(() => flashes.forEach(m => m.remove()), 4000);
});
