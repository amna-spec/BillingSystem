import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
# Database connection 
def get_connection():
    return sqlite3.connect("billing_system.db", check_same_thread=False)

# Fetch table data 
def get_table_data(table_name):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# Insert user data 
def insert_user(person_id, name, flat_no, user_type, load_sanctioned, phase):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Users (PersonID, Name, FlatNo, UserType, LoadSanctioned, Phase)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (person_id, name, flat_no, user_type, load_sanctioned, phase))
    conn.commit()
    conn.close()

# Update user data 
def update_user(person_id, name, flat_no, user_type, load_sanctioned, phase):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Users SET Name=?, FlatNo=?, UserType=?, LoadSanctioned=?, Phase=?
        WHERE PersonID=?
    """, (name, flat_no, user_type, load_sanctioned, phase, person_id))
    conn.commit()
    conn.close()

# Delete user data 
def delete_user(person_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Users WHERE PersonID=?", (person_id,))
    conn.commit()
    conn.close()
def generate_pdf(flat_no, person_id, name,billing_month, reading_date, 
                 previous_reading, present_reading, units_consumed, electric_duty, 
                 gst, surcharge, variable_charges, net_amount, payable_amount):

    file_path = f"{flat_no}_ElectricBill_{billing_month}.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "NED UNIVERSITY OF ENGINEERING & TECHNOLOGY")
    c.drawCentredString(width / 2, height - 70, "DIRECTORATE OF WORKS & SERVICES")
    c.drawCentredString(width / 2, height - 90, "ELECTRIC BILL FOR NED STAFF COLONY")

    # User Details
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 120, f"Flat No: {flat_no}")
    c.drawString(250, height - 120, f"Load Sanctioned: 1 kW")
    c.drawString(50, height - 140, f"Pers No: {person_id}")
    c.drawString(250, height - 140, f"Phase: 1")
    c.drawString(50, height - 160, f"Name: {name}")
    c.drawString(50, height - 200, f"Billing Month: {billing_month}")
    c.drawString(250, height - 200, f"Reading Date: {reading_date}")

    # Table Headers
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.blue)
    c.drawString(50, height - 230, "Billing Detail Residential Tariff (July 2024 - Sept 2024)")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(50, height - 250, "Units Details")
    c.drawString(50, height - 270, f"Previous Reading: {previous_reading}")
    c.drawString(50, height - 290, f"Present Reading: {present_reading}")
    c.drawString(50, height - 310, f"Units Consumed: {units_consumed}")
    c.drawString(50, height - 330, "Units Adjusted: 0")
    c.drawString(50, height - 350, f"Billing Units: {units_consumed}")

    # Charges Section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 380, "Charges Details (PKR)")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 400, f"Variable Charges: {variable_charges}")
    c.drawString(50, height - 420, f"Electric Duty: {electric_duty}")
    c.drawString(50, height - 440, "Meter Rent: 0.00")
    c.drawString(50, height - 460, f"GST: {gst}")
    c.drawString(50, height - 480, f"Surcharge: {surcharge}")
    c.drawString(50, height - 500, f"Net Amount: {net_amount}")
    c.drawString(50, height - 520, f"Payable Amount: {payable_amount}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, height - 550, "Note: Meter Reading will be taken on 1st of every month.")
    c.drawString(50, height - 570, "This is a computer-generated bill and does not require a signature.")
    c.drawString(400, height - 590, f"Bill Generated on: {datetime.now().strftime('%d/%m/%Y')}")

    c.save()
    return file_path    
# Get the previous month from the current billing month    
def get_previous_month(billing_month):
    year, month = map(int, billing_month.split('-'))
    previous_month = (datetime(year, month, 1) - timedelta(days=1)).strftime('%Y-%m')
    return previous_month

# Insert billing data 
def insert_bill(person_id, flat_no, month, present_reading, electric_duty, gst, units_adjusted, surcharge):
    conn = get_connection()
    cursor = conn.cursor()

    previous_month = get_previous_month(month)

    cursor.execute("""
        SELECT PresentReading FROM BillingReadings 
        WHERE FlatNo = ? AND BillingMonth = ? 
        ORDER BY BillingMonth DESC LIMIT 1
    """, (flat_no, previous_month))

    previous_reading = cursor.fetchone()
    previous_reading = previous_reading[0] if previous_reading else 0.0  

    # Calculate units consumed
    units_consumed = abs(present_reading - previous_reading) + units_adjusted  

    cursor.execute("""
        SELECT RatePerUnit FROM TariffSlabs 
        WHERE ? BETWEEN MinUnits AND MaxUnits
        LIMIT 1
    """, (units_consumed,))
    rate_per_unit = cursor.fetchone()
    rate_per_unit = rate_per_unit[0] if rate_per_unit else 0

    variable_charges = units_consumed * rate_per_unit
    net_amount = variable_charges + electric_duty + gst
    payable_amount = net_amount + surcharge

    cursor.execute("""
        INSERT INTO BillingReadings (FlatNo, BillingMonth, PreviousReading, PresentReading)
        VALUES (?, ?, ?, ?)
    """, (flat_no, month, previous_reading, present_reading))

    cursor.execute("SELECT LAST_INSERT_ROWID()")
    reading_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO BillingCharges (ReadingID, RatePerUnit, VariableCharges, ElectricDuty, GST, Surcharge, NetAmount, PayableAmount, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (reading_id, rate_per_unit, variable_charges, electric_duty, gst, surcharge, net_amount, payable_amount, 'Due'))
    name=cursor.execute("SELECT Name FROM Users WHERE PersonID=?", (person_id,)).fetchone()[0]
    conn.commit()
    conn.close()
    # Generate PDF after inserting records
    pdf_path = generate_pdf(flat_no, person_id, name,billing_month, 
                                f"01-{billing_month.split('-')[1]}-25", previous_reading, present_reading, 
                                units_consumed, electric_duty, gst, surcharge, variable_charges, 
                                net_amount, payable_amount)
    
    st.success("✅ Billing information added successfully!")
    with open(pdf_path, "rb") as f:
            st.download_button("📥 Download Bill PDF", f, file_name=pdf_path, mime="application/pdf")

def update_bill(person_id, flat_no, month, present_reading, electric_duty, gst, units_adjusted, surcharge):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Fetch old bill data using FlatNo & Month
        cursor.execute("""
            SELECT ReadingID, PreviousReading FROM BillingReadings 
            WHERE FlatNo = ? AND BillingMonth = ?
        """, (flat_no, month))
        data = cursor.fetchone()

        if not data:
            st.error("❌ Bill not found for FlatNo: {} in {}".format(flat_no, month))
            return

        reading_id, previous_reading = data

        # Calculate new units consumed
        units_consumed = abs(present_reading - previous_reading) + units_adjusted

        # Fetch updated rate per unit
        cursor.execute("""
            SELECT RatePerUnit FROM TariffSlabs 
            WHERE ? BETWEEN MinUnits AND MaxUnits
            LIMIT 1
        """, (units_consumed,))
        rate_per_unit = cursor.fetchone()
        rate_per_unit = rate_per_unit[0] if rate_per_unit else 0

        # Recalculate Charges
        variable_charges = units_consumed * rate_per_unit
        net_amount = variable_charges + electric_duty + gst
        payable_amount = net_amount + surcharge

        # Update BillingReadings
        cursor.execute("""
            UPDATE BillingReadings 
            SET PresentReading=?, PreviousReading=? 
            WHERE FlatNo=? AND BillingMonth=?
        """, (present_reading, previous_reading, flat_no, month))

        # Update BillingCharges
        cursor.execute("""
            UPDATE BillingCharges 
            SET RatePerUnit=?, VariableCharges=?, ElectricDuty=?, GST=?, Surcharge=?, NetAmount=?, PayableAmount=?
            WHERE ReadingID=?
        """, (rate_per_unit, variable_charges, electric_duty, gst, surcharge, net_amount, payable_amount, reading_id))

        conn.commit()
        st.success(f"✅ Bill updated successfully for Flat {flat_no} ({month})!")

    except Exception as e:
        conn.rollback()
        st.error(f"❌ Error updating bill: {e}")

    finally:
        conn.close()


# **Delete bill record**
def delete_bill(person_id, flat_no, month):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Find the ReadingID using FlatNo & Month
        cursor.execute("""
            SELECT ReadingID FROM BillingReadings 
            WHERE FlatNo=? AND BillingMonth=?
        """, (flat_no, month))
        bill_data = cursor.fetchone()

        if not bill_data:
            st.error(f"❌ No bill found for Flat {flat_no} in {month}!")
            return

        reading_id = bill_data[0]

        # Fetch the Bill ID from BillingCharges (if exists)
        cursor.execute("SELECT BillID FROM BillingCharges WHERE ReadingID=?", (reading_id,))
        bill_id_data = cursor.fetchone()
        bill_id = bill_id_data[0] if bill_id_data else None  # Check if Bill ID exists

        # Delete from dependent tables first
        cursor.execute("DELETE FROM BillingCharges WHERE ReadingID=?", (bill_id,))

        # Delete from BillingReadings (also removes ReadingID)
        cursor.execute("DELETE FROM BillingReadings WHERE ReadingID=?", (reading_id,))

        conn.commit()
        st.warning(f"⚠️ Bill record for Flat {flat_no} ({month}) deleted successfully!")

    except Exception as e:
        conn.rollback()
        st.error(f"❌ Error deleting bill: {e}")

    finally:
        conn.close()

# Update bill status (Paid/Unpaid/Due)
def update_bill_status(bill_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Billing SET Status=?
        WHERE BillID=?
    """, (status, bill_id))
    conn.commit()
    conn.close()
