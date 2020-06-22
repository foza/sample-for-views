#!venv/bin/python3
from flask import Flask, jsonify, abort, request, make_response
from flask_httpauth import HTTPBasicAuth
from components.functions import *
from components.config import Config
from components.database import Database
from os import environ
import requests
app = Flask(__name__)
auth = HTTPBasicAuth()
config = Config()


@auth.verify_password
def verify_password(username, password):
    db = Database(config)
    user = db.getOneByParam("SELECT `password` FROM `user` WHERE `username` = %s", username)
    if user is not None and user.get("password") is not None:
        if validatePassword(password, user.get("password")):
            return True
    return False


@auth.error_handler
def unauthorized():
    return make_response(get_response("Несанкционированный доступ", False), 403)


@app.errorhandler(404)
def not_found(error):
    return make_response(get_response("Страница не найдена", False), 404)


@app.route('/')
def index():
    return "Welcome retaraunts api"


@app.route(config.url_v1 + '/register', methods=['POST'])
def register():
    if not request.json:
        abort(400)

    phone = request.json.get("phone", None)
    intro_token = request.json.get("intro_token", None)

    if phone is None:# or len(str(phone)) != 9:
        abort(400)

    if intro_token is None or intro_token != config.intro_token:
        abort(400)

    code = randomSmsCode()
    db = Database(config)
    user = db.getOneByParam("SELECT id FROM `user_register` WHERE `phone` = %s", phone)
    if not user:
        sql = """INSERT INTO `user_register`(
                    `phone`, `sms_code`, `password`, `token`, `send_count`,
                    `fail_count`, `created_at`, `updated_at`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        db.executeByParams(sql, [phone, code, randomString(), randomString(25), 0, 0, currentTime(), currentTime()])
    else:
        user = db.executeByParams("UPDATE `user_register` SET `sms_code` = %s WHERE `phone` = %s", [code, phone])

    user = db.getOneByParam("SELECT sms_code, token FROM `user_register` WHERE `phone` = %s", phone)

    # send sms to phone number
    headers = {'User-Agent': 'Mozilla/5.0'}
    payload = {'login': Config.sms_login, 'key': Config.sms_pass, 'text': code, 'phone': phone, 'sender': 'Bringo.uz'}
    requests.post(Config.sms_url, data=payload, headers=headers)
    return get_response({
        "code": user.get("sms_code", code),
        "token": user.get("token", None)
    }, True)


@app.route(config.url_v1 + '/check/code', methods=['POST'])
def checkCode():
    if not request.json:
        abort(400)

    phone = request.json.get("phone", None)
    code = request.json.get("code", None)
    token = request.json.get("token", None)

    if not code or not phone or not token:
        abort(400)

    db = Database(config)
    user = db.getOneByParam("SELECT `id`, `sms_code`, `token` FROM `user_register` WHERE `phone` = %s", phone)

    if not user or user.get("token") != token:
        abort(403)

    if user.get("sms_code") != code:
        return get_response("Ваш код SMS неверен", False)

    id = user.get("id")
    new_token = randomString(25)
    user = db.executeByParams("UPDATE `user_register` SET `token` = %s WHERE `id` = %s", [new_token, id])

    return get_response({
        "new_token": new_token
    }, True)


@app.route(config.url_v1 + '/set/password', methods=['POST'])
def setPassword():
    if not request.json:
        abort(400)

    token = request.json.get("token", None)
    password = request.json.get("password", None)

    if not password or not token:
        abort(400)

    db = Database(config)
    register = db.getOneByParam("SELECT `id`, `phone`, `token` FROM `user_register` WHERE `token` = %s", token)

    if not register or register.get("token") != token:
        abort(403)

    phone = register.get("phone")
    user_profile = db.getOneByParam("SELECT `user_id` FROM `user_profile` WHERE `phone` = %s", phone)

    if user_profile and user_profile.get("user_id"):
        user = db.getOneByParam("SELECT `id` FROM `user` WHERE `id` = %s", user_profile.get("user_id"))

        hash = encryptPassword(password)
        if user and user.get("id"):
            db.executeByParams("UPDATE `user` SET `password` = %s, `active` = 1 WHERE `id` = %s", [hash, user.get("id")])
    else:
        sql = """INSERT INTO `user`
                    (`username`, `password`, `email`, `created_at`, `last_login`,
                    `login_ip`, `recovery_key`, `recovery_password`, `discount`,
                    `banned`, `service`, `social_id`, `active`, `secret_code`)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        hash = encryptPassword(password)
        email = str(phone) + "_py3@bringo.uz"
        db.executeByParams(sql, [str(phone), hash, email, None, None, None, None, None, None, 0, None, None, 1, None])

        user = db.getOneByParam("SELECT `id` FROM `user` WHERE `username` = %s", phone)
        if user and user.get("id"):
            sql = """INSERT INTO `user_profile`
                        (`user_id`, `full_name`, `phone`, `delivery_address`, `new_phone`)
                        VALUES (%s, %s, %s, %s, %s)"""

            db.executeByParams(sql, [user.get("id"), str(phone), phone, None, None])

    # finally check if user was successfully registered
    user_profile = db.getOneByParam("SELECT `user_id`, `phone` FROM `user_profile` WHERE `phone` = %s", phone)
    if user_profile and user_profile.get("user_id"):
        user = db.getOneByParam("SELECT `id`, `username` FROM `user` WHERE `id` = %s", user_profile.get("user_id"))

    phone = None
    if user_profile and user_profile.get("phone") is not None:
        phone = user_profile.get("phone")

    user_id = None
    if user and user.get("id") is not None:
        user_id = user.get("id")

    if user_id is not None and phone is not None:
        db.executeByParams("DELETE FROM `user_register` WHERE `token` = %s", [token])

    return get_response({
        "phone": phone,
        "user_id": user_id,
        "password": password,
        "username": user.get("username", None)
    }, True)


