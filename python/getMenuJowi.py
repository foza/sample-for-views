import pymysql
import requests

connection = pymysql.connect(
    host='',
    user='bringo',
    password='',
    db='bringo',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)
'''
    bu cronni har 1 soatga quyish kerak
'''

try:
    with connection.cursor() as cursor:
        sql_jowi_manufacturers = "SELECT `id`, `bringo_id`, `jowi_id` as `jowi_id` FROM `integration_manufacturers` where `status` = '1'"
        a = cursor.execute(sql_jowi_manufacturers)
        fetch_jowi_manufacturers = cursor.fetchall()

        sql = "SELECT * FROM `integration_products`"
        b = cursor.execute(sql)
        fetch_products = cursor.fetchall()

        for one in fetch_jowi_manufacturers:
            id = one['jowi_id']
            url = "https://api.jowi.club/v010/restaurants/" + id
            querystring = {"sig": "3d8b570c9499dc7", "api_key": "JP3BDkdi1jXG_Io2Pt10mvjOdlneWaR-KmoYxsWS"}
            payload = ""
            response = requests.request("GET", url, data=payload, params=querystring)
            data = response.json()
            restoraunts = data['categories']
            for res in restoraunts:
                response = res['courses']
                for a in response:
                    if a['online_order'] == True:
                        online = 1
                    else:
                        online = 0
                    sql_z = f"SELECT * FROM `integration_products` WHERE `jowi_product_id` = '{a['id']}' ORDER BY `jowi_product_id` DESC"
                    cursor.execute(sql_z)
                    c = cursor.fetchone()
                    if not c:
                        if a['online_order'] == False:
                            sql_insert = f"INSERT INTO `integration_products` (`bringo_man_id`,`jowi_man_id`, `title`, `price`, `jowi_product_id`, `active`, `integration_id`) VALUES ('{one['bringo_id']}','{id}', '{a['title']}', '{a['price_for_online_order']}', '{a['id']}', '0', '{one['id']}')"
                        elif a['online_order'] == True:
                            sql_insert = f"INSERT INTO `integration_products` (`bringo_man_id`,`jowi_man_id`, `title`, `price`, `jowi_product_id`, `active`,  `integration_id`) VALUES ('{one['bringo_id']}','{id}', '{a['title']}', '{a['price_for_online_order']}', '{a['id']}', '1', '{one['id']}')"
                        print(sql_insert)
                        cursor.execute(sql_insert)
                        connection.commit()
                    for one in fetch_products:
                        one_price = float(one['price'])
                        a_price = float(a['price_for_online_order'])
                        if a_price != one_price and a['id'] == one['jowi_product_id']:
                            print(one['id'], one['title'], one['price'],'||||', a['price_for_online_order'])
                            sql_update_product = f"UPDATE `integration_products` SET `price` = '{a_price}' WHERE `id` ={one['id']}"
                            cursor.execute(sql_update_product)
                    try:

                        if online != c["active"]:
                            print(c["id"])
                            sql_update_product = f"UPDATE `integration_products` SET `active` = '{online}' WHERE `id` ={c['id']}"
                            cursor.execute(sql_update_product)
                    except:
                        print("hi")
    cursor.close()

    with connection.cursor() as cursor:
        sql_integration = 'SELECT * from `integration_products`'
        cursor.execute(sql_integration)
        int_products = cursor.fetchall()

        for one in int_products:
            if one['bringo_product_id'] != '0':
                sql_integration = f"SELECT * from `StoreProduct` where `id`={one['bringo_product_id']}"
                cursor.execute(sql_integration)
                pr = cursor.fetchone()
                int_price = float(one['price'])
                br_price = float(pr['price'])
                if int_price == br_price:
                    print(pr['id'], pr['price'])
                else:
                    print(int_price, br_price)
                    sql_update = f"UPDATE `StoreProduct` SET `price` = {one['price']} WHERE `id` ={one['bringo_product_id']}"
                    cursor.execute(sql_update)

finally:
    connection.close()
