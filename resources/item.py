import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import ItemSchema, ItemUpdateSchema
from sqlalchemy.exc import SQLAlchemyError

from db import items
from db import db
from models import ItemModel

blp = Blueprint("Items", __name__, description="Operations on items")


@blp.route("/item/<string:item_id>")
class Item(MethodView):
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item

    def delete(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted."}
        #raise NotImplementedError("Deleting an item is not implemented.")

    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get_or_404(item_id)
        raise NotImplementedError("Updating an item is not implemented.")


@blp.route("/item")
class ItemList(MethodView):
    def get(self):
        return {"items": list(items.values())}

    def post(self):
        item_data = request.get_json()
        if (
            "price" not in item_data
            or "store_id" not in item_data
            or "name" not in item_data
        ):
            abort(
                400,
                message="Bad request. Ensure 'price', 'store_id', and 'name' are included in the JSON payload.",
            )
        for item in items.values():
            if (
                item_data["name"] == item["name"]
                and item_data["store_id"] == item["store_id"]
            ):
                abort(400, message=f"Item already exists.")

        item_id = uuid.uuid4().hex
        item = {**item_data, "id": item_id}
        items[item_id] = item

        return item

@blp.arguments(ItemSchema)
@blp.response(201, ItemSchema)
def post(self, item_data):
    item = ItemModel(**item_data)

    try:
        db.session.add(item)
        db.session.commit()
    except SQLAlchemyError:
        abort(500, message="An error occurred while inserting the item.")

    return item

@blp.arguments(ItemUpdateSchema)
@blp.response(200, ItemSchema)
def put(self, item_data, item_id):
    item = ItemModel.query.get(item_id)
    if item:
        item.price = item_data["price"]
        item.name = item_data["name"]
    else:
        item = ItemModel(id=item_id, **item_data)

    db.session.add(item)
    db.session.commit()

    return item

@blp.response(200, ItemSchema)
def get(self, item_id):
    try:
        return items[item_id]
    except KeyError:
        abort(404, message="Item not found.")

@blp.response(200, ItemSchema(many=True))
def get(self):
    return ItemModel.query.all()

