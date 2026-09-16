"""Multi-language translation and localization."""

from typing import Dict, Optional
from enum import Enum


class Language(str, Enum):
    BENGALI = "bn"
    ENGLISH = "en"
    HINDI = "hi"


# Pre-built translations
TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to AI Orchestrator",
        "generating": "Generating your request...",
        "success": "Generation completed successfully!",
        "error": "An error occurred while generating",
        "rate_limit": "Rate limit exceeded. Please try again later.",
        "invalid_prompt": "Please provide a valid prompt",
        "service_unavailable": "Service temporarily unavailable",
        "generating_text": "Generating text...",
        "generating_image": "Generating image...",
        "generating_video": "Generating video...",
        "generating_3d": "Generating 3D model...",
        "processing": "Processing your request",
        "queued": "Your request is in queue",
        "cancelled": "Request cancelled",
        "timeout": "Request timed out",
        "insufficient_credits": "Insufficient credits",
        "uploading": "Uploading...",
        "downloading": "Downloading...",
        "welcome_message": "Welcome to AI Orchestrator! I can help you generate text, images, videos, and 3D models using the best AI services.",
        "help_text": "Available commands:\n- /text - Generate text\n- /image - Generate image\n- /video - Generate video\n- /3d - Generate 3D model\n- /status - Check service status\n- /help - Show this message",
        "feedback_prompt": "How would you rate this generation? (1-5)",
        "thank_you": "Thank you for your feedback!",
        "language_changed": "Language changed to English",
        "credits_remaining": "Credits remaining: {amount}",
        "generation_complete": "Generation complete! Time taken: {time}s",
        "error_message": "Error: {message}",
        "contact_support": "If this persists, please contact support",
    },
    "bn": {
        "welcome": "AI Orchestrator-এ স্বাগতম",
        "generating": "আপনার অনুরোধ তৈরি করা হচ্ছে...",
        "success": "জেনারেশন সফলভাবে সম্পন্ন হয়েছে!",
        "error": "জেনারেশনে একটি ত্রুটি ঘটেছে",
        "rate_limit": "রেট লিমিট অতিক্রান্ত। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
        "invalid_prompt": "অনুগ্রহ করে একটি বৈধ প্রম্পট প্রদান করুন",
        "service_unavailable": "সেবা অস্থায়ীভাবে অনুপলব্ধ",
        "generating_text": "টেক্সট তৈরি করা হচ্ছে...",
        "generating_image": "ছবি তৈরি করা হচ্ছে...",
        "generating_video": "ভিডিও তৈরি করা হচ্ছে...",
        "generating_3d": "৩D মডেল তৈরি করা হচ্ছে...",
        "processing": "আপনার অনুরোধ প্রক্রিয়াকরণ হচ্ছে",
        "queued": "আপনার অনুরোধ কিউতে আছে",
        "cancelled": "অনুরোধ বাতিল করা হয়েছে",
        "timeout": "অনুরোধের সময় শেষ",
        "insufficient_credits": "অপর্যাপ্ত ক্রেডিট",
        "uploading": "আপলোড হচ্ছে...",
        "downloading": "ডাউনলোড হচ্ছে...",
        "welcome_message": "AI Orchestrator-এ স্বাগতম! আমি আপনাকে সেরা AI সেবা ব্যবহার করে টেক্সট, ছবি, ভিডিও এবং ৩D মডেল তৈরি করতে সাহায্য করতে পারি।",
        "help_text": "উপলব্ধ কমান্ড:\n- /text - টেক্সট তৈরি করুন\n- /image - ছবি তৈরি করুন\n- /video - ভিডিও তৈরি করুন\n- /3d - ৩D মডেল তৈরি করুন\n- /status - সেবার স্ট্যাটাস দেখুন\n- /help - এই বার্তা দেখুন",
        "feedback_prompt": "আপনি এই জেনারেশনকে কিভাবে রেটিং দেবেন? (১-৫)",
        "thank_you": "আপনার মতামতের জন্য ধন্যবাদ!",
        "language_changed": "ভাষা বাংলায় পরিবর্তন করা হয়েছে",
        "credits_remaining": "বাকি ক্রেডিট: {amount}",
        "generation_complete": "জেনারেশন সম্পূর্ণ! সময় লাগেছে: {time} সেকেন্ড",
        "error_message": "ত্রুটি: {message}",
        "contact_support": "এটি চালিয়ে গেলে, অনুগ্রহ করে সাপোর্টে যোগাযোগ করুন",
    },
    "hi": {
        "welcome": "AI Orchestrator में आपका स्वागत है",
        "generating": "आपका अनुरोध बनाया जा रहा है...",
        "success": "जनरेशन सफलतापूर्वक पूर्ण!",
        "error": "जनरेशन में एक त्रुटि हुई",
        "rate_limit": "रेट लिमिट पार हो गई। कृपया बाद में पुनः प्रयास करें।",
        "invalid_prompt": "कृपया एक मान्य प्रॉम्प्ट प्रदान करें",
        "service_unavailable": "सेवा अस्थायी रूप से उपलब्ध नहीं है",
        "generating_text": "टेक्स्ट बनाया जा रहा है...",
        "generating_image": "छवि बनाई जा रही है...",
        "generating_video": "वीडियो बनाया जा रहा है...",
        "generating_3d": "3D मॉडल बनाया जा रहा है...",
        "processing": "आपका अनुरोध संसाधित हो रहा है",
        "queued": "आपका अनुरोध कतार में है",
        "cancelled": "अनुरोध रद्द किया गया",
        "timeout": "अनुरोध का समय समाप्त",
        "insufficient_credits": "अपर्याप्त क्रेडिट",
        "uploading": "अपलोड हो रहा है...",
        "downloading": "डाउनलोड हो रहा है...",
        "welcome_message": "AI Orchestrator में आपका स्वागत है! मैं आपको सर्वोत्तम AI सेवाओं का उपयोग करके टेक्स्ट, छवियां, वीडियो और 3D मॉडल बनाने में मदद कर सकता हूं।",
        "help_text": "उपलब्ध कमांड:\n- /text - टेक्स्ट बनाएं\n- /image - छवि बनाएं\n- /video - वीडियो बनाएं\n- /3d - 3D मॉडल बनाएं\n- /status - सेवा स्थिति देखें\n- /help - यह संदेश देखें",
        "feedback_prompt": "आप इस जनरेशन को कैसे रेट करेंगे? (1-5)",
        "thank_you": "आपकी प्रतिक्रिया के लिए धन्यवाद!",
        "language_changed": "भाषा हिंदी में बदली गई",
        "credits_remaining": "शेष क्रेडिट: {amount}",
        "generation_complete": "जनरेशन पूर्ण! समय लगा: {time} सेकंड",
        "error_message": "त्रुटि: {message}",
        "contact_support": "यदि यह जारी रहता है, तो कृपया सपोर्ट से संपर्क करें",
    },
}


