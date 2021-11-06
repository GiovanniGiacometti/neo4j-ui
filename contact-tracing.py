from json import dumps
from flask import Flask,Response, request
from neo4j import GraphDatabase, basic_auth
import string
import random

app = Flask(__name__)

url = "bolt://localhost:7687"
username = ""
password = ""

driver = GraphDatabase.driver(url, auth=basic_auth(username, password))

def get_db():
    return driver.session()
    
@app.route("/homepage")
def get_index():
    return app.send_static_file('index.html')

@app.route("/person")
def get_persondetail():
    return app.send_static_file('person.html')

@app.route("/graph")
def get_graph():
    print("graph called")
    db = get_db()
    results = db.read_transaction(lambda tx: list(tx.run("MATCH (a:Person) "
                                                         "RETURN a.name as name, a.surname as surname, "
                                                         "a.address as address, a.age as age, a.taxcode as taxcode"
                                                         )))
    nodes = []
    for record in results:
        nodes.append({"name": record["name"], "surname": record["surname"],
        "address": record["address"],"age": record["age"], "taxcode":record["taxcode"]})
        
    return Response(dumps({"nodes": nodes}),
                    mimetype="application/json")

@app.route("/search")
def get_search():
    try:
        p = request.args.get('person')
        p=p.split(" ")
        while p.count('') > 0: p.remove('')

    except Exception as e:
        print(e)
        return list()
    else:
        db = get_db()

        if len(p) == 1:
            results = db.read_transaction(lambda tx: list(tx.run("MATCH (a:Person) "
                                                             "WHERE a.name =~ $name "
                                                             "RETURN a.name as name, a.surname as surname, "
                                                         "a.address as address, a.age as age, a.taxcode as taxcode"
                                                         , name = p[0])))
        else:
            results = db.read_transaction(lambda tx: list(tx.run("MATCH (a:Person) "
                        "WHERE a.name =~ $name and a.surname =~ $surname "
                        "RETURN a.name as name, a.surname as surname, "
                                                         "a.address as address, a.age as age, a.taxcode as taxcode"
                                                         , name = p[0] , surname = p[1])))
                                                    
        nodes = list()
        for record in results:
            nodes.append({"name": record["name"], "surname": record["surname"],
                "address": record["address"],"age": record["age"], "taxcode":record["taxcode"]})
        
        
        return Response(dumps({"nodes": nodes}),
                    mimetype="application/json")

@app.route("/covid-test")
def get_covid_test():
    print("covid test called")
    try:
        p = request.args.get('taxcode')
    except Exception as e:
        print(e)
        return list()
    print(p)
    db = get_db()
    results = db.read_transaction(lambda tx: list(tx.run(
        '''
        match(n:Person{taxcode: $taxcode})-[r]->(c:CovidTest) return c.id as id, c.type as type, c.date as date,
        c.result as result
        ''', taxcode = p
        )))
    nodes = []
    for record in results:
        nodes.append({"id": record["id"], "date": str(record["date"]),
        "type": record["type"],"result": record["result"]})
        
    return Response(dumps({"nodes": nodes}),
                    mimetype="application/json")

@app.route("/vaccine")
def get_vaccine():
    print("vaccine called")

    try:
        p = request.args.get('taxcode')
    except Exception as e:
        print(e)
    print(p)
    db = get_db()
    results = db.read_transaction(lambda tx: list(tx.run(
        '''
        match(n:Person{taxcode: $taxcode})-[r]->(v:VaccineCertificate) return v.id as id, v.type as type, 
        v.first_dose_date as first_dose_date, v.second_dose_date as second_dose_date
        ''', taxcode = p
        )))
    nodes = []

    for i,record in enumerate(results):
        
        nodes.append({"id": record["id"],
        "type": record["type"],"first_dose_date": str(record["first_dose_date"])})
        try:
            nodes[i]["second_dose_date"] = str(record["second_dose_date"])
        except:
            print("No second dose")
    return Response(dumps({"nodes": nodes}),
                    mimetype="application/json")


@app.route("/create-covid-test")
def create_covid_test():
    try:

        d = {
            "type":request.args.get('type'),
            "date":request.args.get('date'),
            "result":request.args.get('result'),
            "taxcode": request.args.get("taxcode")
        }

        print(d)
    except Exception as e:
        print(e)
    else:
        db = get_db()

        res = db.read_transaction(lambda tx: list(tx.run(
            '''
                match(n:CovidTest) return n.id as id order by n.id DESC limit 1 
            ''', )))
        highest_id = int(res[0]["id"])

        db.write_transaction(lambda tx: list(tx.run(
            '''
                MATCH(n:Person{taxcode:$taxcode}) CREATE (n)-[r:TESTED]->(a:CovidTest {id:$id, type:$type, result:$result, date:$date})
            ''', id=highest_id+1, type = d["type"], result=d["result"], date = d["date"],taxcode = d["taxcode"])))

        
        return {}



@app.route("/create")
def create_node():
    try:

        d = {
            "name":request.args.get('name'),
            "surname":request.args.get('surname'),
            "age":request.args.get('age'),
            "address":request.args.get('address'),
        }

        print(d)
    except Exception as e:
        print(e)
        return list()
    else:
        db = get_db()

        db.write_transaction(lambda tx: list(tx.run(
            '''
                CREATE (a:Person {taxcode:$taxcode, name:$name, surname:$surname, age:$age, address:$address}) 
            ''', taxcode = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(16)),
                    name = d["name"], surname = d["surname"], age = d["age"],address = d["address"])))

        
        return {}

if __name__ == '__main__':
    app.run(debug = True)
