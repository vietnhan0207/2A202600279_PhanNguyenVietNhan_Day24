# src/quality/validation.py
import pandas as pd


def build_patient_expectation_suite():
    """
    Tạo expectation suite cho patient data dùng Great Expectations.
    """
    import great_expectations as gx

    context = gx.get_context(mode="ephemeral")
    suite = gx.ExpectationSuite(name="patient_data_suite")

    # 1. patient_id không được null
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="patient_id"))

    # 2. cccd phải có đúng 12 ký tự
    suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToEqual(column="cccd", value=12))

    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(
        column="ket_qua_xet_nghiem", min_value=0, max_value=50
    ))

    # 4. benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(
        column="benh", value_set=valid_conditions
    ))

    # 5. email phải match regex pattern
    suite.add_expectation(gx.expectations.ExpectColumnValuesToMatchRegex(
        column="email", regex=r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
    ))

    # 6. Không được có duplicate patient_id
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="patient_id"))

    context.suites.add(suite)
    return suite


def validate_anonymized_data(filepath: str, original_filepath: str = "data/raw/patients_raw.csv") -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    original_df = pd.read_csv(original_filepath)

    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: cccd không còn là số thuần túy 12 chữ số giống bản gốc
    original_cccds = set(original_df["cccd"].astype(str))
    anon_cccds = set(df["cccd"].astype(str))
    leaked = original_cccds & anon_cccds
    if leaked:
        results["success"] = False
        results["failed_checks"].append(
            f"CCCD leak: {len(leaked)} original CCCDs still present in anonymized data"
        )

    # Check 2: Không có null trong các cột quan trọng
    critical_cols = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in critical_cols:
        if col in df.columns and df[col].isnull().any():
            results["success"] = False
            results["failed_checks"].append(f"Null values found in column: {col}")

    # Check 3: Số rows phải bằng original
    if len(df) != len(original_df):
        results["success"] = False
        results["failed_checks"].append(
            f"Row count mismatch: anonymized={len(df)}, original={len(original_df)}"
        )

    return results
