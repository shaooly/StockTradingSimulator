import jinja2
from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db, garph1 as gr1
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import yfinance as yahooFinance
from yahoo_fin.stock_info import *

auth = Blueprint("auth", __name__)


environment = jinja2.Environment()
environment.filters["ticker"] = yahooFinance.Ticker


@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('auth.home2'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route("/trade_after", methods=['GET', 'POST'])
def trade_stock():
    if request.method == "POST" and not request.form.get("stock_amount"):
        stock_name = request.form["myStock"]
        if stock_name not in tickers_sp500():
            flash('The stock you were looking for does not exist. please try again.', category='error')
        else:
            g1 = gr1.get_stock_info(stock_name, "7d")
            g2 = gr1.get_stock_info(stock_name, "1mo")
            g3 = gr1.get_stock_info(stock_name, "12mo")
            ticker = yahooFinance.Ticker(stock_name)
            return render_template("trade_after.html", user=current_user, stock=stock_name, ticker=ticker) + f"<div id='block_container'>{g1 + g2 + g3}</div>"
    else:
        stock_name = request.form.get("stock_ticker")
        stock_ticker = float(yahooFinance.Ticker(stock_name).info["currentPrice"])
        amount = int(request.form.get("stock_amount"))
        user = User.query.get(current_user.__dict__["id"])
        action = request.form.get("stock_action")
        portfolio = pickle.loads(user.portfolio)
        if action == "buy":
            if user.cash - (stock_ticker * amount) < 0:
                flash('Oops look like you are trying to buy more than you can afford. Try to buy less stocks and try again please', category='error')
            else:
                if stock_name not in portfolio:
                    user.cash -= stock_ticker * amount
                    portfolio[stock_name] = amount
                    user.portfolio = pickle.dumps(portfolio)
                else:
                    user.cash -= stock_ticker * amount
                    portfolio[stock_name] += amount
                    user.portfolio = pickle.dumps(portfolio)
        elif action == "sell":
            if stock_name not in portfolio:
                flash("you don't have the stock bruv", category='error')
            else:
                if portfolio[stock_name] < amount:
                    flash(f"you don't have {amount} shares of {stock_name}. You only have {portfolio[stock_name]}",
                          category='error')
                elif portfolio[stock_name] == amount:
                    user.cash += amount * stock_ticker
                    portfolio.pop(stock_name)
                    user.portfolio = pickle.dumps(portfolio)
                else:
                    user.cash += amount * stock_ticker
                    portfolio[stock_name] -= amount
                    user.portfolio = pickle.dumps(portfolio)
        my_portfolio = pickle.loads(current_user.__dict__['portfolio'])
        my_cash = current_user.__dict__['cash']
        db.session.commit()
        sum = 0
        worth_list = []
        for stock_name, amount in my_portfolio.items():
            worth = yahooFinance.Ticker(stock_name).info["currentPrice"] * amount
            sum += worth
            worth_list.append(f"you have {amount} of stocks invested in {stock_name} which are worth {worth}. Nice!")
        return render_template("portfolio.html", user=current_user, cash=my_cash, worth_list=worth_list, sum=sum)


@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        email_exists = User.query.filter_by(email=email).first()
        username_exists = User.query.filter_by(username=username).first()

        if email_exists:
            flash('Email is already in use.', category='error')
        elif username_exists:
            flash('Username is already in use.', category='error')
        elif password1 != password2:
            flash('Password don\'t match!', category='error')
        elif len(username) < 2:
            flash('Username is too short.', category='error')
        elif len(password1) < 6:
            flash('Password is too short.', category='error')
        elif len(email) < 4:
            flash("Email is invalid.", category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(
                password1, method='sha256'), portfolio=pickle.dumps({}), cash=10000)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('User created!')
            return redirect(url_for('auth.home2'))

    return render_template("signup.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.home2"))


@auth.route("/portfolio")
@login_required
def load_portfolio():
    my_portfolio = pickle.loads(current_user.__dict__['portfolio'])
    my_cash = current_user.__dict__['cash']
    sum = 0
    worth_list = []
    if my_portfolio:
        for stock_name, amount in my_portfolio.items():
            worth = yahooFinance.Ticker(stock_name).info["currentPrice"] * amount
            sum += worth
            worth_list.append(f"you have {amount} of stocks invested in {stock_name} which are worth {worth}. Nice!")
    return render_template("portfolio.html", user=current_user, cash=my_cash, worth_list=worth_list, sum=sum)


@auth.route("/trade", methods=['GET', 'POST'])
@login_required
def trade():
    if request.method == "GET":
        return render_template('trade.html', user=current_user, cash=current_user.__dict__['cash'])

    if request.method == "POST":
        stock_name = request.form["myStock"]
        print(stock_name)
        graph = gr1.get_stock_info(stock_name)
        return render_template("trade_after.html", user=current_user, stock=stock_name) + graph


@auth.route("/", methods=['GET', 'POST'])
def home1():
    return render_template("home.html", user=current_user)


@auth.route("/home", methods=['GET', 'POST'])
def home2():
    return render_template("home.html", user=current_user)