@app.route(config.url_v1 + '/user/exists', methods=['POST'])
@auth.login_required
def userExists():
    if not request.json:
        abort(400)

    user_id = request.json.get("user_id", None)
    intro_token = request.json.get("intro_token", None)

    if not user_id or not intro_token:
        abort(400)

    if intro_token is None or intro_token != config.intro_token:
        abort(400)

    db = Database(config)
    sql = "SELECT u.`id`, up.`phone`, u.`username` FROM `user` u INNER JOIN `user_profile` up ON up.`user_id` = u.`id`  WHERE u.`id` = %s"
    user = db.getOneByParam(sql, user_id)

    user_id = user.get("id", None)
    phone = user.get("phone", None)
    username = user.get("username", None)
    if user is None or user_id is None or phone is None:
        return get_response("Пользователь не существует", False)

    return get_response({
        "phone": phone,
        "user_id": user_id,
        "username": username
    }, True)


@app.route(config.url_v1 + '/get/manufacturer', methods=['POST'])
@auth.login_required
def getManufacturer():
    if not request.json:
        abort(400)

    man_id = request.json.get("man_id", None)
    lat = request.json.get("lat", None)
    lng = request.json.get("lng", None)

    if not man_id or not lat or not lng:
        abort(400)

    db = Database(config)
    sql = """SELECT
            	smt.`name`,
            	smt.`description`,
                sm.`is_new`,
                sm.`work_start`,
                sm.`work_finish`,
                sm.`status`,
                smi.name AS 'image'
              FROM `StoreManufacturer` sm
              	INNER JOIN `StoreManufacturerTranslate` smt
                	ON smt.`object_id` = sm.`id` AND smt.`language_id` = 1
                LEFT JOIN StoreManufacturerImage smi
                	ON smi.manufacturer_id = sm.id AND smi.is_main = 1
              WHERE sm.`id` = %s"""
    manufacturer = db.getOneByParam(sql, man_id)
    if not manufacturer:
        abort(400)

    if manufacturer is not None and manufacturer.get("status") != 1:
        return get_response("Производитель сейчас не активен", False)

    result = {
        "name": manufacturer.get("name"),
        "description": manufacturer.get("description"),
        "is_new": True if manufacturer.get("is_new") == 1 else False,
        "start_work": str(manufacturer.get("work_start")),
        "finish_work": str(manufacturer.get("work_finish")),
        "image": manufacturer.get("image")
    }

    result["delivery_price"] = getDeliveryPrice(man_id, lat, lng)

    new_image = None
    if result.get("image") is not None:
        new_image = config.manufacturer_path + result.get("image")
        url = config.url_bringo + config.b_manufacturer_path + result.get("image")
        if (is_downloadable(url) and not is_file_exists(new_image)):
            downloand_image(url, new_image)
        elif not is_file_exists(new_image):
            new_image = None

    if new_image is None:
        new_image = config.no_manufacturer

    result["image"] = new_image

    return get_response(result, True)


