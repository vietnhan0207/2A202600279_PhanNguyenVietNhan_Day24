# tests/test_pii.py
import pytest
import pandas as pd
from src.pii.anonymizer import MedVietAnonymizer


@pytest.fixture(scope="module")
def anonymizer():
    return MedVietAnonymizer()


@pytest.fixture(scope="module")
def sample_df():
    return pd.read_csv("data/raw/patients_raw.csv").head(50)


class TestPIIDetection:

    def test_cccd_detected(self, anonymizer):
        text = "Bệnh nhân Nguyen Van A, CCCD: 012345678901"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                               entities=["VN_CCCD"])
        assert len(results) >= 1

    def test_phone_detected(self, anonymizer):
        text = "Liên hệ: 0912345678"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                               entities=["VN_PHONE"])
        assert len(results) >= 1

    def test_email_detected(self, anonymizer):
        text = "Email: nguyenvana@gmail.com"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                               entities=["EMAIL_ADDRESS"])
        assert len(results) >= 1

    def test_detection_rate_above_95_percent(self, anonymizer, sample_df):
        """Pipeline phải đạt >95% detection rate."""
        pii_columns = ["ho_ten", "cccd", "so_dien_thoai", "email"]
        rate = anonymizer.calculate_detection_rate(sample_df, pii_columns)
        print(f"\nDetection rate: {rate:.2%}")
        assert rate >= 0.95, f"Detection rate {rate:.2%} < 95%"


class TestAnonymization:

    def test_pii_not_in_output(self, anonymizer, sample_df):
        """Sau anonymization, không còn CCCD gốc trong output."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        anon_cccd_values = df_anon["cccd"].astype(str).tolist()
        for original_cccd in sample_df["cccd"].astype(str):
            assert original_cccd not in anon_cccd_values

    def test_non_pii_columns_unchanged(self, anonymizer, sample_df):
        """Cột benh và ket_qua_xet_nghiem phải giữ nguyên."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        assert list(df_anon["benh"]) == list(sample_df["benh"])
        assert list(df_anon["ket_qua_xet_nghiem"]) == list(sample_df["ket_qua_xet_nghiem"])

    def test_patient_id_unchanged(self, anonymizer, sample_df):
        """patient_id phải giữ nguyên (pseudonym)."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        assert list(df_anon["patient_id"]) == list(sample_df["patient_id"])

    def test_anonymize_text_replace(self, anonymizer):
        text = "Bệnh nhân có email test@example.com"
        result = anonymizer.anonymize_text(text, strategy="replace")
        assert "test@example.com" not in result

    def test_anonymize_text_hash(self, anonymizer):
        text = "CCCD: 012345678901"
        result = anonymizer.anonymize_text(text, strategy="hash")
        assert "012345678901" not in result
