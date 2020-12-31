# coding=utf-8
import psycopg2.extras

if __name__ == '__main__':

    from configparser import ConfigParser
    import os

    conn = ConfigParser()

    file_path = os.path.join(os.path.abspath('.'), 'config.ini')
    if not os.path.exists(file_path):
        raise FileNotFoundError("文件不存在")

    conn.read(file_path)
    pghost = conn.get('api', 'pghost')
    pgport = conn.get('api', 'pgport')
    pguser = conn.get('api', 'pguser')
    pgpassword = conn.get('api', 'pgpassword')
    pgdatabase = conn.get('api', 'pgdatabase')
    iotdbIp = conn.get('api', 'iotdbIp')
    iotdbUser = conn.get('api', 'iotdbUser')
    iotdbPassword = conn.get('api', 'iotdbPassword')

    # conn = psycopg2.connect(host='223.99.13.54', port=5098, user='root', password='root', database='dataway')
    conn = psycopg2.connect(host=pghost, port=pgport, user=pguser, password=pgpassword, database=pgdatabase)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    print(cursor)