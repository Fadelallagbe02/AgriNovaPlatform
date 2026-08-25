const AGRINOVA_LANGUAGES = {
  fr: "Français",
  en: "English",
  es: "Español",
  pt: "Português",
  ar: "العربية",
  zh: "中文"
};

function getLanguage() {
  return localStorage.getItem("agrinova_language") || "fr";
}

function setLanguage(lang) {
  if (!AGRINOVA_LANGUAGES[lang]) return;
  localStorage.setItem("agrinova_language", lang);
  window.dispatchEvent(new Event("agrinova-language-changed"));
}
