from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
"""------------ for google sheets parsing ----------------"""
import argparse
from flask import Flask, render_template, request, jsonify, abort, make_response
from flask_sqlalchemy import SQLAlchemy
import csv
import pandas as pd

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///user:password@localhost/mydatabase'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:friz446625@localhost:5432/csv_grep1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
""" ------- Формируем нашу Postgres БД ------- """
products_reviews = db.Table('products_reviews',
                            db.Column('product_id', db.Integer, db.ForeignKey('product.id')),
                            db.Column('review_id', db.Integer, db.ForeignKey('review.id')))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    asin = db.Column(db.String(100), nullable=False, unique=True)
    reviews = db.relationship('Review', secondary=products_reviews, backref=db.backref('products'), lazy='dynamic')

    def __init__(self, title, asin):
        self.title = title.strip()
        self.asin = asin.strip()


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asin = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    review = db.Column(db.Text(), nullable=False)

    def __init__(self, asin, title, review):
        self.asin = asin.strip()
        self.title = title.strip()
        self.review = review.strip()


db.create_all()


def parse_gs_link(filename: str):
    """ Парсит ссылку на Google Таблицу - на выходе SPREADSHEET_ID (длинной 44 символа)\n
    пример: '1roypo_8amDEIYc-RFCQrb3WyubMErd3bxNCJroX-HVE'"""
    rez = filename.strip().split('/')
    for i in rez:
        if len(i) == 44:
            # print("SAMPLE_SPREADSHEET_ID = ", i)
            return i


