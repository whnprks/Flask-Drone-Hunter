from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from pytz import timezone


class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lokasi = db.Column(db.String(100))
    ipcam = db.Column(db.String(100))
    wib_timezone = timezone('Asia/Jakarta')
    date = db.Column(db.DateTime(timezone=True), default=func.now(wib_timezone), server_default=func.now(wib_timezone))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(10))