# Fetch Consumption History for a user/flat
def get_consumption_history(person_id=None, flat_no=None):
    conn = get_connection()
    query = """
        SELECT ch.ConsumptionID, u.Name, f.FlatNo, ch.BillingMonth, ch.UnitsConsumed, ch.RecordedAt
        FROM ConsumptionHistory ch
        JOIN Users u ON u.PersonID = ch.PersonID
        JOIN Flats f ON f.FlatNo = ch.FlatNo
        WHERE 1=1
    """
    params = []
    if person_id:
        query += " AND ch.PersonID = ?"
        params.append(person_id)
    if flat_no:
        query += " AND ch.FlatNo = ?"
        params.append(flat_no)

    query += " ORDER BY ch.BillingMonth DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Streamlit UI 
st.set_page_config(page_title="Electricity Billing System", layout="wide")
st.sidebar.title("⚡ Electricity Billing System")
menu = st.sidebar.radio("Menu", ["Add User", "Update/Delete User", "Insert Billing Data", "View Records", "Update/Delete Bill Record"])

if menu == "Add User":
    st.title("➕ Add New User")
    person_id = st.text_input("Person ID")
    name = st.text_input("Name")
    flat_no = st.text_input("Flat No")
    user_type = st.selectbox("User Type", ["Residential", "Commercial"], index=0)
    load_sanctioned = st.number_input("Load Sanctioned (kW)", min_value=0.0, step=0.1)
    phase = st.selectbox("Phase", ["1-Phase", "3-Phase"], index=0)
    if st.button("✅ Add User"):
        insert_user(person_id, name, flat_no, user_type, load_sanctioned, phase)
        st.success("User added successfully!")

