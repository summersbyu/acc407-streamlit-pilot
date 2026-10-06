"""First ACC 407 public prototype: fictional vendor payments, no API keys."""
import csv
import io
import re
import sqlite3
from datetime import date

import streamlit as st

APP_TITLE = "Accounting Payment Review Dashboard"
CSV_COLUMNS = ["payment_id", "vendor_id", "payment_date", "amount"]
CLEAN_SAMPLE_CSV = """payment_id,vendor_id,payment_date,amount
201,1,2027-03-01,1250.00
202,2,2027-03-06,10000.01
203,5,2027-03-07,250.50
"""
INVALID_SAMPLE_CSV = """payment_id,vendor_id,payment_date,amount
201,1,2027-03-01,1250.00
201,2,2027-03-06,100.00
203,99,2027-03-07,250.50
204,1,2027-02-30,10.00
205,1,2027-03-01,0
206,1,2027-03-01,-1.00
207,1,2027-03-01,1.001
208,,2027-03-01,10.00
"""


def validate_payment_csv(content, vendor_ids):
    """Return complete integer-cent payments or row-specific errors, never partial data."""
    errors, validated, seen = [], [], set()
    try:
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content.lstrip("\ufeff")
    except UnicodeDecodeError:
        return [], ["CSV row 1: file must use UTF-8 encoding."]
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    row_number = 1
    try:
        header = next(reader, [])
        if len(header) != len(set(header)) or any(column not in header for column in CSV_COLUMNS):
            return [], ["CSV row 1: header must contain each required column once: " + ", ".join(CSV_COLUMNS)]
        for fields in reader:
            row_number = reader.line_num
            before = len(errors)
            if len(fields) != len(header):
                errors.append(f"CSV row {row_number}: number of fields does not match the header.")
                continue
            row = dict(zip(header, (field.strip() for field in fields)))
            for column in CSV_COLUMNS:
                if not row[column]:
                    errors.append(f"CSV row {row_number}: {column} is missing.")
            ids = {}
            for column in ["payment_id", "vendor_id"]:
                value = row[column]
                if not value:
                    continue
                if not re.fullmatch(r"[0-9]{1,19}", value) or int(value) > 9223372036854775807:
                    errors.append(f"CSV row {row_number}: {column} must be an integer within the supported range.")
                    continue
                ids[column] = int(value)
            if "payment_id" in ids:
                if ids["payment_id"] in seen:
                    errors.append(f"CSV row {row_number}: duplicate payment_id {ids['payment_id']}.")
                seen.add(ids["payment_id"])
            if "vendor_id" in ids and ids["vendor_id"] not in vendor_ids:
                errors.append(f"CSV row {row_number}: unknown vendor_id {ids['vendor_id']}.")
            if row["payment_date"]:
                try:
                    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row["payment_date"]):
                        raise ValueError
                    date.fromisoformat(row["payment_date"])
                except ValueError:
                    errors.append(f"CSV row {row_number}: payment_date must be a valid date in YYYY-MM-DD format.")
            cents = 0
            if row["amount"]:
                if not re.fullmatch(r"[0-9]{1,17}(\.[0-9]{1,2})?", row["amount"]):
                    errors.append(f"CSV row {row_number}: amount must be positive with at most two decimal places (no commas or currency symbols).")
                else:
                    whole, _, fraction = row["amount"].partition(".")
                    cents = int(whole) * 100 + int(fraction.ljust(2, "0"))
                    if not 0 < cents <= 9223372036854775807:
                        errors.append(f"CSV row {row_number}: amount must be greater than zero and within the supported range.")
            if len(errors) == before:
                validated.append((ids["payment_id"], ids["vendor_id"], row["payment_date"], cents))
    except csv.Error as exc:
        errors.append(f"CSV row {reader.line_num or row_number}: malformed CSV ({exc}).")
    if not errors and not validated:
        errors.append("CSV row 2: file must contain at least one payment.")
    return ([], errors) if errors else (validated, [])


def replace_payments(con, validated):
    """Replace payments in this run's private, in-memory database."""
    con.execute("DELETE FROM payments")
    con.executemany("INSERT INTO payments VALUES (?, ?, ?, ?)", validated)