@app.route(config.url_v1 + '/get/categories', methods=['POST'])
@auth.login_required
def getCategories():
    if not request.json:
        abort(400)

    man_id = request.json.get("man_id", None)

    if man_id is None:
        abort(400)

    db = Database(config)
    sql = "SELECT `id`, `status` FROM StoreManufacturer WHERE id = %s"
    manufacturer = db.getOneByParam(sql, man_id)
    if not manufacturer:
        abort(400)

    if manufacturer is not None and manufacturer.get("status") != 1:
        return get_response("Производитель сейчас не активен", False)

    sql = """SELECT
                  sc.`id`,
                  sct.`name`
                FROM `StoreCategory` sc
                INNER JOIN `StoreCategoryTranslate` sct
                    ON sct.`object_id` = sc.`id` AND sct.`language_id` = 1
                WHERE sc.`parent` IN (
                    SELECT smcr.`category_id`
                        FROM `StoreManufacturerCategoryRef` smcr
                        WHERE smcr.`manufacturer_id` = %s)
                    AND sc.level = 4"""
    categories = db.getAllWithParams(sql, [man_id])

    return get_response(categories, True)


@app.route(config.url_v1 + '/get/products', methods=['POST'])
@auth.login_required
def getProducts():
    if not request.json:
        abort(400)

    man_id = request.json.get("man_id", None)
    cat_id = request.json.get("cat_id", None)

    if not man_id or not cat_id:
        abort(400)

    db = Database(config)

    sql = "SELECT `id`, `status` FROM StoreManufacturer WHERE id = %s"
    manufacturer = db.getOneByParam(sql, man_id)
    if not manufacturer:
        abort(400)

    sql = "SELECT `id` FROM `StoreCategory` WHERE `id` = %s AND `level` = 4"
    category = db.getOneByParam(sql, cat_id)
    if not category:
        abort(400)

    if manufacturer is not None and manufacturer.get("status") != 1:
        return get_response("Производитель сейчас не активен", False)

    # p.position
    sql = """SELECT
            	sppr.product_id AS 'id',
                sp.price,
                pt.name,
                (SELECT spt.ingredients FROM StoreProductTranslate spt WHERE spt.object_id = sp.id and spt.language_id = 1) AS 'ingredients',
                sppr.is_default,
                (SELECT spi.name FROM StoreProductImage spi WHERE spi.is_main = 1 AND spi.product_id = sp.id) AS 'image'
        	FROM StoreProductCategoryRef spcr
            	INNER JOIN StoreProduct sp
                	ON sp.id = spcr.product
                INNER JOIN StoreProductProductRef sppr
                	ON sppr.store_product_id = spcr.product
                INNER JOIN ProductTranslate pt
                	ON pt.object_id = sppr.product_id AND pt.language_id = 1
                INNER JOIN Products p
                	ON p.id = sppr.product_id
            WHERE spcr.category = %s
            	AND sp.manufacturer_id = %s
                AND sp.is_active = 1
            GROUP BY sppr.product_id
            ORDER BY sppr.is_default DESC"""

    products = db.getAllWithParams(sql, [cat_id, man_id])

    for product in products:
        new_image = None
        if product["image"] is not None:
            new_image = config.product_path + product["image"]
            url = config.url_bringo + config.product_path + product["image"]
            if (is_downloadable(url) and not is_file_exists(new_image)):
                downloand_image(url, new_image)
            elif not is_file_exists(new_image):
                new_image = None

        if new_image is None:
            new_image = config.no_product

        product["image"] = new_image

    return get_response(products, True)


