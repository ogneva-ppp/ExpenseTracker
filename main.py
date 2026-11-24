"""ExpenseTracker Homework: Kivy, Kivy Garden Matplotlib, Firebase REST."""
from collections import defaultdict
from datetime import date
from pathlib import Path
from threading import Thread

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.spinner import SpinnerOption

BG = (1, .94, .97, 1)
INK = (.39, .12, .25, 1)
PINK = (.93, .66, .78, 1)
WHITE = (1, .99, 1, 1)


def rounded(widget, color, radius=14):
    with widget.canvas.before:
        Color(*color)
        shape = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    def update(*_):
        shape.pos = widget.pos
        shape.size = widget.size
    widget.bind(pos=update, size=update)
    return widget

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button as BaseButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label as BaseLabel
from kivy.uix.popup import Popup as BasePopup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner as BaseSpinner
from kivy.uix.textinput import TextInput

from cloud import check_database_url, download, login, upload
from storage import (EXPENSE_CATEGORIES, INCOME_CATEGORIES, amount_from_text,
                     export_csv, load_rows, make_transaction, save_rows, totals,
                     validate_rows)


class Label(BaseLabel):
    def __init__(self, **kwargs):
        kwargs.setdefault('color', INK)
        super().__init__(**kwargs)


class Button(BaseButton):
    def __init__(self, **kwargs):
        super().__init__(background_normal='', background_down='', background_color=(0,0,0,0), color=INK, **kwargs)
        rounded(self, PINK)


class PinkOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(background_normal='', background_down='', background_color=PINK, color=INK, **kwargs)


class Spinner(BaseSpinner):
    def __init__(self, **kwargs):
        super().__init__(background_normal='', background_down='', background_color=PINK, color=INK, option_cls=PinkOption, **kwargs)


class Popup(BasePopup):
    def __init__(self, **kwargs):
        super().__init__(background='', background_color=BG, title_color=INK, separator_color=PINK, **kwargs)
        if self.content:
            rounded(self.content, BG, 8)


def btn(text, callback, height=46):
    widget = Button(text=text, size_hint_y=None, height=height)
    widget.bind(on_release=lambda *_: callback())
    return widget


def field(hint='', text='', password=False):
    return TextInput(text=text, hint_text=hint, multiline=False, password=password,
                     size_hint_y=None, height=44, background_normal="", background_active="", background_color=WHITE, foreground_color=INK, cursor_color=INK, hint_text_color=(.55,.32,.43,1))


def label(text, height=35):
    return Label(text=text, size_hint_y=None, height=height, halign='center')


