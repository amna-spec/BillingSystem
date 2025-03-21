# Description: This file contains the main logic for the Streamlit app.
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from functions import *
# Streamlit UI 
st.set_page_config(page_title="Electricity Billing System", layout="wide")
st.sidebar.title("⚡ Electricity Billing System")
st.sidebar.markdown("---")  # Add a separator

# Define a single menu variable
menu_options = {
    "👤 User Management": {
        "User Operations": ["Add User", "Update User", "Delete User"],
        "📊 Report Logs": ["User Directory"]
    },
    "📊 Billing Management": {
        "Billing Operations": ["Enter Bill Record", "Update/Delete Bill Record"],
        "Billing Actions": ["Generate Bill"],
        "📊 Report Logs": ["Billing Records"]
    },
    "⚡ Rate Management": {
        "GST": ["Set GST Rate", "Update GST Rate", "View GST Rate"],
        "Electric Duty": ["Set Electric Duty", "Update Electric Duty", "View Electric Duty"],
        "Surcharge": ["Set Surcharge Rate", "Update Surcharge Rate", "View Surcharge Rate"]
    }
}


# Sidebar navigation
st.sidebar.title("📌 Main Menu")
# Sidebar for menu selection
selected_section = st.sidebar.radio("Select Section", list(menu_options.keys()))

# Get the submenu based on selected section
submenu_options = []
for category, options in menu_options[selected_section].items():
    submenu_options.extend(options)

# Create radio button for menu selection
selected_option = st.sidebar.radio("Menu", submenu_options)

st.sidebar.markdown("---")  # Add a separator

# Main logic
# User Management
if selected_section == "👤 User Management":
  if selected_option== "Add User":
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

 # Update or Delete User
  elif selected_option == "Update User" or selected_option == "Delete User":
    st.title("✏️ Update or 🗑️ Delete User")
    # Placeholder for fetching users
    users_df = get_table_data("Users")
    if not users_df.empty:
        selected_user_id = st.selectbox("Select a User ID", users_df["PersonID"].tolist())
        user_data = users_df[users_df["PersonID"] == selected_user_id].iloc[0]
        name = st.text_input("Name", user_data["Name"])
        flat_no = st.text_input("Flat No", user_data["FlatNo"])
        user_type = st.selectbox("User Type", ["Residential", "Commercial"], index=["Residential", "Commercial"].index(user_data["UserType"]))
        load_sanctioned = st.number_input("Load Sanctioned (kW)", min_value=0.0, step=0.1, value=float(user_data["LoadSanctioned"]))
        phase = st.selectbox("Phase", ["1-Phase", "3-Phase"], index=["1-Phase", "3-Phase"].index(user_data["Phase"]))
        
        if selected_option == "Update User" and st.button("✏️ Update User"):
            update_user(selected_user_id, name, flat_no, user_type, load_sanctioned, phase)
            st.success("User updated successfully!")
        elif selected_option == "Delete User" and st.button("🗑️ Delete User"):
            delete_user(selected_user_id)
            st.warning("User deleted!")
    else:
        st.warning("No users found!")
 # Report Logs to view all users     and allowing searching by persno and name   
  elif selected_option == "User Directory":
     st.title("📜 User Directory")

     # Fetch Users Data
     users_df = get_table_data("Users")

     if not users_df.empty:
        st.write("### 🔍 Search Users (Optional)")
        col1, col2 = st.columns(2)

        with col1:
            person_id_filter = st.text_input("Search by Person ID (exact match):", key="person_id")
        with col2:
            name_filter = st.text_input("Search by Name (contains, case-insensitive):", key="name")

        # Initialize filtered DataFrame with all users
        filtered_users_df = users_df.copy()

        # Apply search filters if provided
        if person_id_filter:
            filtered_users_df = filtered_users_df[filtered_users_df["PersonID"].astype(str) == person_id_filter]
        if name_filter:
            filtered_users_df = filtered_users_df[filtered_users_df["Name"].str.contains(name_filter, case=False, na=False)]

        # Display full dataset or filtered results
        if filtered_users_df.empty:
            st.warning("No users found matching your search criteria.")
        else:
            st.write(f"### Users ({len(filtered_users_df)} records found)")
            st.dataframe(filtered_users_df.sort_values(by="Name"))

        # Download Option
        st.download_button("📥 Download CSV", filtered_users_df.to_csv(index=False), "users.csv", "text/csv")

     else:
        st.warning("No users available!")