elif menu == "Update/Delete User":
    st.title("✏️ Update or 🗑️ Delete User")
    users_df = get_table_data("Users")
    if not users_df.empty:
        selected_user_id = st.selectbox("Select a User ID", users_df["PersonID"].tolist())
        user_data = users_df[users_df["PersonID"] == selected_user_id].iloc[0]
        name = st.text_input("Name", user_data["Name"])
        flat_no = st.text_input("Flat No", user_data["FlatNo"])
        user_type = st.selectbox("User Type", ["Residential", "Commercial"], index=["Residential", "Commercial"].index(user_data["UserType"]))
        load_sanctioned = st.number_input("Load Sanctioned (kW)", min_value=0.0, step=0.1, value=float(user_data["LoadSanctioned"]))
        phase = st.selectbox("Phase", ["1-Phase", "3-Phase"], index=["1-Phase", "3-Phase"].index(user_data["Phase"]))
        if st.button("✏️ Update User"):
            update_user(selected_user_id, name, flat_no, user_type, load_sanctioned, phase)
            st.success("User updated successfully!")
        if st.button("🗑️ Delete User"):
            delete_user(selected_user_id)
            st.warning("User deleted!")
    else:
        st.warning("No users found!")

elif menu == "Insert Billing Data":
    st.title("📋 Insert Billing Data")
    
    # Fetch data for dropdowns
    users_df = get_table_data("Users")
    flats_df = get_table_data("Flats")
    gst_rates_df = get_table_data("GSTRates")
    duty_rates_df = get_table_data("ElectricDutyRates")

    # Select the person ID and flat number
    person_id = st.selectbox("Select Person ID", users_df["PersonID"].tolist())
    selected_user = users_df[users_df["PersonID"] == person_id].iloc[0]
    flat_no = st.selectbox("Select Flat No", flats_df[flats_df["FlatNo"].isin([selected_user["FlatNo"]])]["FlatNo"].tolist())

    # Convert month names to "YYYY-MM" format
    current_year = datetime.now().year
    month_names = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12"
    }

    selected_month_name = st.selectbox("Billing Month", list(month_names.keys()))
    billing_month = f"{current_year}-{month_names[selected_month_name]}"  # Ensure format is "YYYY-MM"

    present_reading = st.number_input("Present Reading (kWh)", min_value=0.0, step=0.01)

    # **Dropdown for GST**
    gst_options = gst_rates_df["GST"].tolist() if not gst_rates_df.empty else []
    gst_selected = st.selectbox("Select GST (%)", gst_options + ["Manual Entry"], index=0)
    gst_value = (
        st.number_input("Enter GST (%)", min_value=0.0, step=0.01) if gst_selected == "Manual Entry" else gst_selected
    )

    # **Dropdown for Electric Duty**
    duty_options = duty_rates_df["ElectricDuty"].tolist() if not duty_rates_df.empty else []
    duty_selected = st.selectbox("Select Electric Duty", duty_options + ["Manual Entry"], index=0)
    electric_duty = (
        st.number_input("Enter Electric Duty", min_value=0.0, step=0.01) if duty_selected == "Manual Entry" else duty_selected
    )

    # **Units Adjusted** (Admin can enter manually)
    units_adjusted = st.number_input("Units Adjusted (if any)", min_value=0.0, step=0.01, value=0.0)

    # **Surcharge** (Default = 0)
    surcharge = 0  # Fixed as per your requirement

    if st.button("📌 Insert Record"):
        insert_bill(person_id, flat_no, billing_month, present_reading, electric_duty, gst_value, units_adjusted, surcharge)
        st.success("✅ Billing record inserted successfully!")

