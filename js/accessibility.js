/**
 * SmartCare Queue AI - Accessibility & Multi-Language Engine
 * Supports English, Tamil, and Hindi UI Translations + WCAG AA Controls
 */

const TRANSLATIONS = {
  en: {
    dashboard: "Dashboard",
    join_queue: "Join Queue",
    appointments: "Appointments",
    departments: "Departments",
    hospital_map: "Hospital Map",
    qr_token: "QR Token",
    lab_tests: "Lab Tests",
    billing: "Billing & Payments",
    ai_assistant: "AI Assistant",
    best_time: "Best Time to Visit",
    notifications: "Notifications",
    waiting_history: "Waiting History",
    feedback: "Feedback",
    accessibility: "Accessibility",
    logout: "Logout",
    now_serving: "Now Serving",
    patients_ahead: "Patients Ahead",
    est_wait: "Estimated Wait",
    less_waiting: "Less Waiting. Better Care."
  },
  ta: {
    dashboard: "முகப்பு பலகை",
    join_queue: "வரிசையில் சேரவும்",
    appointments: "முன்பதிவுகள்",
    departments: "மருத்துவ துறைகள்",
    hospital_map: "மருத்துவமனை வரைபடம்",
    qr_token: "QR டோக்கன்",
    lab_tests: "ஆய்வக சோதனைகள்",
    billing: "கட்டணங்கள் & ரசீது",
    ai_assistant: "AI உதவியாளர்",
    best_time: "வருகைக்கான சிறந்த நேரம்",
    notifications: "அறிவிப்புகள்",
    waiting_history: "காத்திருப்பு வரலாறு",
    feedback: "கருத்து பதிவு",
    accessibility: "அணுகல்தன்மை",
    logout: "வெளியேறு",
    now_serving: "தற்போது அழைக்கப்படுவது",
    patients_ahead: "முன்னால் உள்ள நோயாளிகள்",
    est_wait: "மதிப்பிடப்பட்ட நேரம்",
    less_waiting: "குறைந்த காத்திருப்பு. சிறந்த பராமரிப்பு."
  },
  hi: {
    dashboard: "डैशबोर्ड",
    join_queue: "कतार में शामिल हों",
    appointments: "अपॉइंटमेंट",
    departments: "चिकित्सा विभाग",
    hospital_map: "अस्पताल का नक्शा",
    qr_token: "क्यूआर टोकन",
    lab_tests: "लैब टेस्ट",
    billing: "बिलिंग और भुगतान",
    ai_assistant: "एआई सहायक",
    best_time: "आने का सबसे अच्छा समय",
    notifications: "सूचनाएं",
    waiting_history: "प्रतीक्षा इतिहास",
    feedback: "प्रतिक्रिया",
    accessibility: "सुलभता नियंत्रण",
    logout: "लॉग आउट",
    now_serving: "वर्तमान टोकन",
    patients_ahead: "आगे प्रतीक्षा कर रहे मरीज",
    est_wait: "अनुमानित प्रतीक्षा समय",
    less_waiting: "कम प्रतीक्षा। बेहतर देखभाल।"
  }
};

const Accessibility = {
  init() {
    this.applySavedPreferences();
    this.setupLanguageSelector();
    this.setupAccessibilityListeners();
  },

  applySavedPreferences() {
    // 1. High contrast
    const contrast = localStorage.getItem('smartcare_contrast');
    if (contrast === 'high') {
      document.body.classList.add('high-contrast');
    }

    // 2. Font sizing
    const fontSize = localStorage.getItem('smartcare_fontsize') || 'normal';
    if (fontSize === 'lg') document.body.classList.add('font-lg');
    if (fontSize === 'xl') document.body.classList.add('font-xl');

    // 3. Language
    const lang = localStorage.getItem('smartcare_lang') || 'en';
    this.applyLanguage(lang);
  },

  setupLanguageSelector() {
    const selector = document.getElementById('global-lang-select');
    if (!selector) return;

    selector.value = localStorage.getItem('smartcare_lang') || 'en';
    selector.addEventListener('change', (e) => {
      const chosen = e.target.value;
      localStorage.setItem('smartcare_lang', chosen);
      this.applyLanguage(chosen);
      window.api.showToast(`Language switched to ${CONFIG.LANGUAGES[chosen] || chosen}`, 'info');
    });
  },

  applyLanguage(lang) {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });
  },

  setupAccessibilityListeners() {
    const contrastBtn = document.getElementById('toggle-contrast-btn');
    const fontPlusBtn = document.getElementById('font-plus-btn');
    const fontMinusBtn = document.getElementById('font-minus-btn');
    const speechBtn = document.getElementById('voice-announce-btn');

    if (contrastBtn) {
      contrastBtn.addEventListener('click', () => {
        const isHigh = document.body.classList.toggle('high-contrast');
        localStorage.setItem('smartcare_contrast', isHigh ? 'high' : 'normal');
        window.api.showToast(`High Contrast Mode ${isHigh ? 'Enabled' : 'Disabled'}`, 'info');
      });
    }

    if (fontPlusBtn) {
      fontPlusBtn.addEventListener('click', () => {
        if (document.body.classList.contains('font-lg')) {
          document.body.classList.remove('font-lg');
          document.body.classList.add('font-xl');
          localStorage.setItem('smartcare_fontsize', 'xl');
        } else {
          document.body.classList.add('font-lg');
          localStorage.setItem('smartcare_fontsize', 'lg');
        }
      });
    }

    if (fontMinusBtn) {
      fontMinusBtn.addEventListener('click', () => {
        document.body.classList.remove('font-lg', 'font-xl');
        localStorage.setItem('smartcare_fontsize', 'normal');
      });
    }

    if (speechBtn) {
      speechBtn.addEventListener('click', () => {
        this.speakQueueStatus();
      });
    }
  },

  speakQueueStatus() {
    if (!('speechSynthesis' in window)) {
      window.api.showToast('Speech synthesis not supported in this browser', 'warning');
      return;
    }

    const tokenEl = document.querySelector('.token-badge-code');
    const servingEl = document.querySelector('.banner-metric-value');

    const token = tokenEl ? tokenEl.textContent : 'none';
    const serving = servingEl ? servingEl.textContent : 'none';

    const text = `SmartCare Queue update. Your token is ${token}. Now serving token ${serving}.`;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
    window.api.showToast('Announcing current queue status via speech...', 'info');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Accessibility.init();
});

window.Accessibility = Accessibility;
