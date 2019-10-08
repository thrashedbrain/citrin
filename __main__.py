import datetime
import requests
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/citrin_caller"
mongo = PyMongo(app)


@app.route('/workers')
def workers():
    workers = mongo.db.workers.find({})
    datastr = []
    for document in workers:
        datastr.append({'name': document['name']})

    return jsonify(datastr)


@app.route('/setworkers', methods=['POST'])
def setworkers():
    data = {
        "name": request.form.get('name')
    }
    collection = mongo.db.workers.insert_one(data)
    return jsonify("asd")


@app.route('/blacklist/', methods=['POST', 'GET', 'DELETE'])
def blacklist():
    if request.method == 'POST':
        data = {
            "name": request.form.get('phone')
        }
        collection = mongo.db.blacklist.insert_one(data)
        return jsonify("asd")

    elif request.method == 'GET':
        blacklist = mongo.db.blacklist.find({})
        datastr = []
        for document in blacklist:
            datastr.append({'phone': document['name']})
        return jsonify(datastr)

    elif request.method == 'DELETE':
        blacklist = mongo.db.blacklist.remove({'phone': request.form.get('phone')})
        return jsonify("asd")


@app.route('/setlead/', methods=['POST'])
def setlead():
    if request.method == 'POST':
        phone = request.form.get('phone')
        date = datetime.datetime.utcnow()
        blacklist = mongo.db.blacklist.find_one({'name': phone})

        if blacklist is not None and blacklist['name'] == phone:
            return jsonify("blacklist")
        else:
            dbdata = mongo.db.phones.find_one({'phone': phone})
            if dbdata is None:
                print('fail')
                mongo.db.phones.insert_one({'phone': phone, 'date': date})
                req = requests.post('https://citrin.bitrix24.ru/crm/configs/import/lead.php', data={
                    'LOGIN': "citrin@citrin.su",
                    'PASSWORD': "PlayBoy69",
                    'TITLE': "Авито",
                    'PHONE_MOBILE': phone
                })
                print(req.text)
                return jsonify('asd')
            else:
                delta = date - dbdata['date']
                if delta.total_seconds() // 3600 > 24:
                    mongo.db.phones.update_one({
                        '_id': dbdata['_id']
                    }, {
                        '$set': {
                            'date': date
                        }
                    })
                    req = requests.post('https://citrin.bitrix24.ru/crm/configs/import/lead.php', data={
                        'LOGIN': "citrin@citrin.su",
                        'PASSWORD': "PlayBoy69",
                        'TITLE': "Авито",
                        'PHONE_MOBILE': phone
                    })
                    print(req.text)
                    return jsonify("asd")

                else:
                    return jsonify('err')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='7676')
