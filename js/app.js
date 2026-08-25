document.addEventListener("DOMContentLoaded", () => {
  const language = getLanguage();

  document.querySelectorAll("[data-language]").forEach(button => {
    button.addEventListener("click", () => {
      setLanguage(button.dataset.language);
      location.reload();
    });
  });

  document.querySelectorAll("[data-current-language]").forEach(el => {
    el.textContent = AGRINOVA_LANGUAGES[language] || "Français";
  });

  document.querySelectorAll("[data-year]").forEach(el => {
    el.textContent = new Date().getFullYear();
  });
});