def google_sheets_to_postgres(filename: str):
    """ Парсит данные из Google Sheets таблиц \n
    filename::ссылка на google таблицу \n
    ( пример https://docs.google.com/spreadsheets/d/1roypo_8amDEIYc-RFCQrb3WyubMErd3bxNCJroX-HVE/edit#gid=0 )"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    # SAMPLE_SPREADSHEET_ID = '1roypo_8amDEIYc-RFCQrb3WyubMErd3bxNCJroX-HVE'
    SAMPLE_SPREADSHEET_ID = parse_gs_link(filename)

    """ ------- Авторизация ------- """
    creds = None
    if os.path.exists('static/token.json'):
        creds = Credentials.from_authorized_user_file('static/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'static/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('static/token.json', 'w') as token:
            token.write(creds.to_json())

    """ ------- Парсим Google Таблицу ------- """
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SAMPLE_SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        name = sheet_metadata.get("properties", {}).get("title")  # name='Products.csv'
        title = sheets[0].get("properties", {}).get("title", "Sheet1")

        SAMPLE_RANGE_NAME = f'{title}!A2:Z1000'  # c какой по какую ячейку парсить Google Таблицу

        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        """ Записываем данные Sheets в Postgres БД """
        write_to_postgres(name, values, is_google_sheets=True)

    except HttpError as err:
        print(err)


def write_to_postgres(filename, reader, is_google_sheets=False):
    """ Записывает полученные данные в нашу Postgres БД \n
    (когда пишем из google sheets) установить is_google_sheets=True (чтобы добавило первую строку записей) """

    column_is_first = True
    if is_google_sheets:
        column_is_first = False

    print(f"{filename=}")

    if not filename.endswith('.csv'):
        filename = filename + '.csv'

    if filename == 'Products.csv' or 'Products.csv' in filename:
        for line in reader:
            if column_is_first:
                column_is_first = False
                continue
            try:
                db.session.add(Product(line[0], line[1]))
                db.session.commit()
                print(f"db.session.add - PRODUCT - {line[1]} - OK")
            except Exception as e:
                print(e)

    elif filename == 'Reviews.csv' or 'Reviews.csv' in filename:
        for line in reader:
            if column_is_first:
                column_is_first = False
                continue
            try:
                db.session.add(Review(line[0], line[1], line[2]))
                # print(f"{line[0]} - {line[1]} - {line[2]}")
                db.session.commit()
                print(f"db.session.add - REVIEW - {line[0]} - OK")
            except Exception as e:
                print(e)

    else:
        raise Exception


def csv_to_postgres(filename: str):
    """ Парсит файл(лы) CSV и записывает в Postgres БД """

    if type(filename) == str:
        try:
            if 'docs.google.com' in filename:
                google_sheets_to_postgres(filename)
        except:
            print(f"Не знаю как спарсить этот Google Sheets:\n{filename}")

        try:
            if not filename.endswith('.csv'):
                filename = filename + '.csv'
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                # print(f"{reader=}")
                write_to_postgres(filename, reader)
        except:
            print(f"Не знаю как спарсить этот файл: {filename} !!!")

    elif type(filename) == list:
        """ Если ввели несколько CSV файлов \n Например ['Reviews.csv','Products.csv'] """
        for i in filename:
            csv_to_postgres(i)


@app.route('/')
def CsvToHtml():
    """ формирует HTML страничку показывающую содержимое наших CSV файлов """
    # return render_template('index.html')
    product_data = pd.read_csv("Products.csv")
    print(f"{product_data=}")
    review_data = pd.read_csv("Reviews.csv")
    print(f"{review_data=}")
    # for i in range(0,10):
    #     print(f"{data[i]=}")
    return render_template("index.html", products=[product_data.to_html()]
                           , titles=[''], reviews=[review_data.to_html()])


@app.route('/test', methods=['GET'])
def test():
    return {
        'test': 'test1'
    }


@app.route("/products", methods=['GET'])
def get_products():
    """ [GET] Получает все Продукты из БД (в формате JSON)"""
    allProducts = Product.query.all()
    output = []
    for product in allProducts:
        currProduct = {}
        currProduct['title'] = product.title
        currProduct['asin'] = product.asin
        output.append(currProduct)
    return jsonify(output)


"""
{
    {
        "asin": "B06X14Z8JP",
        "title": "JVC Blue and Red Wireless Water Resistant Pivot Motion Sport Headphone with Locking Ear Fit HA-ET50BTA"
    },
    {
    ...
    }
"""


@app.route("/products", methods=['POST'])
def post_products():
    """ [POST] Добавляем Продукт в БД """
    if not request.json or not 'title' in request.json:
        abort(400)
    productData = request.get_json()
    product = Product(title=productData['title'], asin=productData['asin'])
    db.session.add(product)
    db.session.commit()
    return jsonify(productData), 201  # 201 = Created


# @app.route("/reviews/<int:product_id>", methods=['PUT'])
# def post_products(product_id):
#     productData = Product.query.get(product_id)
#     product = Product(title=productData['title'], asin=productData['asin'])
#     db.session.add(product)
#     # db.session.update(product)
#     db.session.commit()
#     return jsonify(productData)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def main(infile=None, start=False):
    if infile != None:
        csv_to_postgres(infile)
    if start:
        app.run(host="localhost", port=5000)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Парсинг CSV файла в нашу Postgres БД')
    parser.add_argument("-i", "--infile", nargs='*'
                        , help="Входной файл\nПример: python app.py -i Products.csv")
    parser.add_argument("-s", "--start", help="Запустить Flask\nПример2: python app.py -s 1")
    args = parser.parse_args()
    if args.infile:
        main(args.infile)
        if args.start:
            main(0, args.start)
    else:
        print("Введите параметры.\n Пример: python app.py -i Products.csv Reviews.csv\nПример2: python app.py -s 1")
        """
        Примеры допустимых вводимых комманд:
        
        python app.py -i Reviews.csv
        python app.py -i Products.csv Reviews.csv
        python app.py -i Products.csv Reviews.csv -s 1
        python app.py -i C:\Django\\Unilime-CSV-to-Flask-API\Products.csv
        python app.py -i https://docs.google.com/spreadsheets/d/1roypo_8amDEIYc-RFCQrb3WyubMErd3bxNCJroX-HVE/edit#gid=0
        python app.py -i https://docs.google.com/spreadsheets/d/1iSR0bR0TO5C3CfNv-k1bxrKLD5SuYt_2HXhI2yq15Kg/edit#gid=0

        """