# Rate Management Logic
elif selected_section == "⚡ Rate Management":
    st.title("⚡ Manage Rates")
    effective_date = datetime.today().strftime('%Y-%m-%d')
    
    if "GST" in selected_option:
        st.subheader("GST Rates")
        if "Set" in selected_option or "Update" in selected_option:
            gst_rate = st.number_input("Enter GST Rate (%)", min_value=0.0, step=0.1)
            if st.button("💾 Save GST Rate"):
                upsert_gst_rate(gst_rate, effective_date)
                st.success("GST Rate updated!")
        elif "View" in selected_option:
            st.dataframe(get_gst_rates())
    
    elif "Electric Duty" in selected_option:
        st.subheader("Electric Duty Rates")
        if "Set" in selected_option or "Update" in selected_option:
            duty_rate = st.number_input("Enter Electric Duty Rate (%)", min_value=0.0, step=0.1)
            if st.button("💾 Save Electric Duty Rate"):
                upsert_electric_duty_rate(duty_rate, effective_date)
                st.success("Electric Duty Rate updated!")
        elif "View" in selected_option:
            st.dataframe(get_electric_duty_rates())
    
    elif "Surcharge" in selected_option:
        st.subheader("Surcharge Rates")
        if "Set" in selected_option or "Update" in selected_option:
            surcharge_type_id = st.number_input("Surcharge Type ID", min_value=1, step=1)
            rate_per_unit = st.number_input("Rate Per Unit", min_value=0.0, step=0.1)
            units_from = st.number_input("Units From", min_value=0, step=1)
            units_to = st.number_input("Units To", min_value=0, step=1)
            if st.button("💾 Save Surcharge Rate"):
                upsert_surcharge_rate(surcharge_type_id, rate_per_unit, units_from, units_to, effective_date)
                st.success("Surcharge Rate updated!")
        elif "View" in selected_option:
            st.dataframe(get_surcharge_rates())
