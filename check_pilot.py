"""Known-answer accounting and Streamlit interaction checks."""
from app import database, payments, export, vendor_summary
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
print('Six accounting cases, CSV row counts, vendor-summary reconciliation, and interactive boundary/empty-result checks passed.')
