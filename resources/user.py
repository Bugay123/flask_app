import logging
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from models import UserModel
from schemas import UserSchema
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
)
from blocklist import BLOCKLIST
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

blp = Blueprint("Users", "users", description="Operations on users")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        try:
            if UserModel.query.filter(UserModel.username == user_data["username"]).first():
                abort(409, message="A user with that username already exists.")

            user = UserModel(
                username=user_data["username"],
                password=pbkdf2_sha256.hash(user_data["password"]),
            )
            db.session.add(user)
            db.session.commit()

            logger.info(f"User {user.username} created successfully.")
            return {"message": "User created successfully."}, 201
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"IntegrityError: {e}")
            abort(409, message="A user with that username already exists.")
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"SQLAlchemyError: {e}")
            abort(500, message="An error occurred while creating the user.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error: {e}")
            abort(500, message="An unexpected error occurred while creating the user.")

@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200

@blp.route("/users")
class UserList(MethodView):
    @blp.response(200, UserSchema(many=True))
    def get(self):
        return UserModel.query.all()

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=str(user.id))
            return {"access_token": access_token}, 200

        abort(401, message="Invalid credentials.")

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200