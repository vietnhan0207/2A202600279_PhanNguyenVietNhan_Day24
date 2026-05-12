# src/pii/detector.py
import spacy
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider


def _try_load_nlp_engine(model_name: str, lang_code: str = "vi"):
    """Try to create an NLP engine for the given model. Returns engine or None."""
    try:
        spacy.load(model_name)
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": lang_code, "model_name": model_name}]
        })
        return provider.create_engine()
    except BaseException:
        return None


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    """

    # --- TASK 2.2.1 ---
    # CCCD VN: 12 chữ số.
    # Also match 11 digits: pandas drops leading zeros when reading CSV
    # (e.g. "012345678901" stored as int 12345678901 = 11 chars).
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[Pattern(name="cccd_pattern", regex=r"\b\d{11,12}\b", score=0.9)],
        context=["cccd", "căn cước", "chứng minh", "cmnd"],
        supported_language="vi"
    )

    # --- TASK 2.2.2 ---
    # Số điện thoại VN: 0[35789]xxxxxxxx (10 chữ số)
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern(name="vn_phone", regex=r"\b0?[35789]\d{8}\b", score=0.85)],
        context=["điện thoại", "sdt", "phone", "liên hệ"],
        supported_language="vi"
    )

    # Email recognizer for "vi" (built-in Presidio EMAIL only covers "en")
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[Pattern(
            name="email_vi",
            regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            score=0.85
        )],
        supported_language="vi"
    )

    # Vietnamese name recognizer.
    # Uses entity "VN_PERSON" (not "PERSON") to avoid conflict with the
    # NLP engine's built-in PERSON entity, which silences custom PERSON
    # PatternRecognizers when the NLP model returns no results.
    # Vietnamese names: 2-4 capitalized words, each starting with A-Z
    # (Đ-initial words like "Đinh" are matched from the 2nd word onward).
    # [^\s]+ handles all Vietnamese diacritics without needing explicit Unicode ranges.
    person_recognizer = PatternRecognizer(
        supported_entity="VN_PERSON",
        patterns=[Pattern(
            name="vn_person_name",
            regex=r"[A-Z\u00C0-\u1EF9][^\s]+(?:[ \t][A-Z\u00C0-\u1EF9][^\s]+){1,3}",
            score=0.75
        )],
        supported_language="vi"
    )

    # --- TASK 2.2.3 ---
    # NLP engine — try vi_core_news_lg first, fallback to installed English models
    nlp_engine = None
    for model in ["vi_core_news_lg", "en_core_web_sm", "en_core_web_md", "en_core_web_lg"]:
        nlp_engine = _try_load_nlp_engine(model)
        if nlp_engine:
            break

    if nlp_engine is None:
        raise RuntimeError(
            "No spaCy model found. Run:\n"
            "  python -m spacy download en_core_web_sm"
        )

    # --- TASK 2.2.4 ---
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["vi"]
    )
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)
    analyzer.registry.add_recognizer(person_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities: PERSON (via VN_PERSON), EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    return analyzer.analyze(
        text=text,
        language="vi",
        entities=["VN_PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
