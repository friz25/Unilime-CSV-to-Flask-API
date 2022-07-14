# 📊️ Unilime-CSV-to-Flask-API

Тестовое задание - Парсинг CSV файлов + Flask API

<details><summary>🏗 Cамо Тестовое задание :</summary>

Нужно написать мини app, в котором:
Распарсить два 2 .csv файла (ссылки прилагаются) (Products, Reviews), данные сохранять в базу (использовать Postgres, соотношения one-to-many или many-to-many на выбор). Парсинг и сохранение в базу можно реализовать консольной командой.

Products
https://docs.google.com/spreadsheets/d/1roypo_8amDEIYc-RFCQrb3WyubMErd3bxNCJroX-HVE/edit#gid=0

Reviews
https://docs.google.com/spreadsheets/d/1iSR0bR0TO5C3CfNv-k1bxrKLD5SuYt_2HXhI2yq15Kg/edit#gid=0

На основе Flask создать API endpoint (GET), который будет возвращать данные в формате json следующего содержания:
По id товара отдавать информацию по этому товару (ASIN, Title) и Reviews этого товара с пагинацией.
Желательно создать кеширование для GET endpoint. 

Создать второй API endpoint (PUT), который будет писать в базу данных новый Review для товара (по id).

Требования:
- Python 3
- Flask
- pep 8
- Postgres DB
- requirements.txt

</details>
<details><summary>🧙 Как запустить / Установка :</summary>

клонируем проект из github'a себе на рабочий пк<br><br>
Создать виртуальное окружение<br>
`python -m venv venv`<br><br>
зайдём в виртуальное окружение с терминала (venv/Scripts/activate)<br><br>
Установить зависимости<br>
`pip install -r requirements.txt`<br><br>
Установим PostgreSQL. Запустим pgAdmin. Создадим БД `csv_grep1`<br>
<br>
*если всё ОК, проект запустился 🧙
</details>


Примеры допустимых вводимых комманд:
        
    python app.py -i Reviews.csv
    python app.py -i Products.csv Reviews.csv
    python app.py -i Products.csv Reviews.csv -s 1
    python app.py -i C:\Django\\Unilime-CSV-to-Flask-API\Products.csv
    python app.py -i https://docs.google.com/spreadsheets/d/1roypo_8amDEIYc-RFCQrb3WyubMErd3bxNCJroX-HVE/edit#gid=0
    python app.py -i https://docs.google.com/spreadsheets/d/1iSR0bR0TO5C3CfNv-k1bxrKLD5SuYt_2HXhI2yq15Kg/edit#gid=0

(может парсить список CSV файлов / список ссылок на Google Таблицы)