import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ---- GOOGLE SHEETS CONNECTION ----
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# ---- MAIN DASHBOARD ----
st.title("Gold Star Games Dashboard")

# Define tabs
tab1, tab2, tab3, tab4 = st.tabs(["Games Stock", "Day-to-Day Sales", "Enquiry","Admin"])

# ---- TAB 1: Games Stock ----
with tab1:
    sheet = client.open("Gold Star Games").worksheet("Games Stock")
    data = pd.DataFrame(sheet.get_all_records())

    st.header("Games Stock Management")

    # ---- LOW STOCK ALERT ----
    low_stock_threshold = 1  # Customize this threshold
    low_stock_items = data[data['QTY IN HAND'] <= low_stock_threshold]

    if not low_stock_items.empty:
        with st.expander("low stocks"):
            st.warning(f"Low stock alert! These items are running low:\n{', '.join(low_stock_items['Product'])}")

    # ---- SEARCH & PRODUCT SELECTION ----
    search_query = st.text_input("Search Product")
    if search_query:
        filtered_products = [p for p in data['Product'].tolist() if search_query.lower() in p.lower()]
    else:
        filtered_products = data['Product'].tolist()

    selected_product = st.selectbox("Select Product", ["-- Select --"] + filtered_products)

    if selected_product != "-- Select --":
        product_row = data[data['Product'] == selected_product].iloc[0]
        st.write(f"**Price:** {product_row['Price']}")
        st.write(f"**Quantity in Hand:** {product_row['QTY IN HAND']}")
        st.write(f"**Reorder Needed:** {product_row['REORDER']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sell (Reduce by 1)"):
                current_qty = int(product_row['QTY IN HAND'])
                if current_qty > 0:
                    new_qty = current_qty - 1
                    row_index = data[data['Product'] == selected_product].index[0] + 2
                    sheet.update_cell(row_index, 3, new_qty)
                    st.success(f"Sold 1 unit of {selected_product}. New quantity: {new_qty}")
                else:
                    st.error("Cannot sell, stock is already 0!")
        with col2:
            if st.button("Purchase (+1)"):
                current_qty = int(product_row['QTY IN HAND'])
                new_qty = current_qty + 1
                row_index = data[data['Product'] == selected_product].index[0] + 2
                sheet.update_cell(row_index, 3, new_qty)
                st.success(f"Purchased 1 unit of {selected_product}. New quantity: {new_qty}")

    st.markdown("---")
    st.subheader("Add New Item to Stock")

    with st.form("add_item_form"):
        new_product = st.text_input("Product Name")
        new_price = st.number_input("Price", min_value=0.0, step=0.1)
        new_qty = st.number_input("Quantity in Hand", min_value=0, step=1)
        new_reorder = st.text_input("Reorder Status (Yes/No)")
        submitted = st.form_submit_button("Add Item")

        if submitted:
            if new_product.strip() == "":
                st.error("Product name cannot be empty.")
            else:
                sheet.append_row([new_product, new_price, new_qty, new_reorder])
                st.success(f"New item '{new_product}' added successfully!")

    st.markdown("---")
    with st.expander("View Full Stock Table"):
        st.dataframe(data)

        export_option = st.radio("Export as:", ["None", "Excel", "PDF"])
        if export_option == "Excel":
            data.to_excel("Games_Stock.xlsx", index=False)
            with open("Games_Stock.xlsx", "rb") as file:
                st.download_button("Download Excel", file, file_name="Games_Stock.xlsx")
        elif export_option == "PDF":
            from reportlab.platypus import SimpleDocTemplate, Table
            from reportlab.lib.pagesizes import A4
            doc = SimpleDocTemplate("Games_Stock.pdf", pagesize=A4)
            table_data = [data.columns.tolist()] + data.values.tolist()
            table = Table(table_data)
            doc.build([table])
            with open("Games_Stock.pdf", "rb") as file:
                st.download_button("Download PDF", file, file_name="Games_Stock.pdf")