# Handling Billing Management section
elif selected_section == "⚡ Billing Management":
    if selected_option == "Enter Bill Record":
     st.title("📋 Insert Billing Data")

     # Fetch necessary data
     users_df = get_table_data("Users") 
     flats_df = get_table_data("Flats")
     gst_rates_df = get_table_data("GSTRates")
     duty_rates_df = get_table_data("ElectricDutyRates")
     surcharge_types_df = get_surcharge_data()

     # Select user and flat
     person_id = st.selectbox("Select Person ID", users_df["PersonID"].tolist())
     selected_user = users_df[users_df["PersonID"] == person_id].iloc[0]
     flat_no = st.selectbox("Select Flat No", flats_df[flats_df["FlatNo"].isin([selected_user["FlatNo"]])]["FlatNo"].tolist())

     # Select Billing Month (format: YYYY-MM)
     current_year = datetime.now().year
     month_mapping = {m: f"{current_year}-{i:02d}" for i, m in enumerate([
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"], 1)}
     selected_month = st.selectbox("Billing Month", list(month_mapping.keys()))
     billing_month = month_mapping[selected_month]

     # Meter Reading Inputs
     present_reading = st.number_input("Present Reading (kWh)", min_value=0.0, step=0.01)

     # GST Selection
     gst_options = gst_rates_df["GST"].tolist() if not gst_rates_df.empty else []
     gst_selected = st.selectbox("Select GST (%)", gst_options + ["Manual Entry"], index=0)
     gst_value = st.number_input("Enter GST (%)", min_value=0.0, step=0.01) if gst_selected == "Manual Entry" else gst_selected

     # Electric Duty Selection
     duty_options = duty_rates_df["ElectricDuty"].tolist() if not duty_rates_df.empty else []
     duty_selected = st.selectbox("Select Electric Duty", duty_options + ["Manual Entry"], index=0)
     electric_duty = st.number_input("Enter Electric Duty", min_value=0.0, step=0.01) if duty_selected == "Manual Entry" else duty_selected

     # **Units Adjusted (for previous months)**
     units_adjusted = st.number_input("Units Adjusted (if any)", min_value=0.0, step=0.01, value=0.0)
     
     st.subheader("⚡ Surcharge Handling") 
     # **📌 Step 1: Select Surcharge Type for the Current Billing Month**
     surcharge_options = surcharge_types_df["SurchargeType"].tolist() if not surcharge_types_df.empty else []
     selected_surcharge_type = st.selectbox("Select Surcharge Type for Current Billing Month", surcharge_options + ["Manual Entry"], index=0)
     
     manual_surcharge = 0  # Default to 0
     if selected_surcharge_type == "Manual Entry":
       manual_surcharge = st.number_input("Enter Surcharge for Current Billing Month (if any)", min_value=0.0, step=0.01)
     
     # Fetch surcharge for the current month
     if selected_surcharge_type != "Manual Entry":
      try:
        month_surcharge = get_surcharge_amount(flat_no, billing_month, selected_surcharge_type)
      except Exception as e:
        st.error(f"Error fetching current month surcharge: {e}")
        month_surcharge = 0.0
     else:
      month_surcharge = manual_surcharge
     
     # **📌 Step 2: Select Adjusted Months for Surcharge Adjustments**
     previous_months = get_previous_billing_months(flat_no, billing_month)   
     adjusted_months = st.multiselect("Select Adjusted Billing Months", previous_months)
     
     # **📌 Step 3: Select Surcharge Type for Each Adjusted Month**
     adjusted_surcharge_total = 0

     for adjusted_month in adjusted_months:
        st.markdown(f"**Adjusted Billing Month: {adjusted_month}**")
        selected_adjusted_surcharge_type = st.selectbox(
          f"Select Surcharge Type for {adjusted_month}",
          surcharge_options + ["Manual Entry"],
          index=0,
          key=f"surcharge_type_{adjusted_month}"
         )

        manual_adjusted_surcharge = 0
        if selected_adjusted_surcharge_type == "Manual Entry":
           manual_adjusted_surcharge = st.number_input(
              f"Enter Surcharge for {adjusted_month} (if any)",
              min_value=0.0,
              step=0.01,
              key=f"manual_surcharge_{adjusted_month}"
             )

        if selected_adjusted_surcharge_type != "Manual Entry":
          try:
            adjusted_surcharge = get_surcharge_amount(flat_no, adjusted_month, selected_adjusted_surcharge_type)
          except Exception as e:
            st.error(f"Error fetching surcharge for {adjusted_month}: {e}")
            adjusted_surcharge = 0.0
        else:
           adjusted_surcharge = manual_adjusted_surcharge

        adjusted_surcharge_total += adjusted_surcharge

     
     # **📌 Step 4: Compute Total Surcharge**
     computed_surcharge = month_surcharge + adjusted_surcharge_total
     

     # **7️⃣ Display Computed Values**
     st.text(f"🔹 **Current Month Surcharge:** {month_surcharge:.2f} PKR")
     st.text(f"🔹 **Adjusted Surcharge Total:** {adjusted_surcharge_total:.2f} PKR")
     st.text(f"💰 **Final Computed Surcharge:** {computed_surcharge:.2f} PKR")

     # **Insert Record Button**
     if st.button("📌 Insert Record"):
      insert_bill(person_id, flat_no, billing_month, present_reading, electric_duty, gst_value, units_adjusted, computed_surcharge)
      st.success("✅ Billing record inserted successfully!")

    elif selected_option== "Update/Delete Bill Record":
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

     cursor.execute("""
        SELECT br.PreviousReading, br.PresentReading, bc.ElectricDuty, bc.GST, bc.TotalSurcharge 
        FROM BillingReadings br
        JOIN BillingCharges bc ON br.ReadingID = bc.ReadingID
        WHERE br.FlatNo = %s AND br.BillingMonth = %s
        """, (flat_no, month))

     bill_data = cursor.fetchone()

     if bill_data:
        previous_reading, present_reading, electric_duty, gst, surcharge = bill_data

         # 📌 Editable Inputs
        present_reading = st.number_input("New Present Reading (kWh)", min_value=0.0, step=0.01, value=present_reading)
        electric_duty = st.number_input("Electric Duty", min_value=0.0, step=0.01, value=electric_duty)
        gst = st.number_input("GST (%)", min_value=0.0, step=0.01, value=gst)
        units_adjusted = st.number_input("Units Adjusted", min_value=0.0, step=0.01, value=0.0)
        surcharge = st.number_input("Surcharge", min_value=0.0, step=0.01, value=surcharge)

     try: 
                    # 📌 Update Button
        if st.button("✏️ Update Bill Record"):
             update_bill(flat_no, billing_month, present_reading, electric_duty, gst, units_adjusted, surcharge)
             st.success("✅ Bill updated successfully!")

                   # 📌 Delete Button
        if st.button("🗑️ Delete Bill Record"):
            delete_bill(flat_no, billing_month)
            st.success("❌ Bill deleted successfully!")

        else:
         st.warning("⚠️ No bill found for the selected Flat No and Month!")

     except Exception as e:
        st.error(f"❌ An error occurred: {e}")

     finally:
        if conn:
            conn.close()  # Ensure the connection is always closed


    elif selected_option == "Billing Records":
     st.title("📊 View Records")

     # List of available tables
     tables = [
        "BillingReadings", "BillingCharges", "ConsumptionHistory",
        "TariffSlabs", "GSTRates", "ElectricDutyRates",
     ]
    
     # Dropdown to select a table
     selected_table = st.selectbox("Select a Table", tables)
    
     # Fetch data for the selected table
     df = get_table_data(selected_table)
    
     # Display the raw dataframe
     st.write(f"### {selected_table} Table")
     st.dataframe(df)

     # Add advanced search filters
     st.markdown("---")
     st.write("### 🔍 Advanced Search")
    
     # Use columns for better alignment
     col1, col2 = st.columns(2)
    
     # Initialize filtered DataFrame
     filtered_df = df.copy()

     # ✅ **Initialize filters to avoid NameError**
     flat_no_filter = None
     billing_month_filter = None
     person_id_filter = None
     name_filter = None

     # Dynamic search filters based on the selected table
     if selected_table == "BillingReadings":
        with col1:
            flat_no_filter = st.text_input("Search by Flat No (exact match):")
        with col2:
            billing_month_filter = st.text_input("Search by Billing Month (YYYY-MM):")
        
        # Apply filters
        if flat_no_filter:
            filtered_df = filtered_df[filtered_df["FlatNo"].astype(str) == flat_no_filter]
        if billing_month_filter:
            filtered_df = filtered_df[filtered_df["BillingMonth"].astype(str) == billing_month_filter]
    
     elif selected_table == "BillingCharges":
        with col1:
            flat_no_filter = st.text_input("Search by Flat No (exact match):")

        # Apply filters
        if flat_no_filter:
            filtered_df = filtered_df[filtered_df["FlatNo"].astype(str) == flat_no_filter]

     elif selected_table == "ConsumptionHistory":
        with col1:
            billing_month_filter = st.text_input("Search by Billing Month (YYYY-MM):")

        # Apply filters
        if billing_month_filter:
            filtered_df = filtered_df[filtered_df["BillingMonth"].astype(str) == billing_month_filter]

     # General Search if no specific filters are applied
     # **Fix: Ensure variables exist before checking them**
     if not any([flat_no_filter, billing_month_filter, person_id_filter, name_filter]):
        st.markdown("---")
        st.write("### 🔍 General Search")
        search_term = st.text_input("Search within the table (all columns):")
        if search_term:
            filtered_df = filtered_df[filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
    
     # Display filtered results
     if not filtered_df.empty:
        st.write(f"### Filtered Results ({len(filtered_df)} records found)")
        st.dataframe(filtered_df)
     else:
        st.warning("No records found matching your search criteria.")


    elif selected_option == "Generate Bill":
     st.title("⚡ User-Specific Electricity Bill Generation")
    
     # Option 1: Generate Bill for a specific user and month
     flat_no = st.text_input("Enter Flat Number:", key="flat_no_input")
     person_id = st.text_input("Enter Person ID:", key="person_id_input")
     billing_month = st.text_input("Enter Billing Month (YYYY-MM):", key="single_bill_month")

     if st.button("Fetch Bill Details"):
      if flat_no and billing_month:
        # Fetch bill details (Note: No PersonID is used here)
        bill = fetch_complete_bill(flat_no, billing_month)  
        
        if bill:
            # Unpack bill details
            bill_id, prev_reading, pres_reading, units_consumed, units_adjusted, rate_per_unit, var_charges, elec_duty, gst, surcharge, net_amount, payable_amount = bill

            # Store bill details in session state
            st.session_state.bill_id = bill_id
            st.session_state.prev_reading = prev_reading
            st.session_state.pres_reading = pres_reading
            st.session_state.units_consumed = units_consumed
            st.session_state.units_adjusted = units_adjusted
            st.session_state.rate_per_unit = rate_per_unit
            st.session_state.var_charges = var_charges
            st.session_state.elec_duty = elec_duty
            st.session_state.gst = gst
            st.session_state.surcharge = surcharge
            st.session_state.net_amount = net_amount
            st.session_state.payable_amount = payable_amount

            # Fetch user details for PDF generation (Only if person_id is given)
            if person_id:
                conn = sqlite3.connect("billing_system.db")
                cursor = conn.cursor()
                cursor.execute("SELECT Name FROM Users WHERE FlatNo = ? AND PersonID = ?", (flat_no, person_id))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    st.session_state.name = result[0]
                else:
                    st.warning("User not found for the given Flat Number and Person ID.")
        
        else:
            st.error("No bill found for the given Flat Number and Billing Month.")
    else:
        st.error("Please enter Flat Number and Billing Month.")  # Removed Person ID from this error


    # If bill details are fetched, display editable fields
     
    if "bill_id" in st.session_state:
     # Editable fields with current values
     present_reading = st.number_input("Present Reading:", value=st.session_state.pres_reading)
     units_adjusted = st.number_input("Units Adjusted:", value=st.session_state.units_adjusted)
     electric_duty = st.number_input("Electric Duty:", value=st.session_state.elec_duty)
     gst = st.number_input("GST:", value=st.session_state.gst)
     surcharge = st.number_input("Surcharge:", value=st.session_state.surcharge)

     if st.button("Update Bill"):
        # Call update_bill function with modified values
        update_bill(
            flat_no=flat_no,
            month=billing_month,
            present_reading=present_reading if present_reading != st.session_state.pres_reading else None,
            electric_duty=electric_duty if electric_duty != st.session_state.elec_duty else None,
            gst=gst if gst != st.session_state.gst else None,
            units_adjusted=units_adjusted if units_adjusted != st.session_state.units_adjusted else None,
            surcharge=surcharge if surcharge != st.session_state.surcharge else None
         )
        #Fetch updated bill details
        updated_bill = fetch_complete_bill(flat_no, billing_month)
        if updated_bill:
            # Unpack and store updated details
            (reading_id, prev_reading, pres_reading, units_consumed, units_adjusted, bill_id, 
            rate_per_unit, var_charges, elec_duty, gst, surcharge, net_amount, payable_amount) = updated_bill

            st.session_state.updated_bill = {
                "units_consumed": units_consumed,
                "variable_charges": var_charges,
                "net_amount": net_amount,
                "payable_amount": payable_amount
            }
            st.session_state.pres_reading = pres_reading
            st.session_state.units_adjusted = units_adjusted
            st.session_state.elec_duty = elec_duty
            st.session_state.gst = gst
            st.session_state.surcharge = surcharge

                # If bill is updated, show download button
    if "updated_bill" in st.session_state:
        # Generate updated PDF
        pdf_path = generate_pdf(
            flat_no, st.session_state.person_id, st.session_state.name, billing_month,
            f"01-{billing_month.split('-')[1]}-25", st.session_state.prev_reading, st.session_state.pres_reading,
            st.session_state.updated_bill["units_consumed"], st.session_state.elec_duty, st.session_state.gst, st.session_state.surcharge,
            st.session_state.updated_bill["variable_charges"], st.session_state.updated_bill["net_amount"],
            st.session_state.updated_bill["payable_amount"]
        )

        # Provide download button for the updated PDF
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📥 Download Updated Bill PDF",
                f,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf"
            )

    # Separator
    st.markdown("---")  

    # Option 2: Bulk Electricity Bill Generation
    st.title("📑 Batch Electricity Bill Generation")
    selected_month = st.text_input("Enter Billing Month (YYYY-MM):", key="bulk_bill_month")  # Unique key added

    if st.button("Generate Bills"):
        if selected_month:
            billing_data = fetch_billing_data(selected_month)
            if billing_data:
                pdf_file = Generate_bulk_bill_pdf(billing_data, selected_month)
                st.download_button(
                    label="Download PDF",
                    data=pdf_file.getvalue(),  # Ensure binary data is passed
                    file_name=f"Bulk_Bills_{selected_month}.pdf",
                    mime="application/pdf"
                )

            else:
                st.warning("No billing data found for the selected month!")
        else:
            st.error("Please enter a valid month in YYYY-MM format.")


