import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd


st.title("Interactive session - homepage")

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = pd.DataFrame({'coucou' : [1,2], 'hey' : [3,4]})

# click button to update worksheet
# This is behind a button to avoid exceeding Google API Quota
if st.button("Update worksheet"):
    df = conn.update(data=df)
    st.cache_data.clear()
    st.rerun()



