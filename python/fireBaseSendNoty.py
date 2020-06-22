import pymysql
import requests
import json
import datetime

# Connect to the database
connection = pymysql.connect(
    host='',
    user='bringo',
    password='',
    db='bringo',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        # get courier
        sql_courier = '''
            SELECT
                ocl.courier_id,
                oc.name,
                oc.phone,
                oc.reg_id,
                oc.id
            FROM
                OrderCourierLocation AS ocl
            INNER JOIN OrderCourier oc ON
                oc.id = ocl.courier_id 
                AND oc.is_active = 1 
                AND oc.send_to = 1 
                AND oc.status = 1 
                AND ocl.`last_update` > DATE_SUB(NOW(), INTERVAL 10 MINUTE) 
                AND NOT EXISTS(
                    SELECT
                        COUNT(*) COUNT
                    FROM
                        `Order` o
                    WHERE
                        o.courier_id = oc.id AND(
                            o.status_id = 5 OR o.status_id = 6 OR o.status_id = 1
                        )
                    HAVING
                        COUNT(*) > 2)'''
        couriers = cursor.execute(sql_courier)
        fetch_couriers = cursor.fetchall()
        cursor.close()

    with connection.cursor() as cursor:
        # Read a orders
        sql = '''
                SELECT
                    `id`,
                    `order_code`,
                    status_id,
                    courier_id
                FROM
                    `Order`
                WHERE
                    status_id = 6 
                    AND delivery_id <> 15 
                    AND(courier_id IS NULL OR courier_id <= 0)'''
        a = cursor.execute(sql)
        fetchall = cursor.fetchall()
        order = fetchall
        cursor.close()
    with connection.cursor() as cursor:

        cursor.close()
finally:
    close = connection.close()

    array = []
    for cur in fetch_couriers:
        array.append(cur['reg_id'])

    info_array = []
    for one in order:
        info_array.append(one['order_code'])


def sendNoty(array):
    url = "https://fcm.googleapis.com/fcm/send"
    message = {"title": "Новый заказ", "message": "Поторопись, у тебя новые заказы.", "vibrate": 1, "sound": 1,
               "type": "new", "count": 0}
    fields = {
        'registration_ids': array,
        'data': message,
        'time_to_live': 3
    }
    headers = {
        'Authorization': 'key=AAAAUJHPc4Q:APA91bEqFhybsbdo6tjN_Mp0OP_StiUOt3IDJr-EFNGMKEdl7kBOO6q3Kz5NU8Jg6SCWvDTQrvKRx5IoxCIOaMW5Xrz2ZITkAUt7zFud3TWUR25br3lbxFVk2dO2frY5zMSiroFqWdFQOcjWixIIKHrLqmmcpBtC5g',
        'Content-Type': 'application/json'
    }
    data = json.dumps(fields)
    r = requests.post(url, data=data, headers=headers)
    # print(r.text)


def printit():
    sendNoty(array)
    url = "https://api.telegram.org/*****/sendMessage"
    send_order = len(info_array)
    send_courier = len(array)
    date_time = datetime.datetime.now()
    times = date_time.strftime("%Y-%b-%d %H:%M:%S")
    text = 'Курьер количества:' + str(send_courier) + ',\nКоличества заказа: ' + str(
        send_order) + '\nВремя отправки:' + times
    querystring = {"chat_id": "@cron_push_courier", "text": text}
    payload = ""
    response = requests.request("GET", url, data=payload, params=querystring)


printit()
