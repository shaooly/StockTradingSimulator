import yfinance as yahooFinance
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as htm


def get_stock_info(ticker,timecap):
    get_information = yahooFinance.Ticker(ticker)
    df = pd.DataFrame(get_information.history(period=timecap))
    high_fb = df.High.T
    time_list = df.T
    open_list = df['Open']
    open_value = []
    for item in open_list:
        open_value.append(item)

    date_list = []
    for time_item in time_list:
        date_list.append(time_item)

    df = pd.DataFrame(dict(
        x=date_list,
        y=open_value
    ))
    if timecap == "7d":
        fig = px.line(df, x="x", y="y", title=f"Chart for {ticker} over the week")
    if timecap == "1mo":
        fig = px.line(df, x="x", y="y", title=f"Chart for {ticker} over the month")
    if timecap == "12mo":
        fig = px.line(df, x="x", y="y", title=f"Chart for {ticker} over the year")

    fig.update_layout(
        autosize=False,
        width=500,
        height=500,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
        paper_bgcolor="LightSteelBlue",
    )
    my_html = htm.to_html(fig, full_html=True)
    return my_html