class Tracker(App):
    def build(self):
        self.title = 'ExpenseTracker — Rose'
        Window.clearcolor = BG
        self.folder = Path(self.user_data_dir)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.data_file = self.folder / 'transactions.json'
        try:
            self.rows = load_rows(self.data_file)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.rows = []
            self.startup_error = str(exc)
        else:
            self.startup_error = ''
        self.cloud_uid = None
        self.cloud_token = None
        self.database_url = ''
        root = BoxLayout(orientation='vertical', padding=18, spacing=10)
        heading = label('EXPENSE TRACKER', 45)
        heading.font_size = '24sp'
        heading.bold = True
        root.add_widget(heading)
        self.summary = label('', 95)
        self.summary.font_size = '20sp'
        rounded(self.summary, (.98,.80,.87,1))
        root.add_widget(self.summary)
        actions = GridLayout(cols=3, size_hint_y=None, height=104, spacing=8)
        for name, action in [('Добавить', self.edit_popup), ('Графики', self.charts_popup),
                             ('CSV', self.export), ('Облако', self.cloud_popup),
                             ('Статистика', self.statistics), ('Обновить', self.refresh)]:
            actions.add_widget(btn(name, action))
        root.add_widget(actions)
        filters = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.search = field('Поиск')
        self.search.bind(text=lambda *_: self.refresh())
        filters.add_widget(self.search)
        self.type_filter = Spinner(text='Все', values=('Все', 'Доходы', 'Расходы'), size_hint_x=.38)
        self.type_filter.bind(text=lambda *_: self.refresh())
        filters.add_widget(self.type_filter)
        root.add_widget(filters)
        scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)
        self.refresh()
        if self.startup_error:
            Clock.schedule_once(lambda *_: self.message('Ошибка файла', self.startup_error), .2)
        return root

    def message(self, title, text):
        body = BoxLayout(orientation='vertical', padding=12, spacing=8)
        body.add_widget(Label(text=str(text), halign='center'))
        popup = Popup(title=title, content=body, size_hint=(.9, .45))
        body.add_widget(btn('Закрыть', popup.dismiss))
        popup.open()

    def persist(self):
        save_rows(self.data_file, self.rows)
        self.refresh()

    def refresh(self):
        income, expense, balance = totals(self.rows)
        self.summary.text = 'Доходы: {:.2f} руб.    Расходы: {:.2f} руб.\nБаланс: {:.2f} руб.'.format(income, expense, balance)
        self.list_box.clear_widgets()
        filtered = sorted(self.rows, key=lambda x: (x['date'], x['id']), reverse=True)
        query = self.search.text.lower().strip()
        if self.type_filter.text == 'Доходы':
            filtered = [r for r in filtered if r['type'] == 'income']
        elif self.type_filter.text == 'Расходы':
            filtered = [r for r in filtered if r['type'] == 'expense']
        for row in filtered:
            if query and query not in (row['description'] + ' ' + row['category']).lower():
                continue
            line = BoxLayout(size_hint_y=None, height=65, spacing=8, padding=5)
            rounded(line, WHITE)
            kind = '+' if row['type'] == 'income' else '-'
            description = row['description'][:22]
            line.add_widget(Label(text='{} {}\n{} | {} | {:.2f} руб.'.format(
                row['date'], description, row['category'], kind, row['amount']),
                halign='left'))
            line.add_widget(btn('Изменить', lambda r=row: self.edit_popup(r), 55))
            line.add_widget(btn('Удалить', lambda r=row: self.confirm_delete(r), 55))
            self.list_box.add_widget(line)
        if not self.list_box.children:
            self.list_box.add_widget(label('Нет операций', 60))

    def edit_popup(self, existing=None):
        existing = existing or {}
        box = BoxLayout(orientation='vertical', padding=12, spacing=7)
        kind = Spinner(text='Доход' if existing.get('type') == 'income' else 'Расход',
                       values=('Доход', 'Расход'), size_hint_y=None, height=44)
        category = Spinner(size_hint_y=None, height=44)
        def update_categories(*_):
            values = INCOME_CATEGORIES if kind.text == 'Доход' else EXPENSE_CATEGORIES
            category.values = values
            category.text = existing.get('category') if existing.get('category') in values else values[0]
        kind.bind(text=update_categories)
        update_categories()
        description = field('Описание', existing.get('description', ''))
        amount = field('Сумма, руб.', str(existing.get('amount', '')))
        when = field('Дата ГГГГ-ММ-ДД', existing.get('date', date.today().isoformat()))
        for item in (kind, category, description, amount, when):
            box.add_widget(item)
        popup = Popup(title='Изменить операцию' if existing else 'Новая операция',
                      content=box, size_hint=(.92, .8))
        def save():
            try:
                item = make_transaction('income' if kind.text == 'Доход' else 'expense',
                                        category.text, description.text, amount.text,
                                        when.text, existing.get('id'))
                if existing:
                    self.rows = [item if r['id'] == existing['id'] else r for r in self.rows]
                else:
                    self.rows.append(item)
                self.persist()
                popup.dismiss()
            except (ValueError, OSError) as exc:
                self.message('Ошибка', str(exc))
        box.add_widget(btn('Сохранить', save))
        box.add_widget(btn('Отмена', popup.dismiss))
        popup.open()

    def confirm_delete(self, row):
        box = BoxLayout(orientation='vertical', padding=10, spacing=5)
        box.add_widget(label('Удалить эту операцию?'))
        popup = Popup(title='Подтверждение', content=box, size_hint=(.8, .4))
        def remove():
            self.rows = [r for r in self.rows if r['id'] != row['id']]
            self.persist()
            popup.dismiss()
        box.add_widget(btn('Да, удалить', remove))
        box.add_widget(btn('Отмена', popup.dismiss))
        popup.open()

    def statistics(self):
        income, expense, balance = totals(self.rows)
        by_category = defaultdict(float)
        for r in self.rows:
            if r['type'] == 'expense':
                by_category[r['category']] += r['amount']
        top = max(by_category, key=by_category.get) if by_category else 'нет данных'
        self.message('Статистика', 'Операций: {}\nДоходы: {:.2f}\nРасходы: {:.2f}\nБаланс: {:.2f}\nГлавная статья расходов: {}'.format(
            len(self.rows), income, expense, balance, top))

    def charts_popup(self):
        try:
            import matplotlib
            matplotlib.use('Agg')
            from matplotlib.figure import Figure
            from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
        except ImportError as exc:
            self.message('Графики', 'Установите зависимости из requirements.txt:\n' + str(exc))
            return
        box = BoxLayout(orientation='vertical', spacing=5, padding=5)
        figure = Figure(figsize=(7, 7), dpi=90, facecolor="#fff0f5")
        ax1 = figure.add_subplot(211)
        ax2 = figure.add_subplot(212)
        expenses = defaultdict(float)
        months = defaultdict(lambda: {'income': 0., 'expense': 0.})
        for r in self.rows:
            months[r['date'][:7]][r['type']] += r['amount']
            if r['type'] == 'expense':
                expenses[r['category']] += r['amount']
        if expenses:
            ax1.pie(list(expenses.values()), labels=list(expenses.keys()), autopct='%1.0f%%', colors=['#d66a99','#f3b5cf','#a94d78','#e88ab0','#f8d3e3'], textprops={'fontsize': 8, 'color':'#792747'})
        else:
            ax1.text(.5, .5, 'Нет расходов', ha='center', va='center')
        ax1.set_title('Расходы по категориям')
        if months:
            keys = sorted(months)[-6:]
            x = list(range(len(keys)))
            ax2.bar([v-.2 for v in x], [months[k]['income'] for k in keys], width=.4, label='Доходы', color='#b54c7a')
            ax2.bar([v+.2 for v in x], [months[k]['expense'] for k in keys], width=.4, label='Расходы', color='#efa9c8')
            ax2.set_xticks(x, keys, rotation=20)
            ax2.legend(fontsize=8)
        else:
            ax2.text(.5, .5, 'Нет операций', ha='center', va='center')
        ax2.set_title('Доходы и расходы по месяцам')
        for ax in (ax1, ax2):
            ax.set_facecolor("#fff8fb")
            ax.title.set_color("#792747")
            ax.tick_params(colors="#792747")
            for spine in ax.spines.values():
                spine.set_color("#e5b4ca")
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        FigureCanvasAgg(figure)
        figure.tight_layout()
        box.add_widget(FigureCanvasKivyAgg(figure))
        popup = Popup(title='Графики (Kivy Garden + Matplotlib)', content=box, size_hint=(.97, .95))
        box.add_widget(btn('Закрыть', popup.dismiss, 42))
        popup.open()

    def export(self):
        path = self.folder / 'transactions_export.csv'
        try:
            export_csv(path, self.rows)
            self.message('Экспорт CSV', 'Файл сохранён:\n' + str(path))
        except OSError as exc:
            self.message('Ошибка экспорта', str(exc))

    def cloud_popup(self):
        box = BoxLayout(orientation='vertical', padding=12, spacing=8)
        box.add_widget(label('Firebase Realtime Database + Email/Password', 45))
        database = field('Database URL (https://...firebasedatabase.app)')
        key = field('Firebase Web API key')
        email = field('Email пользователя')
        password = field('Пароль', password=True)
        for item in (database, key, email, password):
            box.add_widget(item)
        status = label('Сначала войдите в Firebase', 45)
        box.add_widget(status)
        popup = Popup(title='Синхронизация Firebase', content=box, size_hint=(.95, .88))
        def run_async(operation, success):
            status.text = 'Выполняется запрос...'
            def worker():
                try:
                    result = operation()
                except Exception as exc:
                    Clock.schedule_once(lambda _, msg=str(exc): setattr(status, 'text', 'Ошибка: ' + msg[:180]))
                else:
                    Clock.schedule_once(lambda _, result=result: success(result))
            Thread(target=worker, daemon=True).start()
        def sign_in():
            try:
                self.database_url = check_database_url(database.text)
            except ValueError as exc:
                status.text = str(exc)
                return
            def done(result):
                self.cloud_uid, self.cloud_token = result
                status.text = 'Вход выполнен. Выберите загрузку или выгрузку.'
            run_async(lambda: login(key.text, email.text, password.text), done)
        def require_login():
            if not self.cloud_token:
                status.text = 'Сначала выполните вход'
                return False
            return True
        def push():
            if require_login():
                snapshot = validate_rows(self.rows)
                run_async(lambda: upload(self.database_url, self.cloud_uid, self.cloud_token, snapshot),
                          lambda _: setattr(status, 'text', 'Данные отправлены в облако (заменили прежние).'))
        def pull():
            if require_login():
                def done(raw):
                    try:
                        rows = validate_rows(raw)
                        # Backup before replacing local data.
                        backup = self.folder / 'transactions_before_cloud.json'
                        save_rows(backup, self.rows)
                        self.rows = rows
                        self.persist()
                        status.text = 'Облако загружено; локальные данные заменены. Есть резервная копия.'
                    except (ValueError, KeyError, TypeError, OSError) as exc:
                        status.text = 'Ошибка данных: ' + str(exc)[:140]
                run_async(lambda: download(self.database_url, self.cloud_uid, self.cloud_token), done)
        box.add_widget(btn('1. Войти', sign_in))
        box.add_widget(btn('2. Отправить локальные данные в облако', push))
        box.add_widget(btn('3. Скачать из облака (заменит локальные)', pull))
        box.add_widget(btn('Закрыть', popup.dismiss))
        popup.open()


if __name__ == '__main__':
    Tracker().run()