elif menu == "Update/Delete Bill Record":
    st.title("✏️ Update or 🗑️ Delete Bill Record")

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all unique flat numbers & months for selection
    cursor.execute("SELECT DISTINCT FlatNo FROM BillingReadings")
    flat_list = [row[0] for row in cursor.fetchall()]
    flat_no = st.selectbox("Select Flat No", flat_list)

    
    cursor.execute("SELECT DISTINCT BillingMonth FROM BillingReadings WHERE FlatNo=?", (flat_no,))
    month_list = [row[0] for row in cursor.fetchall()]
    month = st.selectbox("Select Billing Month", month_list)


    # Fetch person details (handling multiple users in a flat)
    cursor.execute("SELECT PersonID, Name FROM Users WHERE FlatNo=?", (flat_no,))
    users = cursor.fetchall()

    if users:
        user_dict = {f"{row[1]} (ID: {row[0]})": row for row in users}  # Map Name & ID
        selected_user = st.selectbox("Select Person", list(user_dict.keys()))
        person_id, person_name = user_dict[selected_user]  # Extract selected ID & Name
    else:
        st.warning("⚠️ No user found for this flat!")
        person_id, person_name = None, "Unknown"

    # Display Person ID and Name
    st.text(f"👤 Person ID: {person_id}")
    st.text(f"📛 Name: {person_name}")

    # Fetch billing details using SQL
    cursor.execute("""
        SELECT PreviousReading, PresentReading, ElectricDuty, GST, Surcharge 
        FROM BillingReadings br
        JOIN BillingCharges bc ON br.ReadingID = bc.ReadingID
        WHERE br.FlatNo=? AND br.BillingMonth=?
    """, (flat_no, month))
    
    bill_data = cursor.fetchone()
    
    if bill_data:
        previous_reading, present_reading, electric_duty, gst, surcharge = bill_data
        present_reading = st.number_input("New Present Reading (kWh)", min_value=0.0, step=0.01, value=present_reading)
        electric_duty = st.number_input("Electric Duty", min_value=0.0, step=0.01, value=electric_duty)
        gst = st.number_input("GST", min_value=0.0, step=0.01, value=gst)
        units_adjusted = st.number_input("Units Adjusted", min_value=0.0, step=0.01, value=0.0)
        surcharge = st.number_input("Surcharge", min_value=0.0, step=0.01, value=surcharge)

        if st.button("✏️ Update Bill"):
            update_bill(person_id, flat_no, month, present_reading, electric_duty, gst, units_adjusted, surcharge)

        if st.button("🗑️ Delete Bill"):
            delete_bill(person_id, flat_no, month)
    else:
        st.warning("⚠️ No bill found for the selected Flat No and Month!")

    conn.close()


elif menu == "View Records":
    st.title("📊 View Records")
    
    tables = [
        "Users", "BillingReadings", "BillingCharges", "ConsumptionHistory",
        "Administrators", "Flats", "TariffSlabs", "GSTRates",
        "ElectricDutyRates", "UserClassification"
    ]
    
    selected_table = st.selectbox("Select a Table", tables)
    df = get_table_data(selected_table)
    st.dataframe(df)