# ---- TAB 2: Day-to-Day Sales (to be implemented) ----
with tab2:
    st.subheader("Day-to-Day Sales, Purchases & Service")
    st.info("This tab manages daily sales, purchases, and services.")

    # Open the dedicated sheet
    sheet_sales = client.open("Gold Star Games").worksheet("new day to day")
    sales_data = pd.DataFrame(sheet_sales.get_all_records())

    # --- FILTERS ---
    if not sales_data.empty:
        st.markdown("### Filter Transactions")
        with st.expander("Filters"):
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_date = st.text_input("Date (YYYY-MM-DD)")
                filter_sales = st.text_input("Sales Item")
                filter_purchased = st.text_input("Purchased Item")
            with col2:
                filter_service = st.text_input("Service Item")
                filter_name = st.text_input("Customer Name")
                filter_phone = st.text_input("Phone Number")
            with col3:
                filter_amount = st.text_input("Amount")
                filter_payment = st.text_input("Payment Mode")

        filtered_data = sales_data.copy()

        if filter_date:
            filtered_data = filtered_data[filtered_data['DATE'].astype(str).str.contains(filter_date, case=False, na=False)]
        if filter_sales:
            filtered_data = filtered_data[filtered_data['SALES'].str.contains(filter_sales, case=False, na=False)]
        if filter_purchased:
            filtered_data = filtered_data[filtered_data['PURCHASED'].str.contains(filter_purchased, case=False, na=False)]
        if filter_service:
            filtered_data = filtered_data[filtered_data['SERVICE'].str.contains(filter_service, case=False, na=False)]
        if filter_name:
            filtered_data = filtered_data[filtered_data['NAME'].str.contains(filter_name, case=False, na=False)]
        if filter_phone:
            filtered_data = filtered_data[filtered_data['PHONE'].astype(str).str.contains(filter_phone, case=False, na=False)]
        if filter_amount:
            filtered_data = filtered_data[filtered_data['AMOUNT'].astype(str).str.contains(filter_amount, case=False, na=False)]
        if filter_payment:
            filtered_data = filtered_data[filtered_data['PAYMENT MODE'].astype(str).str.contains(filter_payment, case=False, na=False)]

        st.dataframe(filtered_data)

        with st.expander("Show Full Sheet (Read-Only)"):
            st.dataframe(sales_data)

    # --- ADD NEW TRANSACTION ---
    st.markdown("---")
    st.markdown("### Add New Transaction")
    with st.form("add_sales_form"):
        date = st.date_input("Date")
        sales_item = st.text_area("Sales Item(s)")
        purchased_item = st.text_area("Purchased Item(s)")
        service_item = st.text_area("Service Item(s)")
        customer_name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        amount = st.text_input("Amount")
        payment_mode = st.text_input("Payment Mode")
        notes = st.text_area("Additional Notes")
        submitted = st.form_submit_button("Add Entry")

        if submitted:
            row_data = [
                str(date),
                sales_item,
                purchased_item,
                service_item,
                customer_name,
                phone,
                amount,
                payment_mode,
                notes
            ]
            sheet_sales.append_row(row_data)
            st.success("Transaction added successfully!")


# ---- TAB 3: Enquiry ----
# ---- TAB 3: Enquiry ----
with tab3:
    st.subheader("Customer Enquiry")
    st.info("This tab manages customer inquiries.")

    # Open the enquiry sheet
    sheet_enquiry = client.open("Gold Star Games").worksheet("Enquiry")
    enquiry_data = pd.DataFrame(sheet_enquiry.get_all_records())

    # --- FILTERS ---
    if not enquiry_data.empty:
        st.markdown("### Filter Enquiries")
        with st.expander("Filters"):
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_date = st.text_input("Date (YYYY-MM-DD)", key="filter_date")
                filter_name = st.text_input("Customer Name", key="filter_name")
            with col2:
                filter_phone = st.text_input("Phone Number", key="filter_phone")
                filter_product = st.text_input("Product Detail", key="filter_product")
            with col3:
                filter_content = st.text_input("Content", key="filter_content")

        filtered_enquiries = enquiry_data.copy()

        if filter_date:
            filtered_enquiries = filtered_enquiries[
                filtered_enquiries['DATE'].astype(str).str.contains(filter_date, case=False, na=False)
            ]
        if filter_name:
            filtered_enquiries = filtered_enquiries[
                filtered_enquiries['CUSTOMERS NAME'].str.contains(filter_name, case=False, na=False)
            ]
        if filter_phone:
            filtered_enquiries = filtered_enquiries[
                filtered_enquiries['PH NO'].astype(str).str.contains(filter_phone, case=False, na=False)
            ]
        if filter_product:
            filtered_enquiries = filtered_enquiries[
                filtered_enquiries['PRODUCT DETAIL'].str.contains(filter_product, case=False, na=False)
            ]
        if filter_content:
            filtered_enquiries = filtered_enquiries[
                filtered_enquiries['CONTENT'].str.contains(filter_content, case=False, na=False)
            ]

        st.dataframe(filtered_enquiries)

        with st.expander("Show Full Enquiry Sheet (Read-Only)"):
            st.dataframe(enquiry_data)

    # --- ADD NEW ENQUIRY ---
    st.markdown("---")
    st.markdown("### Add New Enquiry")
    with st.form("add_enquiry_form"):
        date = st.date_input("Date", key="add_date")
        customer_name = st.text_input("Customer Name", key="add_name")
        phone = st.text_input("Phone Number", key="add_phone")
        product_detail = st.text_input("Product Detail", key="add_product")
        content = st.text_area("Enquiry Content", key="add_content")
        submitted = st.form_submit_button("Add Enquiry")

        if submitted:
            row_data = [
                str(date),
                customer_name,
                phone,
                product_detail,
                content
            ]
            sheet_enquiry.append_row(row_data)
            st.success(f"Enquiry from {customer_name} added successfully!")

