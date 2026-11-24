"""Local persistence and transaction validation for ExpenseTracker Homework."""
import csv
import json
import math
import uuid
from datetime import date
from pathlib import Path

EXPENSE_CATEGORIES = ('Офис', 'Зарплаты', 'Маркетинг', 'Логистика', 'Налоги', 'Прочее')
INCOME_CATEGORIES = ('Продажи', 'Услуги', 'Инвестиции', 'Возвраты', 'Прочее')


def amount_from_text(text):
    value = float(str(text).replace(' ', '').replace(',', '.'))
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Сумма должна быть положительным конечным числом')
    return round(value, 2)


def make_transaction(kind, category, description, amount, when=None, transaction_id=None):
    if kind not in ('income', 'expense'):
        raise ValueError('Неверный тип операции')
    allowed = INCOME_CATEGORIES if kind == 'income' else EXPENSE_CATEGORIES
    if category not in allowed:
        raise ValueError('Неверная категория')
    when = when or date.today().isoformat()
    date.fromisoformat(when)
    return {'id': transaction_id or str(uuid.uuid4()), 'type': kind,
            'category': category, 'description': str(description).strip()[:200],
            'amount': amount_from_text(amount), 'date': when}


def totals(rows):
    income = round(sum(r['amount'] for r in rows if r['type'] == 'income'), 2)
    expense = round(sum(r['amount'] for r in rows if r['type'] == 'expense'), 2)
    return income, expense, round(income - expense, 2)


def validate_rows(raw):
    if not isinstance(raw, list):
        raise ValueError('Ожидался список операций')
    result, seen = [], set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError('Неверная запись')
        item = make_transaction(row['type'], row['category'], row.get('description', ''),
                                row['amount'], row['date'], row['id'])
        if item['id'] in seen:
            raise ValueError('Повторяющийся ID')
        seen.add(item['id'])
        result.append(item)
    return result


def load_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    return validate_rows(json.loads(path.read_text(encoding='utf-8')))


def save_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(validate_rows(rows), ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def export_csv(path, rows):
    with open(path, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Дата', 'Тип', 'Категория', 'Описание', 'Сумма (руб.)'])
        for r in rows:
            writer.writerow([r['date'], 'Доход' if r['type'] == 'income' else 'Расход',
                             r['category'], r['description'], r['amount']])
