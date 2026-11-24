import tempfile
import unittest
from pathlib import Path
from storage import amount_from_text, make_transaction, totals, save_rows, load_rows, export_csv
from cloud import check_database_url

class TestTracker(unittest.TestCase):
    def test_balance(self):
        rows = [make_transaction('income', 'Продажи', 'Заказ', '15000'),
                make_transaction('expense', 'Маркетинг', 'Реклама', '2500')]
        self.assertEqual(totals(rows), (15000, 2500, 12500))

    def test_amount_validation(self):
        for bad in ('-1', '0', 'nan', 'inf', 'текст'):
            with self.assertRaises(ValueError):
                amount_from_text(bad)
        self.assertEqual(amount_from_text('1 200,50'), 1200.5)

    def test_persistence_and_csv(self):
        rows = [make_transaction('income', 'Услуги', 'Тест', '150')]
        with tempfile.TemporaryDirectory() as d:
            json_path = Path(d) / 'data.json'
            save_rows(json_path, rows)
            self.assertEqual(load_rows(json_path), rows)
            csv_path = Path(d) / 'out.csv'
            export_csv(csv_path, rows)
            self.assertIn('Услуги', csv_path.read_text(encoding='utf-8-sig'))

    def test_database_url(self):
        self.assertEqual(check_database_url('https://abc-default-rtdb.firebaseio.com/'),
                         'https://abc-default-rtdb.firebaseio.com')
        for bad in ('http://abc.firebaseio.com', 'https://example.com',
                    'https://abc.firebaseio.com/other'):
            with self.assertRaises(ValueError):
                check_database_url(bad)

if __name__ == '__main__':
    unittest.main()
