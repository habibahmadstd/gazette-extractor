import io
import re
import pandas as pd
import streamlit as st

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Gazette Result Extractor",
    page_icon="📋",
    layout="centered",
)

st.title("📋 Gazette Result Extractor")
st.markdown(
    "Upload your **gazette file** and your **roll numbers file**, "
    "set the columns-per-student, and download the extracted results instantly."
)
st.divider()

# ── Helpers ───────────────────────────────────────────────────

def split_row_into_students(row_values, cols_per_student):
    students = []
    for start in range(0, len(row_values), cols_per_student):
        chunk = list(row_values[start : start + cols_per_student])
        chunk += [""] * (cols_per_student - len(chunk))
        students.append(chunk)
    return students


def load_roll_numbers_from_bytes(file_bytes, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, header=None)
    else:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, header=None)

    roll_numbers = (
        df.iloc[:, 0]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .tolist()
    )
    # Drop text header if present
    if roll_numbers and not roll_numbers[0].isdigit():
        roll_numbers = roll_numbers[1:]
    return roll_numbers


def extract_from_spreadsheet_bytes(file_bytes, filename, roll_numbers, cols_per_student):
    ext = filename.rsplit(".", 1)[-1].lower()
    roll_set = set(str(r).strip() for r in roll_numbers)

    if ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, header=None)
    else:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, header=None)

    df = df.fillna("").astype(str).apply(lambda c: c.str.strip())

    # Auto-detect and skip header row
    header_row_idx = None
    for idx, row in df.iterrows():
        joined = " ".join(row.values).lower()
        if any(k in joined for k in ["roll", "name", "result", "marks", "declarat"]):
            header_row_idx = idx
            break

    data_df = df.iloc[header_row_idx + 1 :].reset_index(drop=True) if header_row_idx is not None else df

    matched_records = []
    for _, row in data_df.iterrows():
        for student in split_row_into_students(list(row.values), cols_per_student):
            if str(student[0]).strip() in roll_set:
                matched_records.append(student)

    if not matched_records:
        return pd.DataFrame(), roll_set

    cols = [f"Col_{i+1}" for i in range(cols_per_student)]
    result_df = pd.DataFrame(matched_records, columns=cols)
    return result_df, roll_set


def extract_from_pdf_bytes(file_bytes, roll_numbers, cols_per_student):
    import pdfplumber

    roll_set = set(str(r).strip() for r in roll_numbers)
    matched_records = []
    progress = st.progress(0, text="Reading gazette PDF…")

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            progress.progress((i + 1) / total, text=f"Processing page {i+1} of {total}…")

            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if not row:
                            continue
                        row = [str(c).strip() if c else "" for c in row]
                        for student in split_row_into_students(row, cols_per_student):
                            if str(student[0]).strip() in roll_set:
                                matched_records.append(student)
            else:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.split("\n"):
                    parts = [p.strip() for p in re.split(r"\s{2,}|\t", line.strip()) if p.strip()]
                    for student in split_row_into_students(parts, cols_per_student):
                        if str(student[0]).strip() in roll_set:
                            matched_records.append(student)

    progress.empty()

    if not matched_records:
        return pd.DataFrame(), roll_set

    cols = [f"Col_{i+1}" for i in range(cols_per_student)]
    result_df = pd.DataFrame(matched_records, columns=cols)
    return result_df, roll_set


def to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()


# ── Sidebar settings ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    cols_per_student = st.number_input(
        "Columns per student in gazette",
        min_value=2,
        max_value=20,
        value=5,
        help="How many columns make up one student's record in the gazette. "
             "E.g. Roll No, Name, blank, blank, Marks = 5",
    )
    st.markdown("---")
    st.markdown(
        "**Tip:** If extracted results look wrong, try changing "
        "this number (e.g. 6 or 7) to match your gazette layout."
    )

# ── File uploaders ────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    gazette_file = st.file_uploader(
        "📂 Upload Gazette File",
        type=["pdf", "xlsx", "xls", "csv"],
        help="The full gazette — PDF, Excel, or CSV",
    )

with col2:
    roll_file = st.file_uploader(
        "📝 Upload Roll Numbers File",
        type=["xlsx", "xls", "csv"],
        help="Excel or CSV with roll numbers in the first column",
    )

st.divider()

# ── Extract button ────────────────────────────────────────────
if st.button("🔍 Extract Results", type="primary", use_container_width=True):

    if not gazette_file:
        st.error("Please upload the gazette file.")
        st.stop()
    if not roll_file:
        st.error("Please upload the roll numbers file.")
        st.stop()

    # Load roll numbers
    roll_numbers = load_roll_numbers_from_bytes(roll_file.read(), roll_file.name)
    if not roll_numbers:
        st.error("No roll numbers found in the uploaded file. Check the first column.")
        st.stop()

    st.info(f"✅ Loaded **{len(roll_numbers)}** roll numbers.")

    # Extract from gazette
    gazette_bytes = gazette_file.read()
    ext = gazette_file.name.rsplit(".", 1)[-1].lower()

    with st.spinner("Searching gazette… please wait."):
        if ext == "pdf":
            result_df, roll_set = extract_from_pdf_bytes(gazette_bytes, roll_numbers, cols_per_student)
        else:
            result_df, roll_set = extract_from_spreadsheet_bytes(
                gazette_bytes, gazette_file.name, roll_numbers, cols_per_student
            )

    # ── Results ───────────────────────────────────────────────
    if result_df.empty:
        st.warning(
            "⚠️ No matching records found. "
            "Check that roll numbers are correct and 'Columns per student' matches your gazette."
        )
    else:
        st.success(f"✅ Found **{len(result_df)}** student record(s).")
        st.dataframe(result_df, use_container_width=True)

        # Download button
        excel_bytes = to_excel_bytes(result_df)
        st.download_button(
            label="⬇️ Download Results as Excel",
            data=excel_bytes,
            file_name="extracted_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        # Not-found report
        found_set = set(result_df["Col_1"].astype(str).str.strip().tolist())
        not_found = [r for r in roll_numbers if r not in found_set]
        if not_found:
            with st.expander(f"⚠️ {len(not_found)} roll number(s) NOT found in gazette"):
                st.write(not_found)

st.divider()
st.caption("Gazette Result Extractor • Works with PDF, Excel, and CSV gazette files")
