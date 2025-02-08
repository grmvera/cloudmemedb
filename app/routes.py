from flask import Flask, jsonify
from . import app, db
from .models import User

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Cloud MemeDB API!"})