import plotly.express as px

# ---- TAB 4: Admin Analytics ----

with tab4:
    st.subheader("Admin Analytics Dashboard")
    st.info("Interactive insights from your stock, sales, and enquiries.")

    # ---- STOCK ANALYTICS ----
    st.markdown("### Stock Analytics")
    sheet = client.open("Gold Star Games").worksheet("Games Stock")
    stock_data = pd.DataFrame(sheet.get_all_records())
    
    total_products = len(stock_data)
    total_qty = stock_data['QTY IN HAND'].sum()
    low_stock_items = stock_data[stock_data['QTY IN HAND'] <= 1]
    total_stock_value = (stock_data['Price'] * stock_data['QTY IN HAND']).sum()

    st.metric("Total Products", total_products)
    st.metric("Total Quantity in Stock", total_qty)
    st.metric("Low Stock Items", len(low_stock_items))
    st.metric("Total Stock Value", f"₹{total_stock_value}")

    # Interactive bar chart of stock quantities
    fig_stock = px.bar(stock_data, x='Product', y='QTY IN HAND', 
                       color='QTY IN HAND', text='QTY IN HAND',
                       title="Stock Quantity per Product")
    st.plotly_chart(fig_stock, use_container_width=True)

    # ---- SALES ANALYTICS ----
    st.markdown("### Sales Analytics")
    sheet_sales = client.open("Gold Star Games").worksheet("new day to day")
    sales_data = pd.DataFrame(sheet_sales.get_all_records())

    if not sales_data.empty:
        sales_data['AMOUNT_NUM'] = pd.to_numeric(sales_data['Amount'], errors='coerce').fillna(0)
        total_sales_amount = sales_data['AMOUNT_NUM'].sum()
        total_customers = sales_data['NAME'].nunique()
        
        st.metric("Total Sales Amount", f"₹{total_sales_amount}")
        st.metric("Total Customers", total_customers)

        # Top 5 customers by sales
        top_customers = sales_data.groupby('NAME')['AMOUNT_NUM'].sum().sort_values(ascending=False).head(5)
        fig_customers = px.bar(top_customers, x=top_customers.index, y=top_customers.values,
                               labels={'x': 'Customer', 'y': 'Total Amount'},
                               title="Top 5 Customers by Sales")
        st.plotly_chart(fig_customers, use_container_width=True)

        # Top 10 sold products
        top_products = sales_data['SALES'].value_counts().head(10)
        fig_products = px.bar(top_products, x=top_products.index, y=top_products.values,
                              labels={'x': 'Product', 'y': 'Sold Quantity'},
                              title="Top 10 Sold Products")
        st.plotly_chart(fig_products, use_container_width=True)

    # ---- ENQUIRY ANALYTICS ----
    st.markdown("### Enquiry Analytics")
    sheet_enquiry = client.open("Gold Star Games").worksheet("Enquiry")
    enquiry_data = pd.DataFrame(sheet_enquiry.get_all_records())

    if not enquiry_data.empty:
        total_enquiries = len(enquiry_data)
        top_enquiry_products = enquiry_data['PRODUCT DETAIL'].value_counts().head(5)
        top_customers_enquiries = enquiry_data['CUSTOMERS NAME'].value_counts().head(5)

        st.metric("Total Enquiries", total_enquiries)

        fig_enquiry_products = px.bar(top_enquiry_products, x=top_enquiry_products.index, y=top_enquiry_products.values,
                                      labels={'x': 'Product', 'y': 'Enquiry Count'},
                                      title="Top 5 Products by Enquiries")
        st.plotly_chart(fig_enquiry_products, use_container_width=True)

        fig_enquiry_customers = px.bar(top_customers_enquiries, x=top_customers_enquiries.index, y=top_customers_enquiries.values,
                                       labels={'x': 'Customer', 'y': 'Enquiry Count'},
                                       title="Top 5 Customers by Number of Enquiries")
        st.plotly_chart(fig_enquiry_customers, use_container_width=True)
