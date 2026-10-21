import streamlit as st
import pandas as pd

st.set_page_config(page_title="Swedavia Airports Flight Delays", layout="wide")

st.title("Analytics Dashboard for Swedavia Airports Flight Delays")

conn = st.connection("snowflake")

@st.cache_data
def load_data():
    query = "SELECT * FROM FLIGHTDATA_DB.MARTS.MART_FLIGHT_DELAYS"
    df = conn.query(query)
    df.columns = df.columns.str.upper()
    return df

df = load_data()

st.subheader("Overview")
col1, col2, col3 = st.columns(3)

total_flights = len(df)
avg_delay = df['DELAY_MINUTES'].mean()
delayed_flights_count = len(df[df['IS_DELAYED'] == True])
delay_percentage = (delayed_flights_count / total_flights) * 100 if total_flights > 0 else 0

with col1:
    st.metric("Total Flights", total_flights)
    
with col2:
    st.metric("Average Delay (minutes)", f"{round(avg_delay, 2)} min")
    
with col3:
    st.metric("Percentage of delayed flights", f"{round(delay_percentage, 1)} %")

st.divider()

st.subheader("Flight Delays by Airline")
delay_by_airline = df.groupby('AIRLINE_NAME')['DELAY_MINUTES'].mean().reset_index()

st.bar_chart(
    data=delay_by_airline,
    x='AIRLINE_NAME',
    y='DELAY_MINUTES',
    x_label="Airline",
    y_label="Average Delay (minutes)"
)

st.divider()

st.subheader("Flight Delays by weekday")


st.write("Average Delay by Day of the Week")
delay_by_day = df.groupby('DAY_OF_WEEK')['DELAY_MINUTES'].mean().reset_index()

day_mapping = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"
}

# Ändrar på ordningen så dagarna visar i veckoordningen. 
delay_by_day['DAY_OF_WEEK'] = delay_by_day['DAY_OF_WEEK'].map(day_mapping)

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

#Gör om kolumnen till en "Categorical" datatyp så att Streamlit förstår ordningen
delay_by_day['DAY_OF_WEEK'] = pd.Categorical(
    delay_by_day['DAY_OF_WEEK'], 
    categories=weekday_order, 
    ordered=True
)

delay_by_day = delay_by_day.sort_values('DAY_OF_WEEK')

st.bar_chart(
    data=delay_by_day,
    x='DAY_OF_WEEK',
    y='DELAY_MINUTES',
    x_label="Weekday",
    y_label="Average Delay (minutes)"
    )

st.divider()

st.subheader("Data Overview")

airlines = df['AIRLINE_NAME'].dropna().unique()
selected_airline = st.selectbox("Filter by Airline", ["All"] + list(airlines))

if selected_airline != "All":
    filtered_df = df[df['AIRLINE_NAME'] == selected_airline]
else:
    filtered_df = df
    
st.dataframe(filtered_df, use_container_width=True)


#######################################


st.subheader("Delay Analysis")
st.caption("Leave the filter empty to include everything.")

#Filter query
df["IS_DELAYED"] = df["IS_DELAYED"].fillna(False).astype(bool)
df["DELAY_MINUTES"] = pd.to_numeric(df["DELAY_MINUTES"], errors="coerce")
df["AIRPORT"] = df["AIRPORT_NAME_SV"].fillna(df["AIRPORT_CITY"])
df["FULL_DATE"] = pd.to_datetime(df["FULL_DATE"]).dt.date

breakdown_options = {
    "Direction": "DIRECTION",
    "Airline": "AIRLINE_NAME",
    "Airport": "AIRPORT",
    "Date": "FULL_DATE",
}
#Filter selector
breakdown_sel = st.multiselect("Break down by", list(breakdown_options), default=["Airline"])

def summarize(data, group_cols):
    data = data.assign(DELAY_IF_DELAYED=data["DELAY_MINUTES"].where(data["IS_DELAYED"]))
    #default
    if not group_cols:
        data = data.assign(SCOPE="All selected flights")
        group_cols = ["SCOPE"]
    out = data.groupby(group_cols, dropna=False).agg(
        FLIGHTS=("FLIGHT_ID", "size"),
        DELAYED_FLIGHTS=("IS_DELAYED", "sum"),
        TOTAL_DELAY_MIN=("DELAY_IF_DELAYED", "sum"),
        AVG_DELAY_MIN=("DELAY_IF_DELAYED", "mean"),
    ).reset_index()
    #% of total delayed
    out["PCT_DELAYED"] = (out["DELAYED_FLIGHTS"] / out["FLIGHTS"] * 100).round(1)
    out["AVG_DELAY_MIN"] = out["AVG_DELAY_MIN"].fillna(0).round(1)
    return out.sort_values("DELAYED_FLIGHTS", ascending=False)


summary = summarize(df, [breakdown_options[b] for b in breakdown_sel])
# remembered that data should be presented without _ so it doesn't look like its straight from DB
summary_display = summary.rename(columns={
    "AIRLINE_NAME": "Airline",
    "FULL_DATE": "Date",
    "FLIGHTS": "Total Flights",
    "DELAYED_FLIGHTS": "Delayed Flights",
    "TOTAL_DELAY_MIN": "Total Delay (min)",
    "AVG_DELAY_MIN": "Average Delay (min)",
    "PCT_DELAYED": "Delayed (%)",
})
#Add a % to the end of nr in the pct column without making it a string,
#format both average and total to display as whole numbers.
st.dataframe(summary_display.style.format({
    "Delayed (%)": "{:.1f}%",
    "Average Delay (min)": "{:.0f}",
    "Total Delay (min)": "{:.0f}",}),
    use_container_width=True, hide_index=True)

st.download_button("Download as CSV", summary.to_csv(index=False), "delay_analysis.csv", "text/csv")

st.divider()
