"""Known-answer accounting and Streamlit interaction checks."""
import io
from unittest.mock import patch

from app import (database, payments, export, vendor_summary, validate_payment_csv,
                 replace_payments, CLEAN_SAMPLE_CSV, INVALID_SAMPLE_CSV)
from streamlit.testing.v1 import AppTest

with database() as con:
    cases = [
        (None, 0, False, 12, 13130001),
        (2, 0, False, 3, 3550000),
        (None, 0, True, 5, 4900000),
        (None, 1000000, False, 5, 8900001),
        (None, 1000000, True, 2, 3600000),
        (None, 10000000, False, 0, 0),
    ]
    for vendor, threshold, weekend, count, total in cases:
        rows = payments(con, vendor, threshold, weekend)
        assert (len(rows), sum(row['amount_cents'] for row in rows)) == (count, total)
        assert len(export(rows).splitlines()) == count + 1
        summary = vendor_summary(rows)
        assert sum(row['amount_cents'] for row in summary) == total
        assert sum(row['payment_count'] for row in summary) == count
    assert vendor_summary(payments(con, 2)) == [
        {'vendor': 'Canyon Equipment', 'payment_count': 3, 'amount_cents': 3550000}]

at = AppTest.from_file('app.py').run()
assert not at.exception
assert at.metric[0].value == '12'
assert at.dataframe[1].value['Payment count'].sum() == 12
assert round(at.dataframe[1].value['Total amount ($)'].sum() * 100) == 13130001
at.number_input[0].set_value(10000)
at.checkbox[0].check()
at.run()
assert not at.exception
assert at.metric[0].value == '2'
assert at.metric[1].value == '$36,000.00'
assert at.dataframe[1].value['Vendor'].tolist() == ['Harbor Tech Solutions', 'Summit Services']
assert at.dataframe[1].value['Payment count'].sum() == 2
assert at.dataframe[1].value['Total amount ($)'].sum() == 36000
at.number_input[0].set_value(100000)
at.run()
assert not at.exception
assert at.metric[0].value == '0'
assert len(at.info) == 1
assert len(at.dataframe) == 0

with database() as uploaded_con, database() as other_visitor_con:
    vendor_ids = {row['vendor_id'] for row in uploaded_con.execute('SELECT vendor_id FROM vendors')}
    clean, errors = validate_payment_csv(CLEAN_SAMPLE_CSV.encode(), vendor_ids)
    assert not errors
    assert len(clean) == 3
    assert sum(row[3] for row in clean) == 1150051
    mixed_dates = CLEAN_SAMPLE_CSV.replace('2027-03-06', '03/06/2027').replace('2027-03-07', '03/07/2027')
    normalized, errors = validate_payment_csv(mixed_dates, vendor_ids)
    assert not errors and normalized == clean
    replace_payments(uploaded_con, normalized)
    assert [row['payment_id'] for row in payments(uploaded_con)] == [201, 202, 203]
    assert [row['payment_id'] for row in payments(uploaded_con, weekends_only=True)] == [202, 203]
    replace_payments(uploaded_con, clean)
    rows = payments(uploaded_con)
    assert (len(rows), sum(row['amount_cents'] for row in rows)) == (3, 1150051)
    assert sum(row['amount_cents'] for row in vendor_summary(rows)) == 1150051
    filtered = payments(uploaded_con, 2, 1000000, True)
    assert len(filtered) == 1 and filtered[0]['amount_cents'] == 1000001
    assert len(payments(other_visitor_con)) == 12
    rejected, errors = validate_payment_csv(INVALID_SAMPLE_CSV, vendor_ids)
    assert rejected == []
    assert len(errors) == 7
    for number in range(3, 10):
        assert any(error.startswith(f'CSV row {number}:') for error in errors)
    for explanation in ['duplicate', 'unknown', 'valid date', 'greater than zero',
                        'two decimal places', 'missing']:
        assert any(explanation in error for error in errors)
    invalid_cases = [
        ('payment_id,vendor_id,payment_date\n1,1,2027-03-01\n', 1),
        ('payment_id,vendor_id,payment_date,amount\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n1,1,2027-03-01,NaN\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n1,1,2027-03-01,Infinity\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n1,1,20270301,1.00\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n1,1,02/30/2027,1.00\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n1,1,03/01/27,1.00\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n1,1,2027-03-01,"1.00\n', 2),
        ('payment_id,vendor_id,payment_date,amount\n,,,\n', 2),
    ]
    for content, row_number in invalid_cases:
        rejected, errors = validate_payment_csv(content, vendor_ids)
        assert rejected == [] and errors
        assert all(error.startswith(f'CSV row {row_number}:') for error in errors)

# Exercise the actual upload/report path with in-memory files; no disk uploads.
with patch('streamlit.file_uploader', return_value=io.BytesIO(CLEAN_SAMPLE_CSV.encode())):
    uploaded_app = AppTest.from_file('app.py').run()
    assert not uploaded_app.exception
    assert uploaded_app.metric[0].value == '3'
    assert uploaded_app.metric[1].value == '$11,500.51'
    uploaded_app.number_input[0].set_value(10000)
    uploaded_app.checkbox[0].check()
    uploaded_app.run()
    assert not uploaded_app.exception
    assert uploaded_app.metric[0].value == '1'
    assert uploaded_app.metric[1].value == '$10,000.01'
    assert uploaded_app.dataframe[1].value['Total amount ($)'].sum() == 10000.01

with patch('streamlit.file_uploader', return_value=io.BytesIO(INVALID_SAMPLE_CSV.encode())):
    rejected_app = AppTest.from_file('app.py').run()
    assert not rejected_app.exception
    assert len(rejected_app.error) == 8
    assert rejected_app.metric[0].value == '12'
    assert rejected_app.metric[1].value == '$131,300.01'

print('Accounting, CSV export, vendor reconciliation, clean/invalid uploads, row errors, visitor isolation, and interactive filter checks passed.')
