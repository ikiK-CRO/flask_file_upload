import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslation from './locales/en.json';
import hrTranslation from './locales/hr.json';

// Function to get language from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslation },
      hr: { translation: hrTranslation }
    },
    lng: getCookie('lang') || 'hr',  // Get from cookie or default to Croatian
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;