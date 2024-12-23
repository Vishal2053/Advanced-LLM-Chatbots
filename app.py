from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from langchain.llms import Ollama
from simple_bot import run_flow, main

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import argparse
import json
from argparse import RawTextHelpFormatter
import requests
from typing import Optional
import warnings
try:
    from langflow.load import upload_file
except ImportError:
    warnings.warn("Langflow provides a function to help you upload files to the flow. Please install langflow to use it.")
    upload_file = None

# Initialize LangChain's Ollama model
ollama = Ollama(base_url='http://localhost:11434', model="bhakti2.0")

# Database model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration Successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Error: Email already exists.', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Bhakti chatbot route
@app.route('/bhakti', methods=['GET', 'POST'])
@login_required
def bhakti():
    response = None
    if request.method == 'POST':
        user_input = request.form.get('message')  # Safely fetch the message
        if user_input:
            response = ollama(user_input)  # Get response from Ollama model
    return render_template('bhakti.html', response=response)

@app.route('/chatwithvishu', methods=['GET', 'POST'])
@login_required
def chatwithvishu():
    user_response = None
    langflow_response = None
    BASE_API_URL = "https://api.langflow.astra.datastax.com"
    LANGFLOW_ID = "74b379a1-c9a7-47f9-bb3f-f4b511077b91"
    FLOW_ID = "689cbc18-89a5-4a23-bcb2-d0458303e0e9"
    APPLICATION_TOKEN = "AstraCS:xeiCBTNYPKzZBCcpFXGmUFUF:cda78a452debb9518e4a83e26817c0803fe4a80b040860283d9a2bfdbfa09fad"
    ENDPOINT = ""
    TWEAKS = {
    "ChatOutput-jp3xs": {},
    "GroqModel-AI89m": {},
    "ChatInput-N8nuu": {}
    }
    if request.method == 'POST':
        user_input = request.form.get('user_input')  # Safely fetch the message
        if user_input:
            # Generate response using the LangFlow API
            langflow_response = run_flow(
                message=user_input,
                endpoint=FLOW_ID,
                tweaks=TWEAKS,
                application_token=APPLICATION_TOKEN
            )

    return render_template(
        'chatwithvishu.html',
        user_response=user_response,
        langflow_response=langflow_response
    )


@app.route('/chatwithpdf', methods=['GET', 'POST'])
@login_required
def chatwithpdf():
    return render_template('chatwithpdf.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
