import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Legal Desk Dashboard", layout="wide")

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn


def fetch_orders_data(conn):
    """ fetch orders data from the database """
    query = """SELECT
                    order_date,
                    count(order_id) as number_of_orders,
                    sum(total_amount) as total_amount
                FROM Orders
                group by DATE(order_date)
            """
    df = pd.read_sql_query(query, conn)
    return df

def fetch_product_data(conn):
    """ fetch product data from the database """
    query = """SELECT
                    product_name, 
                    category,
                    price,
                    Orders.order_id,
                    order_date
                FROM Orders
                JOIN Order_Items ON Orders.order_id = Order_Items.order_id
                JOIN Products ON Products.product_id = Order_Items.product_id            
            """
    df = pd.read_sql_query(query, conn)
    return df

def fetch_product_frequency(conn):
    """ fetch product frequency data from the database """
    query = """SELECT
                    product_name,
                    category,
                    count(Orders.order_id) as frequency
                FROM Orders
                JOIN Order_Items ON Orders.order_id = Order_Items.order_id
                JOIN Products ON Products.product_id = Order_Items.product_id
                GROUP BY product_name, category
                ORDER BY frequency DESC
            """
    df = pd.read_sql_query(query, conn)
    return df


def plot_product_data_time(product_data):
    #Group by time data month year 
    product_data['order_date'] = pd.to_datetime(product_data['order_date'])
    product_data['year_month'] = product_data['order_date'].dt.to_period('M')
    
    # Group by time: 
    grouped_time_data = product_data.groupby(['year_month','category'])['price'].sum().reset_index()
    grouped_time_data['year_month'] = grouped_time_data['year_month'].dt.to_timestamp()

    # Create a line chart
    fig_time = px.line(grouped_time_data,
                        x='year_month',
                        y='price',
                        color='category',
                        title="Total Price Over Time by Category",
                        labels={'year_month': 'Year-Month', 'price': 'Total Price'})

    #Moving the legend to bottom and being horizontally
    fig_time.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    ))

    #
    st.plotly_chart(fig_time)

def plot_product_data_bars(product_data):
    #Display the product data in a table
    product_categories = product_data['category'].unique()
    selected_category = st.selectbox("Select a product category", product_categories)
    filtered_data = product_data[product_data['category'] == selected_category]

    # Group by the product name and sum the prices
    grouped_data = filtered_data.groupby('product_name')['price'].sum().reset_index().sort_values(by='price', ascending=False)

    fig = px.bar(grouped_data,
        x='product_name',
        y='price',
        title=f"Product Prices in {selected_category} Category")

    st.plotly_chart(fig)

def plot_product_data_bar(product_data):
    # Group by category and sum the prices
    #grouped_data = product_data.groupby('product_name')['frequency'].sum().reset_index().sort_values(by='frequency', ascending=False)

    fig = px.bar(product_data,
                 x='product_name',
                 y='frequency',
                 color = 'category',
                 title="Total Price by Category")

    # Annotate the bars with the frequency
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    fig.update_layout(yaxis_title='Frequency', xaxis_title='Product Name')
    fig.update_layout(xaxis_tickangle=-45)

    #Set height and width of the chart
    fig.update_layout(height=600, width=800)

    st.plotly_chart(fig, use_container_width=True)

# Set title: 
st.title("Legal Desk Dashboard")
st.write("This is a simple Streamlit app to display product data from an SQLite database.")

# Create connection to the SQLite database
conn = sqlite3.connect('legal_documents_ecommerce.db')

# Fetch product data
product_data = fetch_product_data(conn)

orders_data = fetch_orders_data(conn)

## Task one display number of orders per week and month
st.subheader("Orders per week and month")

orders_data['order_date'] = pd.to_datetime(orders_data['order_date'])
orders_data = orders_data.set_index('order_date')

# Resample the data to get weekly and monthly counts
granularity = st.selectbox("Select granularity", ["Weekly", "Monthly"])
orders_resampled = orders_data.resample(granularity[0]).sum()

# Create a line chart for weekly orders
fig_weekly = px.line(orders_resampled, x=orders_resampled.index, y='number_of_orders', title='Weekly Orders')
st.plotly_chart(fig_weekly)



## Most frequent products
st.subheader("Most Frequent Products")

#Fetch the product frequency data
prod_freq = fetch_product_frequency(conn)

# Display the product frequency
plot_product_data_bar(prod_freq)


# Close the connection
#st.subheader("Product Data")
#st.write("""
#         Here we aim to give the user a better understanding of which categories of data performs.
#         The idea is the user will first be presented with an over time view of the categories and then will be allowed to drill into each category
#         with the boxplot.
#         """)




## Plot the product data over time
#plot_product_data_time(product_data)
#
#plot_product_data_bars(product_data)