from os import read
import requests
from datetime import datetime
import json
import pandas as pd
import csv
import time
import streamlit as st
import os
import chime

#CoWIN Public API URLs
URL_PINCODE = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={}&date={}"
URL_DISTRICT = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id={}&date={}"

#Dataframe Column Names
COLUMNS = {
    'date':"Date",
    'district_name' : "District",
    'pincode': "Pincode",
    'name' : "Centre", 
    'fee_type' : "Type",
    'fee':"Fees",
    'available_capacity': "Availability",
    'min_age_limit':"Age",
    'vaccine':"Vaccine",
    'vaccine_name':'Name'
}

#Request Headers
headers = {
    "accept":"application/json",
    "Accept-Language": "hi_IN",
    "cache-control":"max-age=0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "upgrade-insecure-requests": "1",
    "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

#Function to load districts and state data
@st.cache
def load_districts():
    reader = csv.DictReader(open("DistrictCode.csv"))
    data_dict = {}
    for row in reader:
        if row["State"] in data_dict.keys():
            data_dict[row["State"]][row["District"]] = row["DistrictID"]
        else:
            data_dict[row["State"]] = {row["District"]: row["DistrictID"]}
    return data_dict

#Function to check if pincode is valid
def isValidPincode(pincode):
    if pincode.isnumeric() and len(pincode) == 6:
        return True
    return False

#Function to filter slots based on vacine type and minimum age parameters
def filterSlots(df,vaccine_type,minimum_age):
    if vaccine_type != "Any":
        df = df[df.Type == vaccine_type]
    if minimum_age !="Any":
        df = df[df.Age == minimum_age]
    return df
    

#Function to fetch pincode based parameters
def getPincodeFilters():
    col1, col2, col3, col4 = st.beta_columns(4)
    with col1:
        pincode = st.text_input("Enter Pincode","122002")
        st.write('You entered:', pincode)
    with col2:
        vaccine_type = st.selectbox('Vaccine (Free or Paid)',["Any","Free","Paid"])
        st.write('You selected:', vaccine_type)
    with col3:
        min_age = st.selectbox("Select Minimum Age",["Any",18,45])
        st.write("You selected:", min_age)
    with col4:
        vaccine_Name = st.selectbox('Select Vaccine Name',["Any","COVISHIELD","COVAXIN","CORBEVAX"])
        st.write('You selected:', vaccine_Name)
    return pincode, vaccine_type, min_age,vaccine_Name

        
        
#Function to fetch district based parameters
def getDistrictFilters(location_dict):
    col1, col2, col3, col4 ,col5 = st.beta_columns(5)
    with col1:
        state = st.selectbox('State',list(location_dict.keys()))
        st.write('You selected:', state)
    with col2:
        district = st.selectbox('District',list(location_dict[state].keys()))
        st.write('You selected:', district)
        districtID = location_dict[state][district]
    with col3:
        vaccine_type = st.selectbox('Vaccine (Free or Paid)',["Any","Free","Paid"])
        st.write('You selected:', vaccine_type)
    with col4:
        min_age = st.selectbox('Select Minimum Age',['Any',18,45])
        st.write('You selected:', min_age)
    with col5:
        vaccine_Name = st.selectbox('Select vaccine name',["Any","COVISHIELD","COVAXIN","CORBEVAX"])
        st.write('You selected vaccine name:', vaccine_Name)
    return districtID, vaccine_type , min_age, vaccine_Name
    

#Function to track slots 
def trackSlots(identifier, vaccine_type, min_age, date,vaccine_name, option):
    if option == "Pincode":
        URL = URL_PINCODE
    else:
        URL = URL_DISTRICT
    slt = st.table(pd.DataFrame())
    tsp = st.text('Slots will be tracked at 10 seconds interval. Last Tracked at : ' + str(datetime.now().time()))
    while True:   
        final_URL = URL.format(identifier,date)

        res = requests.get(final_URL,headers=headers, verify=False)
        
        slots = json.loads(res.text)["sessions"]
        slots_df = pd.DataFrame(slots, columns = COLUMNS.keys())
        slots_df.rename(columns = COLUMNS, inplace = True)
        slots_df = filterSlots(slots_df, vaccine_type, min_age ,vaccine_name)
        if len(slots_df):
            slt.table(slots_df)
            centres = slots_df["Centre"].unique()
            centres_str = "your preferred slots are available at " + ",".join(centres)
            os.system('say ' + centres_str)
        else:
            slt.info('No slots available for your preference. Relax, we are tracking them for you.')
        tsp.text('Slots will be tracked at 10 seconds interval. Last Tracked at : ' + str(datetime.now().time()))
        time.sleep(10)

#Function to find slots
def findSlots(identifier, vaccine_type, min_age, date,vaccine_name, option):
    if option == "Pincode":
        URL = URL_PINCODE
    else:
        URL = URL_DISTRICT
    slt = st.table(pd.DataFrame())
    final_URL = URL.format(identifier,date)
    res = requests.get(final_URL, headers=headers, verify=False)
    slots = json.loads(res.text)["sessions"]
    slots_df = pd.DataFrame(slots, columns = COLUMNS.keys())
    slots_df.rename(columns = COLUMNS, inplace = True)
    slots_df['Name']=vaccine_name
    slots_df1 = filterSlots(slots_df, vaccine_type, min_age)
    slots_df2=  slots_df1[slots_df1['Vaccine'] == vaccine_name] 
    if len(slots_df1):
     if vaccine_name.upper() in ['ANY']:
           slt.table(slots_df1)
           os.system('say "your preferred slots are available"')
     else:
           slt.table(slots_df2)
           os.system('say "your preferred slots are available"')
    else:
        slt.error('No slots available for your preference, please start a tracker to keep you notified.')

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

if __name__ == "__main__":
    st.markdown("<h1 style='text-align: center; color: red;'>CoWIN Vaccination Slot Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: black;margin-bottom: 2em;'>Web App by <a href='https://www.linkedin.com/in/vaibhav-kunwar-990059218/'>Vaibhav Kunwar</a></div>", unsafe_allow_html=True)

    location_dict = load_districts()
    
    col1, col2 = st.beta_columns(2)
    with col1:
        option = st.selectbox("Slots By ",["District","Pincode"])
        st.write('You selected:', option)
    
    with col2:
        date = st.date_input("Pick a date").strftime("%d-%m-%Y")
        st.write('You selected:', date)

    if option == "Pincode":
        identifier, vaccine_type, min_age , vaccine_name = getPincodeFilters()
    else:
        identifier, vaccine_type, min_age , vaccine_name = getDistrictFilters(location_dict)
    
    _,col1,col2,_ = st.beta_columns([4, 1, 1, 4])
    with col1:
        find_slots = st.button('Find Slots')         
    with col2:
        track_slots =  st.button('Track Slots')

    if find_slots:
        findSlots(identifier, vaccine_type, min_age, date,vaccine_name, option)
        
    if track_slots:
        trackSlots(identifier, vaccine_type, min_age, date,vaccine_name, option)
