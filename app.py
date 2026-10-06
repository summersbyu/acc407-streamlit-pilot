"""First ACC 407 public prototype: fictional vendor payments, no API keys."""
import csv
import io
import sqlite3
from datetime import date

import streamlit as st

APP_TITLE = "Accounting Payment Review Dashboard"


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
    st.title(APP_TITLE)
    st.write("Explore fictional company payments and identify items for review.")
    st.caption("ACC 407 learning prototype • Fictional data • No transactions are posted")
    with database() as con:
        vendors = dict(con.execute("SELECT vendor_id, name FROM vendors ORDER BY name"))
        st.subheader("Choose the report")
        vendor = st.selectbox("Vendor", [None, *vendors],
                              format_func=lambda value: "All vendors" if value is None else vendors[value])
        threshold = st.number_input("Show payments strictly greater than this amount ($)",
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
