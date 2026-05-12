# src/pii/anonymizer.py
import random
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

def _fake_cccd() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(12)])

def _fake_phone() -> str:
    return f"0{random.choice([3,5,7,8,9])}" + "".join([str(random.randint(0,9)) for _ in range(8)])

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.
        - "replace" : thay bằng fake data (dùng Faker)
        - "mask"    : che khuất ký tự bằng *
        - "hash"    : SHA-256 one-way hash
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "VN_PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": _fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": _fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "DEFAULT": OperatorConfig("mask", {
                    "masking_char": "*",
                    "chars_to_mask": 100,
                    "from_end": False
                })
            }
        elif strategy == "hash":
            operators = {
                "DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})
            }
        else:
            operators = {}

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame.
        - ho_ten, dia_chi, email: dùng anonymize_text()
        - cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - bac_si_phu_trach: replace bằng fake name
        - benh, ket_qua_xet_nghiem, patient_id, ngay_sinh, ngay_kham: GIỮ NGUYÊN
        """
        df_anon = df.copy()

        # Text columns — dùng anonymize_text để detect + replace
        df_anon["ho_ten"] = df_anon["ho_ten"].apply(
            lambda x: self.anonymize_text(str(x), strategy="replace")
        )
        df_anon["dia_chi"] = df_anon["dia_chi"].apply(
            lambda x: self.anonymize_text(str(x), strategy="replace")
        )
        df_anon["email"] = df_anon["email"].apply(
            lambda x: self.anonymize_text(str(x), strategy="replace")
        )

        # Structured PII — replace trực tiếp
        df_anon["cccd"] = [_fake_cccd() for _ in range(len(df_anon))]
        df_anon["so_dien_thoai"] = [_fake_phone() for _ in range(len(df_anon))]
        df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]

        # benh, ket_qua_xet_nghiem, patient_id, ngay_sinh, ngay_kham — GIỮ NGUYÊN

        return df_anon

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công trên pii_columns.
        Mục tiêu: > 95%
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
