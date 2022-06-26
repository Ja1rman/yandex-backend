from flask import Flask, Response, request, jsonify
import db
from schema import items_table, relations_table, Type
import sys
from sqlalchemy import delete, select, insert, update
import json
import traceback
import re


migrate = len(sys.argv) == 2 and sys.argv[1] == "migrate"
if migrate:
    db.migrate()

app = Flask(__name__)


@app.route('/imports', methods=["POST"])
def imports():
    data = json.loads(request.data)
    conn = db.engine.connect()
    trans = conn.begin()
    ids = []
    for item in data["items"]:
        if not re.findall('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', item["id"]):
            return Response('{"code": 400,"message": "Validation Failed"}', 400)
        if item["type"] == "CATEGORY":
            if "price" in item and item["price"] != None:
                return Response('{"code": 400,"message": "Validation Failed"}', 400)
        elif item["type"] == "OFFER":
            if item["price"] == None or type(item["price"]) != int or item["price"] <= 0:
                return Response('{"code": 400,"message": "Validation Failed"}', 400)
        if item["id"] in ids:
            return Response('{"code": 400,"message": "Validation Failed"}', 400)
        ids.append(item["id"])

    try:
        for item in data["items"]:
            if item["type"] == "CATEGORY":
                if len(conn.execute(items_table.select().where(items_table.c.id==item['id'])).fetchall()) == 0:
                    conn.execute(insert(items_table).values(name=item["name"], 
                        type=Type.CATEGORY, 
                        id=item["id"], 
                        update_date=data["updateDate"]))
                else:
                    conn.execute(update(items_table).values(name=item["name"], 
                        type=Type.CATEGORY, 
                        id=item["id"], 
                        update_date=data["updateDate"]))
            elif item["type"] == "OFFER":
                if len(conn.execute(items_table.select().where(items_table.c.id==item['id'])).fetchall()) == 0:
                    conn.execute(insert(items_table).values(name=item["name"], 
                        type=Type.OFFER, 
                        id=item["id"],
                        price=item["price"],
                        update_date=data["updateDate"]))
                else:
                    conn.execute(update(items_table).values(name=item["name"], 
                        type=Type.OFFER, 
                        id=item["id"],
                        price=item["price"],
                        update_date=data["updateDate"]))

                conn.execute(relations_table.delete().where(relations_table.c.child_id==item['id']))
                conn.execute(insert(relations_table).values(parent_id=item["parentId"], child_id=item["id"]))

        trans.commit()
    except:
        print(traceback.format_exc())
        trans.rollback()
        return Response('{"code": 400,"message": "Validation Failed"}', 400)

    #print(str(db.engine.execute(select([items_table])).fetchall()))
    return Response(None, 200)


@app.route('/delete/<id>', methods=["DELETE"])
def delete_by_id(id):
    def delete_recursive(id, to_delete):
        ids = db.engine.execute(relations_table.select().where(relations_table.c.parent_id == id)).fetchall()

        for id_ in ids:
            to_delete.append(id_[1])
            delete_recursive(id_[1], to_delete)

        for id_ in to_delete:
            db.engine.execute(items_table.delete().where(items_table.c.id == id_))
            to_delete.remove(id_)


    if not re.findall('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', id):
        return Response('{"code": 400,"message": "Validation Failed"}', 400)
    
    if len(db.engine.execute(items_table.select().where(items_table.c.id == id)).fetchall()):
        to_delete = [id]
        delete_recursive(id, to_delete)

    return Response(None, 200)


@app.route('/nodes/<id>', methods=["GET"])
def nodes_by_id(id):
    if not re.findall('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',id):
        return Response('{"code": 400, "message" : "Validation Failed"}',400)

    if len(db.engine.execute(items_table.select().where(items_table.c.id == id)).fetchall()):
        root = db.engine.execute(items_table.select().where(items_table.c.id == id)).one()
        res = nodes_rec(root)
        print(res)
        return jsonify(res)
    else:
        return Response('{"code": 404, "message" : "Item not found"}',404)

    # return Response('"code" : 200, "message" : None', 200)

def nodes_rec(root):
    root_node = {
            'id': root[0],
            'price': root[1],
            'name': root[2],
            'type': root[3],
            'date': root[4].strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            'children': None,
        }

    parent = db.engine.execute(relations_table.select().where(relations_table.c.child_id == root[0])).fetchall()
    if len(parent):
        root_node['parentId'] = parent[0][0]
    else:
        root_node['parentId'] = None

    if root_node['type'] == 'OFFER':
        return root_node

    childs = []

    for child_id in db.engine.execute(relations_table.select().where(relations_table.c.parent_id == root[0])).fetchall():
        child = db.engine.execute(items_table.select().where(items_table.c.id == child_id[1])).one()
        childs.append(nodes_rec(child))

    root_node['children'] = childs

    _sum = 0
    for child in childs:
        _sum += child['price']

    root_node['price'] = _sum // max(len(childs), 1)
    return root_node
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)