@app.route(config.url_v1 + '/get/products-all', methods=['POST'])
@auth.login_required
def getProductsAll():
    if not request.json:
        abort(400)

    man_id = request.json.get("man_id", None)
    # cat_id = request.json.get("cat_id", None)

    if not man_id:
        abort(400)

    db = Database(config)

    sql = "SELECT `id`, `status` FROM StoreManufacturer WHERE id = %s"
    manufacturer = db.getOneByParam(sql, man_id)
    if not manufacturer:
        abort(400)

    # sql = "SELECT `id` FROM `StoreCategory` WHERE `id` = %s AND `level` = 4"
    # category = db.getOneByParam(sql, cat_id)
    #if not category:
        #abort(400)

    if manufacturer is not None and manufacturer.get("status") != 1:
        return get_response("Производитель сейчас не активен", False)

    # sql = """SELECT
    #               sc.`id`,
    #               sct.`name`
    #             FROM `StoreCategory` sc
    #             INNER JOIN `StoreCategoryTranslate` sct
    #                 ON sct.`object_id` = sc.`id` AND sct.`language_id` = 1
    #             WHERE sc.`parent` IN (
    #                 SELECT smcr.`category_id`
    #                     FROM `StoreManufacturerCategoryRef` smcr
    #                     WHERE smcr.`manufacturer_id` = %s)
    #                 AND sc.level = 4"""
    # p.position
    sql = """SELECT
                sppr.product_id AS 'id',
                sp.price,
                pt.name,
                (SELECT spt.ingredients FROM StoreProductTranslate spt WHERE spt.object_id = sp.id and spt.language_id = 1) AS 'ingredients',
                sppr.is_default,
                (SELECT spi.name FROM StoreProductImage spi WHERE spi.is_main = 1 AND spi.product_id = sp.id) AS 'image',
                (SELECT sct.`name` FROM `StoreCategoryTranslate` sct  WHERE sct.object_id = spcr.category AND sct.`language_id` = 1 ) AS 'catName'
            FROM StoreProductCategoryRef spcr
                INNER JOIN StoreProduct sp
                    ON sp.id = spcr.product
                INNER JOIN StoreProductProductRef sppr
                    ON sppr.store_product_id = spcr.product
                INNER JOIN ProductTranslate pt
                    ON pt.object_id = sppr.product_id AND pt.language_id = 1
                INNER JOIN Products p
                    ON p.id = sppr.product_id
            WHERE sp.manufacturer_id = %s
                AND sp.is_active = 1
            GROUP BY sppr.product_id
            ORDER BY sppr.is_default DESC"""

    products = db.getAllWithParams(sql, [man_id])

    for product in products:
        new_image = None
        if product["image"] is not None:
            new_image = config.product_path + product["image"]
            url = config.url_bringo + config.product_path + product["image"]
            if (is_downloadable(url) and not is_file_exists(new_image)):
                downloand_image(url, new_image)
            elif not is_file_exists(new_image):
                new_image = None

        if new_image is None:
            new_image = config.no_product

        product["image"] = new_image

    return get_response(products, True)
@app.route(config.url_v1 + '/get/product', methods=['POST'])
@auth.login_required
def getProduct():
    if not request.json:
        abort(400)

    man_id = request.json.get("man_id", None)
    product_id = request.json.get("product_id", None)

    if not man_id or not product_id:
        abort(400)

    db = Database(config)

    sql = "SELECT `id`, `status` FROM StoreManufacturer WHERE id = %s"
    manufacturer = db.getOneByParam(sql, man_id)
    if not manufacturer:
        abort(400)

    if manufacturer is not None and manufacturer.get("status") != 1:
        return get_response("Производитель сейчас не активен", False)

    sql = """SELECT
            	p.id,
                pt.name,
                sppr.is_default,
                (SELECT spt.ingredients FROM StoreProductTranslate spt WHERE spt.object_id = sppr.store_product_id AND spt.language_id = 1) AS 'ingredients',
                (SELECT spi.name FROM StoreProductImage spi WHERE spi.is_main = 1 AND spi.product_id = sppr.product_id) AS 'image'
        	FROM Products p
            INNER JOIN ProductTranslate pt ON pt.object_id = p.id AND pt.language_id = 1
            INNER JOIN StoreProductProductRef sppr
            	ON sppr.product_id = p.id
          WHERE p.id = %s
          GROUP BY sppr.product_id
          ORDER BY sppr.is_default DESC"""
    product = db.getOneByParam(sql, product_id)

    sql = """SELECT
        	  sppr.option_id AS 'id',
              ot.name,
              sp.price,
              sp.id AS 'product_id'
        	FROM StoreProductProductRef sppr
            INNER JOIN StoreProduct sp
            	ON sp.id = sppr.store_product_id
            INNER JOIN OptionTranslate ot
            	ON ot.object_id = sppr.option_id AND ot.language_id = 1
            WHERE sppr.product_id = %s"""
    product["options"] = db.getAllWithParams(sql, [product_id])

    new_image = None
    if product["image"] is not None:
        new_image = config.product_path + product["image"]
        url = config.url_bringo + config.product_path + product["image"]
        if (is_downloadable(url) and not is_file_exists(new_image)):
            downloand_image(url, new_image)
        elif not is_file_exists(new_image):
            new_image = None

    if new_image is None:
        new_image = config.no_product

    product["image"] = new_image

    return get_response(product, True)