class Translator:
    """Handle translations and localization."""

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.translations = TRANSLATIONS
        self._user_languages: Dict[str, str] = {}

    def t(self, key: str, language: str = None, **kwargs) -> str:
        """Translate a key to the specified language."""
        lang = language or self.default_language
        translations = self.translations.get(lang, self.translations[self.default_language])
        text = translations.get(key, key)

        # Support string formatting with {key} placeholders
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def set_user_language(self, user_id: str, language: str):
        """Set preferred language for a user."""
        if language in [lang.value for lang in Language]:
            self._user_languages[user_id] = language

    def get_user_language(self, user_id: str) -> str:
        """Get user's preferred language."""
        return self._user_languages.get(user_id, self.default_language)

    def translate_text(self, text: str, from_lang: str, to_lang: str) -> str:
        """
        Translate arbitrary text between languages.
        NOTE: This is a stub. For production, integrate with:
        - Google Translate API
        - DeepL API
        - Microsoft Translator
        - Meta NLLB (open source)
        """
        # In production, call a real translation API here
        return f"[{to_lang}] {text}"

    def detect_language(self, text: str) -> str:
        """
        Detect language of text.
        NOTE: This is a stub. For production, use:
        - langdetect library
        - Google Cloud Translation
        - FastText language detection
        """
        # Simple heuristic for demo
        bengali_chars = sum(1 for c in text if 'ঀ' <= c <= '৿')
        devanagari_chars = sum(1 for c in text if 'ऀ' <= c <= 'ॿ')

        if bengali_chars > len(text) * 0.1:
            return Language.BENGALI.value
        elif devanagari_chars > len(text) * 0.1:
            return Language.HINDI.value
        return Language.ENGLISH.value

    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return [
            {"code": lang.value, "name": lang.name}
            for lang in Language
        ]


# Global translator instance
translator = Translator()
