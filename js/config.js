/**
 * SmartCare Queue AI - Global Configuration
 */
const CONFIG = {
  // Points to local Flask backend API
  API_BASE_URL: (window.location.origin && !window.location.origin.startsWith('file')) 
    ? `${window.location.origin}/api` 
    : 'http://localhost:5002/api',

  // Supabase Client Config (Fill with your project details)
  SUPABASE: {
    URL: 'https://your-project.supabase.co',
    ANON_KEY: 'your-anon-public-key'
  },

  // Supported Languages
  LANGUAGES: {
    en: "English",
    ta: "தமிழ் (Tamil)",
    hi: "हिन्दी (Hindi)"
  }
};

window.CONFIG = CONFIG;
