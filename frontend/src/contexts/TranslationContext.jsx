import React, { createContext, useContext, useState, useEffect } from 'react';
import en from '../locales/en';
import ar from '../locales/ar';

const TranslationContext = createContext();

export const useTranslation = () => useContext(TranslationContext);

export const TranslationProvider = ({ children }) => {
  const [language, setLanguage] = useState(localStorage.getItem('erp_lang') || 'en');

  useEffect(() => {
    localStorage.setItem('erp_lang', language);
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
  }, [language]);

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === 'en' ? 'ar' : 'en'));
  };

  const t = (key, params) => {
    const dictionary = language === 'ar' ? ar : en;
    const keys = key.split('.');
    let value = dictionary;
    for (const k of keys) {
      if (value === undefined || value[k] === undefined) {
        return key; // return key itself if missing
      }
      value = value[k];
    }
    if (typeof value === 'string' && params) {
      return Object.entries(params).reduce(
        (str, [k, v]) => str.split(`{${k}}`).join(v),
        value
      );
    }
    return value;
  };

  return (
    <TranslationContext.Provider value={{ language, toggleLanguage, t }}>
      {children}
    </TranslationContext.Provider>
  );
};
