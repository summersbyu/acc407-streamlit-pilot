"""Known-answer accounting and Streamlit interaction checks."""
from app import database, payments, export
from streamlit.testing.v1 import AppTest

with database() as con:
    cases = [
        (None, 0, False, 8, 7425001),
        (2, 0, False, 3, 3550000),
        (None, 0, True, 4, 2800000),
        (None, 1000000, False, 3, 5000001),
        (None, 1000000, True, 1, 1500000),
        (None, 10000000, False, 0, 0),
    ]
    for vendor, threshold, weekend, count, total in cases:
        rows = payments(con, vendor, threshold, weekend)
        assert (len(rows), sum(row['amount_cents'] for row in rows)) == (count, total)
        assert len(export(rows).splitlines()) == count + 1

at = AppTest.from_file('app.py').run()
assert not at.exception
assert at.metric[0].value == '8'
at.number_input[0].set_value(10000)
at.checkbox[0].check()
at.run()
assert not at.exception
assert at.metric[0].value == '1'
assert at.metric[1].value == '$15,000.00'
at.number_input[0].set_value(100000)
at.run()
assert not at.exception
assert at.metric[0].value == '0'
assert len(at.info) == 1
print('Six accounting cases, CSV row counts, and interactive boundary/empty-result checks passed.')
