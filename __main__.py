import datetime
import requests
from bson import ObjectId
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/citrin_caller"
mongo = PyMongo(app)

currentMail = "Citrin@citrin.su"
currentPassword = "PlayBoy69"


@app.route('/hooks/', methods=['POST'])
def hooks():
    print(request.form)
    return jsonify({'Status': 'Ok'})


@app.route('/workers/')
def workers():
    workers = mongo.db.workers.find({})
    datastr = []
    for document in workers:
        datastr.append({'name': document['name'],
                        'username': document['username'],
                        'password': document['password'],
                        'id': str(document['_id'])})
    print(datastr)
    return jsonify(datastr)


@app.route('/setworkers/', methods=['POST'])
def addworkers():
    if request.form.get("name") == "" \
            or request.form.get("name") is None \
            or request.form.get("username") == "" \
            or request.form.get("username") is None \
            or request.form.get("password") == "" \
            or request.form.get("password") is None:
        return jsonify({"Status": "Err"})

    workers = mongo.db.workers.find({})
    datastr = []
    for document in workers:
        if document['username'] == request.form.get('username'):
            return jsonify({"Status": "Exist"})

    data = {
        "name": request.form.get('name'),
        "username": request.form.get('username'),
        "password": request.form.get('password')
    }

    collection = mongo.db.workers.insert_one(data)
    print("/setworkers Status: added")
    return jsonify({"Status": "Added"})


@app.route('/setworker/', methods=['POST'])
def setworker():
    id = request.form.get("id")
    print(id)
    collection = mongo.db.workers.find_one({'_id': ObjectId(id)})

    if collection['username'] is not None \
            and collection['username'] != "" \
            and collection['password'] is not None \
            and collection['username'] != "":
        currentMail = collection['username']
        currentPassword = collection['password']
        print(currentMail)
        return jsonify({"Status": "Ok"})

    else:
        return jsonify({"Status": "Err"})


@app.route('/blacklist/', methods=['POST', 'GET', 'DELETE'])
def blacklist():
    if request.method == 'POST':
        data = {
            "name": request.form.get('phone')
        }
        collection = mongo.db.blacklist.insert_one(data)
        return jsonify({"Status": "Ok"})

    elif request.method == 'GET':
        blacklist = mongo.db.blacklist.find({})
        datastr = []
        for document in blacklist:
            datastr.append({'phone': document['name']})
        return jsonify(datastr)

    elif request.method == 'DELETE':
        blacklist = mongo.db.blacklist.remove({'phone': request.form.get('phone')})
        return jsonify({"Status": "Deleted"})


@app.route('/setlead/', methods=['POST'])
def setlead():
    if request.method == 'POST':
        phone = request.form.get('phone')
        date = datetime.datetime.utcnow()
        blacklist = mongo.db.blacklist.find_one({'name': phone})

        if phone is None or phone == "":
            return jsonify({"Status": "Empty"})

        if blacklist is not None and blacklist['name'] == phone:
            return jsonify({"Status": "blacklist"})
        else:
            dbdata = mongo.db.phones.find_one({'phone': phone})
            if dbdata is None:
                print('fail')
                mongo.db.phones.insert_one({'phone': phone, 'date': date})
                req = requests.post('https://citrin.bitrix24.ru/crm/configs/import/lead.php', data={
                    'LOGIN': currentMail,
                    'PASSWORD': currentPassword,
                    'TITLE': "Авито",
                    'PHONE_MOBILE': phone
                })
                print(req.text)
                return jsonify({"Status": "Ok"})
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
                        'LOGIN': currentMail,
                        'PASSWORD': currentPassword,
                        'TITLE': "Авито",
                        'PHONE_MOBILE': phone
                    })
                    print(req.text)
                    return jsonify({"Status": "Ok"})

                else:
                    return jsonify({"Status": "Err"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='7676')
