"""Localized prompt templates for different services."""

PROMPT_TEMPLATES = {
    "en": {
        "text_generation": {
            "creative": "Write a creative piece about: {topic}",
            "professional": "Write a professional {format} about: {topic}",
            "casual": "Tell me about: {topic} in a fun way",
            "technical": "Explain the technical details of: {topic}",
        },
        "image_generation": {
            "photo": "A realistic photograph of {subject}, high quality, detailed",
            "artistic": "An artistic illustration of {subject}, creative style",
            "logo": "A professional logo design for {brand}, clean and modern",
            "banner": "A wide banner image about {topic}, eye-catching",
        },
    },
    "bn": {
        "text_generation": {
            "creative": "{topic} নিয়ে একটি সৃজনশীল লেখা লিখুন",
            "professional": "{topic} নিয়ে একটি পেশাদার {format} লিখুন",
            "casual": "{topic} সম্পর্কে মজার ভাবে বলুন",
            "technical": "{topic} -এর প্রযুক্তিগত বিবরণ ব্যাখ্যা করুন",
        },
        "image_generation": {
            "photo": "{subject} -এর একটি বাস্তবসম্মত ছবি, উচ্চ মানের",
            "artistic": "{subject} -এর একটি শৈল্পিক চিত্র, সৃজনশীল শৈলী",
            "logo": "{brand} -এর জন্য একটি পেশাদার লোগো ডিজাইন",
            "banner": "{topic} সম্পর্কে একটি চোখ-ধাঁধানো ব্যানার ছবি",
        },
    },
    "hi": {
        "text_generation": {
            "creative": "{topic} के बारे में एक रचनात्मक टुकड़ा लिखें",
            "professional": "{topic} के बारे में एक पेशेवर {format} लिखें",
            "casual": "{topic} के बारे में मजेदार तरीके से बताएं",
            "technical": "{topic} की तकनीकी जानकारी समझाएं",
        },
        "image_generation": {
            "photo": "{subject} की एक यथार्थवादी तस्वीर, उच्च गुणवत्ता",
            "artistic": "{subject} की एक कलात्मक चित्रण, रचनात्मक शैली",
            "logo": "{brand} के लिए एक पेशेवर लोगो डिज़ाइन",
            "banner": "{topic} के बारे में एक आकर्षक बैनर छवि",
        },
    },
}


class PromptTemplate:
    """Manage localized prompt templates."""

    def __init__(self):
        self.templates = PROMPT_TEMPLATES

    def get(self, language: str, category: str, template_type: str,
             **kwargs) -> str:
        """Get and format a prompt template."""
        lang_templates = self.templates.get(language, self.templates["en"])
        category_templates = lang_templates.get(category, {})
        template = category_templates.get(template_type, "")

        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        return template

    def list_templates(self, language: str = "en") -> dict:
        """List available templates for a language."""
        return self.templates.get(language, self.templates["en"])


# Global template instance
prompt_templates = PromptTemplate()