@app.route(config.url_v1 + '/get/payments', methods=['POST'])
@auth.login_required
def getPayments():
    if not request.json:
        abort(400)

    man_id = request.json.get("man_id", None)

    if man_id is None:
        abort(400)

    db = Database(config)
    sql = "SELECT `id`, `status` FROM StoreManufacturer WHERE id = %s"
    manufacturer = db.getOneByParam(sql, man_id)
    if not manufacturer:
        abort(400)

    if manufacturer is not None and manufacturer.get("status") != 1:
        return get_response("Производитель сейчас не активен", False)

    sql = """SELECT
            	  smp.payment_id,
            	  spmt.name
            	FROM StoreManufacturerPayment smp
                INNER JOIN StorePaymentMethodTranslate spmt
                	ON spmt.language_id = 1 AND spmt.object_id = smp.payment_id
                WHERE smp.manufacturer_id = %s"""
    payments = db.getAllWithParams(sql, [man_id])

    return get_response(payments, True)


@app.route(config.url_v1 + '/make/order', methods=['POST'])
@auth.login_required
def makeOrder():
    if not request.json:
        abort(400)

    # # required fields
    # payment_id = request.json.get("payment_id", None)
    # delivery_id = request.json.get("delivery_id", None)
    # manufacturer_id = request.json.get("manufacturer_id", None)
    #
    # if not payment_id or not delivery_id or manufacturer_id is None:
    #     abort(400)
    #
    # # require fields if pick_up is true
    # lat = request.json.get("lat", None)
    # lng = request.json.get("lng", None)
    # pick_up = request.json.get("pick_up", False)
    #
    # if not bool(pick_up) and (not lat or not lng):
    #     abort(400)
    # elif pick_up:
    #     lat = None
    #     lng = None
    #
    # # times
    # date = request.json.get("date", None)
    # time = request.json.get("time", None)
    #
    # # required fields if order is not urgunt
    # if delivery_id != 16 and (not date or not time):
    #     abort(400)
    #
    # # required products
    # products = request.json.get("products", None)
    #
    # if products is None or not isinstance(products, list):
    #     abort(400)
    #
    # # address
    # address = request.json.get("address", None)
    # unit = request.json.get("unit", None)
    # apartment = request.json.get("apartment", None)
    # floor = request.json.get("floor", None)
    # home = request.json.get("home", None)
    #
    #
    # # create json params
    # params = {
    #     "payment_id": payment_id,
    #     "manufacturer_id": manufacturer_id,
    #     "delivery_type": 1 if date and time else 0,
    #     # "lat": lat,
    #     # "lng": lng,
    #     "products": products
    # }
    #
    # if date is not None and time is not None:
    #     params["delivery_date"] = date
    #     params["delivery_time"] = time
    #
    # if address is not None:
    #     params["address"] = address
    #
    # if unit is not None:
    #     params["user_unit"] = unit
    #
    # if apartment is not None:
    #     params["user_apartment"] = apartment
    #
    # if floor is not None:
    #     params["user_floor"] = floor
    #
    # if home is not None:
    #     params["user_home"] = home
    #
    # if lat is not None:
    #     params["lat"] = lat
    #
    # if lng is not None:
    #     params["lng"] = lng

    # create auth params
    username = request.authorization.username
    password = request.authorization.password

    # create order
    response = createOrder(request.json, (username, password))
    if response is None:
        return get_response("Ошибка сервера", False)

    return response
    # return get_response(json.loads(response), True)



if __name__ == '__main__':
    app.debug = True
#    app.run(host = environ.get("HOST"), port=environ.get("PORT"))
    app.run(host = environ.get("HOST"), port=8000)