def database():
    """A fresh fictional dataset per run; no shared writes or persistent files."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript("""
        CREATE TABLE vendors (vendor_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE payments (
            payment_id INTEGER PRIMARY KEY,
            vendor_id INTEGER NOT NULL REFERENCES vendors(vendor_id),
            payment_date TEXT NOT NULL,
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0));
    """)
    con.executemany("INSERT INTO vendors VALUES (?, ?)", [
        (1, "Aspen Office Supply"), (2, "Canyon Equipment"), (3, "Summit Services"),
        (4, "Bluebird Logistics"), (5, "Harbor Tech Solutions")])
    con.executemany("INSERT INTO payments VALUES (?, ?, ?, ?)", [
        (101, 1, "2027-03-01", 125000), (102, 2, "2027-03-05", 1000000),
        (103, 3, "2027-03-06", 1500000), (104, 1, "2027-03-07", 250000),
        (105, 2, "2027-03-08", 2500000), (106, 3, "2027-03-09", 1000001),
        (107, 1, "2027-03-13", 1000000), (108, 2, "2027-03-14", 50000),
        (109, 4, "2027-03-15", 875000), (110, 4, "2027-03-18", 1800000),
        (111, 5, "2027-03-19", 930000), (112, 5, "2027-03-20", 2100000)])
    return con


def payments(con, vendor_id=None, threshold_cents=0, weekends_only=False):
    rows = con.execute("""
        SELECT p.payment_id, v.name AS vendor, p.payment_date, p.amount_cents
        FROM payments p JOIN vendors v ON p.vendor_id = v.vendor_id
        WHERE (? IS NULL OR p.vendor_id = ?) AND p.amount_cents > ?
        ORDER BY p.payment_date, p.payment_id
    """, (vendor_id, vendor_id, threshold_cents)).fetchall()
    return [dict(row) for row in rows if not weekends_only
            or date.fromisoformat(row["payment_date"]).weekday() >= 5]


def vendor_summary(rows):
    """Summarize only filtered payments, keeping totals in integer cents."""
    grouped = {}
    for row in rows:
        vendor = row["vendor"]
        summary = grouped.setdefault(vendor, {
            "vendor": vendor, "payment_count": 0, "amount_cents": 0})
        summary["payment_count"] += 1
        summary["amount_cents"] += row["amount_cents"]
    return [grouped[vendor] for vendor in sorted(grouped)]


def export(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["payment_id", "vendor", "payment_date", "amount"])
    writer.writeheader()
    for row in rows:
        cents = row["amount_cents"]
        writer.writerow({"payment_id": row["payment_id"], "vendor": row["vendor"],
                         "payment_date": row["payment_date"],
                         "amount": f"{cents // 100}.{cents % 100:02d}"})
    return output.getvalue()


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.markdown("""
        <style>
        .stMainBlockContainer { max-width: 1200px; padding-top: 2rem; }
        h1 { color: #143D70; letter-spacing: -0.035em; }
        h2, h3 { color: #20558C; }
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #FFFFFF, #E7F0FF);
            border: 1px solid #C8DBF5;
            border-top: 4px solid #3B82F6;
            border-radius: 16px;
            padding: 1.2rem 1.5rem;
            box-shadow: 0 4px 16px rgba(20, 61, 112, 0.06);
        }
        [data-testid="stMetricValue"] { color: #174B8A; }
        [data-testid="stDataFrame"] {
            border: 1px solid #C8DBF5;
            border-radius: 12px;
            overflow: hidden;
        }
        [data-testid="stDownloadButton"] button {
            background-color: #2563EB;
            color: white;
            border: 1px solid #2563EB;
            border-radius: 10px;
        }
        [data-testid="stDownloadButton"] button:hover {
            background-color: #1D4ED8;
            border-color: #1D4ED8;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    st.title(APP_TITLE)
    st.write("Explore fictional company payments and identify items for review.")
    st.caption("ACC 407 learning prototype • Fictional data • No transactions are posted")
    with database() as con:
        vendors = dict(con.execute("SELECT vendor_id, name FROM vendors ORDER BY name"))
        with st.expander("Upload payment CSV / download examples"):
            st.write("Required columns: payment_id, vendor_id, payment_date, amount. "
                     "Use YYYY-MM-DD dates and positive dollar amounts with at most two decimal places. "
                     "CSV row numbers include the header as row 1.")
            st.caption("Vendor IDs: " + " • ".join(f"{key}: {name}" for key, name in sorted(vendors.items())))
            clean_column, invalid_column = st.columns(2)
            clean_column.download_button("Download clean sample CSV", CLEAN_SAMPLE_CSV,
                                         file_name="clean-payments.csv", mime="text/csv")
            invalid_column.download_button("Download invalid sample CSV", INVALID_SAMPLE_CSV,
                                           file_name="invalid-payments.csv", mime="text/csv")
            uploaded = st.file_uploader("Upload payments", type=["csv"], key="payment_csv")
            if uploaded is not None:
                validated, errors = validate_payment_csv(uploaded.getvalue(), vendors)
                if errors:
                    st.error("Upload rejected. No uploaded payments were used; reports show fictional sample data.")
                    for error in errors:
                        st.error(error)
                else:
                    replace_payments(con, validated)
                    st.success(f"Accepted {len(validated)} payments. Reports use this upload. Remove the file to restore sample data.")
        st.caption("Data source: uploaded payments" if uploaded is not None and not errors
                   else "Data source: fictional sample payments")
        st.subheader("Choose the report")
        vendor_column, threshold_column = st.columns(2)
        vendor = vendor_column.selectbox("Vendor", [None, *vendors],
                              format_func=lambda value: "All vendors" if value is None else vendors[value])
        threshold = threshold_column.number_input("Show payments strictly greater than this amount ($)",
                                    min_value=0, max_value=1000000, value=0, step=1000)
        weekend = st.checkbox("Only payments made on Saturday or Sunday")
        rows = payments(con, vendor, threshold * 100, weekend)
    st.subheader("Report results")
    left, right = st.columns(2)
    left.metric("Payments shown", len(rows))
    right.metric("Total shown", f"${sum(row['amount_cents'] for row in rows) / 100:,.2f}")
    if rows:
        st.dataframe([{"Payment ID": r["payment_id"], "Vendor": r["vendor"],
                       "Date": r["payment_date"], "Amount ($)": r["amount_cents"] / 100}
                      for r in rows], hide_index=True)
    else:
        st.info("No payments match these filters. Try a lower threshold or another vendor.")
    st.download_button("Download this report as CSV", export(rows),
                       file_name="vendor-payment-report.csv", mime="text/csv")
    st.subheader("Vendor summary")
    summary = vendor_summary(rows)
    if summary:
        st.dataframe([{"Vendor": r["vendor"], "Payment count": r["payment_count"],
                       "Total amount ($)": r["amount_cents"] / 100}
                      for r in summary], hide_index=True)
    else:
        st.caption("No vendor payments to summarize for these filters.")
    st.subheader("What this report means")
    st.write("Weekend and high-value payments are review indicators, not proof of error or fraud. "
             "The threshold is exclusive: a payment equal to it is excluded. "
             "Totals describe only the rows currently shown.")


if __name__ == "__main__":
    main()
