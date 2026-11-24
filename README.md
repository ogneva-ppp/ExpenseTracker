<div align="center">

# 🌸 ExpenseTracker Rose

**Личные финансы в розовых тонах**

Учитывай доходы и расходы · Анализируй · Планируй

![Python](https://img.shields.io/badge/Python-3.11-D98AAF?style=flat-square&logo=python&logoColor=white)
![Kivy](https://img.shields.io/badge/Kivy-GUI-E8A4C4?style=flat-square)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Charts-C66B98?style=flat-square)
![Firebase](https://img.shields.io/badge/Firebase-Cloud-D98AAF?style=flat-square&logo=firebase&logoColor=white)
![REST API](https://img.shields.io/badge/REST-API-E8A4C4?style=flat-square)

</div>

---

## ♡ О проекте

**ExpenseTracker Rose** — приложение для учёта личных финансов на Python с графическим интерфейсом в пастельных розовых тонах. Оно помогает отслеживать доходы и расходы, контролировать баланс и анализировать финансовые операции.

## ✨ Возможности

| | Функция | Описание |
| :---: | :--- | :--- |
| 💗 | Учёт финансов | Добавление доходов и расходов по категориям |
| 💰 | Баланс | Автоматический расчёт остатка средств |
| 📊 | Аналитика | Круговая диаграмма расходов и сравнение доходов и расходов по месяцам |
| ☁️ | Облако | Ручная синхронизация с Firebase через REST API |
| 🔎 | Управление | Поиск, фильтрация, редактирование и удаление операций |
| 📁 | Экспорт | Выгрузка всех операций в CSV |

<!-- Когда будут готовы скриншоты, добавьте раздел «Интерфейс» с изображениями screenshots/main.png и screenshots/charts.png. -->

## 🌷 Быстрый запуск

Рекомендуется Python 3.11. Команды для Windows PowerShell:

```powershell
git clone https://github.com/ogneva-ppp/ExpenseTracker.git
cd ExpenseTracker
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Локальные функции доступны без подключения к Firebase. Операции сохраняются в JSON в пользовательском каталоге Kivy.

## ☁️ Облачная синхронизация

1. Создайте проект в [Firebase Console](https://console.firebase.google.com/).
2. Включите Authentication → Email/Password и создайте пользователя.
3. Создайте Realtime Database и опубликуйте правила из [`firebase.rules.json`](firebase.rules.json).
4. Откройте «Облако» в приложении, укажите Database URL, Web API Key, email и пароль.
5. Выполните вход и выберите отправку или загрузку данных.

> Синхронизация выполняется вручную: отправка заменяет облачный список, загрузка заменяет локальный список (с созданием резервной копии). Правила ограничивают доступ по UID пользователя. Не публикуйте пароли и токены.

## 🛠 Структура проекта

```text
ExpenseTracker/
├── main.py              # Интерфейс и диаграммы
├── storage.py           # Операции и локальное хранение
├── cloud.py             # Firebase REST API
├── firebase.rules.json  # Правила доступа
├── requirements.txt     # Зависимости
└── tests/               # Тесты бизнес-логики
```

Запуск тестов:

```bash
python -m unittest discover -s tests -v
```

## 🎓 О разработке

Учебный проект по разработке приложений на Python и Kivy. Реализованы визуализация финансовых данных, облачная синхронизация и учёт доходов с расчётом баланса. Текущая версия предназначена для запуска на компьютере.

---

<div align="center">

Made with ♡ and Python

</div>
