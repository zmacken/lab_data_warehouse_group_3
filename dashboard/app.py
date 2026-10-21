import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Swedavia Airports Flight Delays",
    page_icon="✈️",
    layout="wide",
)


st.title("Swedavia Airports Flight Delays")

conn = st.connection("snowflake")


# Hämta data (cachas i 1 timme)
@st.cache_data(ttl=3600)
def load_data():
    query = "SELECT * FROM FLIGHTDATA_DB.MARTS.MART_FLIGHT_DELAYS"
    df = conn.query(query)
    df.columns = df.columns.str.upper()
    return df


df = load_data()


# Förbered kolumner
df["IS_DELAYED"] = df["IS_DELAYED"].fillna(False).astype(bool)
df["DELAY_MINUTES"] = pd.to_numeric(df["DELAY_MINUTES"], errors="coerce")
df["AIRPORT"] = df["AIRPORT_NAME_SV"].fillna(df["AIRPORT_CITY"])
df["FULL_DATE"] = pd.to_datetime(df["FULL_DATE"]).dt.date

df["AIRPORT"] = df["AIRPORT"].fillna("Unknown")
df["AIRLINE_NAME"] = df["AIRLINE_NAME"].fillna("Unknown")
df["OTHER_AIRPORT"] = (
    df["OTHER_AIRPORT_NAME_SV"].fillna(df["OTHER_AIRPORT_CITY"]).fillna("Unknown")
)
df["IS_WEEKEND"] = df["IS_WEEKEND"].fillna(False).astype(bool)
# SCHEDULED_UTC är i UTC, så vi räknar om till svensk tid innan timmen tas ut
_scheduled_local = pd.to_datetime(df["SCHEDULED_UTC"], utc=True).dt.tz_convert(
    "Europe/Stockholm"
)
df["SCHEDULED_HOUR"] = _scheduled_local.dt.hour

day_mapping = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}
weekday_order = list(day_mapping.values())


# Sidopanel med filter (gäller alla flikar)
with st.sidebar:
    st.header("Filters")

    min_date, max_date = df["FULL_DATE"].min(), df["FULL_DATE"].max()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    sel_airports = st.multiselect("Airport", sorted(df["AIRPORT"].unique()))
    sel_airlines = st.multiselect("Airline", sorted(df["AIRLINE_NAME"].unique()))
    sel_directions = st.multiselect(
        "Direction", sorted(df["DIRECTION"].dropna().unique())
    )
    st.caption("Leave a filter empty to include everything.")

if len(date_range) == 2:
    start_date, end_date = date_range
else:  # användaren har bara valt första datumet än så länge
    start_date = end_date = date_range[0]

# Behåll bara rader som matchar filtren (tomt val = ingen filtrering)
mask = (df["FULL_DATE"] >= start_date) & (df["FULL_DATE"] <= end_date)
if sel_airports:
    mask &= df["AIRPORT"].isin(sel_airports)
if sel_airlines:
    mask &= df["AIRLINE_NAME"].isin(sel_airlines)
if sel_directions:
    mask &= df["DIRECTION"].isin(sel_directions)
df = df[mask]

if df.empty:
    st.warning("No flights match the selected filters.")
    st.stop()



# Hjälpfunktioner
def kpi_table(data, group_cols):
    """Flights, % delayed and avg delay (all flights) per group."""
    out = (
        data.groupby(group_cols, dropna=False)
        .agg(
            FLIGHTS=("FLIGHT_ID", "size"),
            DELAYED=("IS_DELAYED", "sum"),
            AVG_DELAY=("DELAY_MINUTES", "mean"),
        )
        .reset_index()
    )
    out["PCT_DELAYED"] = (out["DELAYED"] / out["FLIGHTS"] * 100).round(1)
    out["AVG_DELAY"] = out["AVG_DELAY"].round(1)
    return out


def on_time_pct(delays, threshold=15):
    """Share of flights with a delay of at most `threshold` minutes."""
    valid = delays.dropna()
    return (valid <= threshold).mean() * 100 if len(valid) else float("nan")


tab_overview, tab_data, tab_analysis, tab_time, tab_routes = st.tabs(
    ["Overview", "Data Overview", "Delay Analysis", "Time Patterns", "Airports & Routes"]
)


# Overview
with tab_overview:
    total_flights = len(df)
    avg_delay = df["DELAY_MINUTES"].mean()
    delayed_flights_count = len(df[df["IS_DELAYED"] == True])
    delay_percentage = (
        (delayed_flights_count / total_flights) * 100 if total_flights > 0 else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Flights", f"{total_flights:,}".replace(",", " "), border=True)
    col2.metric(
        "Average Delay",
        f"{round(avg_delay, 1)} min" if pd.notna(avg_delay) else "–",
        border=True,
    )
    col3.metric("Delayed flights", f"{round(delay_percentage, 1)} %", border=True)


    col4, col5, col6 = st.columns(3)
    otp = on_time_pct(df["DELAY_MINUTES"])
    median_delay = df["DELAY_MINUTES"].median()
    p90_delay = df["DELAY_MINUTES"].quantile(0.9)
    col4.metric(
        "On-time (≤ 15 min)",
        f"{otp:.1f} %" if pd.notna(otp) else "–",
        border=True,
        help="Share of flights delayed 15 minutes or less (early flights count as on time).",
    )
    col5.metric(
        "Median Delay",
        f"{median_delay:.0f} min" if pd.notna(median_delay) else "–",
        border=True,
    )
    col6.metric(
        "90th Percentile Delay",
        f"{p90_delay:.0f} min" if pd.notna(p90_delay) else "–",
        border=True,
        help="9 out of 10 flights are delayed less than this.",
    )

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.subheader("Average delay by airline")
            delay_by_airline = (
                df.groupby("AIRLINE_NAME")["DELAY_MINUTES"].mean().reset_index()
            )
            st.bar_chart(
                data=delay_by_airline,
                x="AIRLINE_NAME",
                y="DELAY_MINUTES",
                x_label="Airline",
                y_label="Average Delay (minutes)",
                sort="-DELAY_MINUTES",
            )

    with right:
        with st.container(border=True):
            st.subheader("Average delay by weekday")
            delay_by_day = df.groupby("DAY_OF_WEEK")["DELAY_MINUTES"].mean().reset_index()

            delay_by_day["DAY_OF_WEEK"] = delay_by_day["DAY_OF_WEEK"].map(day_mapping)
            delay_by_day["DAY_OF_WEEK"] = pd.Categorical(
                delay_by_day["DAY_OF_WEEK"], categories=weekday_order, ordered=True
            )
            delay_by_day = delay_by_day.sort_values("DAY_OF_WEEK")

            st.bar_chart(
                data=delay_by_day,
                x="DAY_OF_WEEK",
                y="DELAY_MINUTES",
                x_label="Weekday",
                y_label="Average Delay (minutes)",
                sort=False,
            )


    left2, right2 = st.columns(2)

    with left2:
        with st.container(border=True):
            st.subheader("Arrivals vs. departures")
            by_direction = kpi_table(df, ["DIRECTION"])
            st.bar_chart(
                data=by_direction,
                x="DIRECTION",
                y="PCT_DELAYED",
                x_label="Direction",
                y_label="Delayed flights (%)",
            )

    with right2:
        with st.container(border=True):
            st.subheader("Distribution of delays")
            # Dela in förseningar i grupper och räkna flyg per grupp
            bins = [-float("inf"), 0, 15, 30, 60, 120, float("inf")]
            labels = ["On time / early", "1–15 min", "16–30 min", "31–60 min", "1–2 h", "2 h +"]
            dist = (
                pd.cut(df["DELAY_MINUTES"], bins=bins, labels=labels)
                .value_counts()
                .reindex(labels)
                .rename_axis("BUCKET")
                .reset_index(name="FLIGHTS")
            )
            st.bar_chart(
                data=dist,
                x="BUCKET",
                y="FLIGHTS",
                x_label="Delay",
                y_label="Flights",
                sort=False,
            )


# Data Overview
with tab_data:
    st.subheader("Data Overview")

    airlines = df["AIRLINE_NAME"].dropna().unique()
    selected_airline = st.selectbox("Filter by Airline", ["All"] + sorted(airlines))

    if selected_airline != "All":
        filtered_df = df[df["AIRLINE_NAME"] == selected_airline]
    else:
        filtered_df = df

    st.caption(f"{len(filtered_df):,} rows".replace(",", " "))
    st.dataframe(filtered_df, width="stretch")

# Delay Analysis
with tab_analysis:
    st.subheader("Delay Analysis")
    st.caption(
        "Note: *Average Delay* in this table is calculated over **delayed flights only**, "
        "while the Overview tab averages over **all flights**."
    )

    breakdown_options = {
        "Direction": "DIRECTION",
        "Airline": "AIRLINE_NAME",
        "Airport": "AIRPORT",
        "Date": "FULL_DATE",
        "Other airport": "OTHER_AIRPORT",
        "Hour of day": "SCHEDULED_HOUR",
        "Weekend": "IS_WEEKEND",
    }
    breakdown_sel = st.multiselect(
        "Break down by",
        list(breakdown_options),
        default=["Airline"],
        help="Leave the filter empty to include everything.",
    )

    def summarize(data, group_cols):
        # Försening räknas här bara för försenade flyg (övriga blir NaN)
        data = data.assign(
            DELAY_IF_DELAYED=data["DELAY_MINUTES"].where(data["IS_DELAYED"])
        )

        if not group_cols:
            data = data.assign(SCOPE="All selected flights")
            group_cols = ["SCOPE"]
        out = (
            data.groupby(group_cols, dropna=False)
            .agg(
                FLIGHTS=("FLIGHT_ID", "size"),
                DELAYED_FLIGHTS=("IS_DELAYED", "sum"),
                TOTAL_DELAY_MIN=("DELAY_IF_DELAYED", "sum"),
                AVG_DELAY_MIN=("DELAY_IF_DELAYED", "mean"),
            )
            .reset_index()
        )

        out["PCT_DELAYED"] = (out["DELAYED_FLIGHTS"] / out["FLIGHTS"] * 100).round(1)
        out["AVG_DELAY_MIN"] = out["AVG_DELAY_MIN"].fillna(0).round(1)
        return out.sort_values("DELAYED_FLIGHTS", ascending=False)

    summary = summarize(df, [breakdown_options[b] for b in breakdown_sel])

    summary_display = summary.rename(
        columns={
            "AIRLINE_NAME": "Airline",
            "FULL_DATE": "Date",
            "FLIGHTS": "Total Flights",
            "DELAYED_FLIGHTS": "Delayed Flights",
            "TOTAL_DELAY_MIN": "Total Delay (min)",
            "AVG_DELAY_MIN": "Average Delay (min)",
            "PCT_DELAYED": "Delayed (%)",
        }
    )

    st.dataframe(
        summary_display.style.format(
            {
                "Delayed (%)": "{:.1f}%",
                "Average Delay (min)": "{:.0f}",
                "Total Delay (min)": "{:.0f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.download_button(
        "⬇Download as CSV",
        summary.to_csv(index=False),
        "delay_analysis.csv",
        "text/csv",
    )

# Time Patterns
with tab_time:
    st.subheader("Time Patterns")
    st.caption("Hours are shown in Stockholm local time.")

    left, right = st.columns(2)


    with st.container(border=True):
        st.subheader("Delayed flights by hour of day")
        by_hour = kpi_table(df.dropna(subset=["SCHEDULED_HOUR"]), ["SCHEDULED_HOUR"])
        st.bar_chart(
            data=by_hour,
            x="SCHEDULED_HOUR",
            y="PCT_DELAYED",
            x_label="Scheduled hour",
            y_label="Delayed flights (%)",
        )


    # Värmekarta: veckodag x timme, färg = andel försenade
    with st.container(border=True):
        st.subheader("When are delays worst? Weekday × hour")
        heat = kpi_table(
            df.dropna(subset=["SCHEDULED_HOUR", "DAY_OF_WEEK"]),
            ["DAY_OF_WEEK", "SCHEDULED_HOUR"],
        )
        heat["WEEKDAY"] = heat["DAY_OF_WEEK"].map(day_mapping)
        heatmap = (
            alt.Chart(heat)
            .mark_rect()
            .encode(
                x=alt.X("SCHEDULED_HOUR:O", title="Scheduled hour"),
                y=alt.Y("WEEKDAY:N", sort=weekday_order, title=None),
                color=alt.Color("PCT_DELAYED:Q", title="% delayed"),
                tooltip=[
                    alt.Tooltip("WEEKDAY:N", title="Weekday"),
                    alt.Tooltip("SCHEDULED_HOUR:O", title="Hour"),
                    alt.Tooltip("PCT_DELAYED:Q", title="% delayed"),
                    alt.Tooltip("AVG_DELAY:Q", title="Avg delay (min)"),
                    alt.Tooltip("FLIGHTS:Q", title="Flights"),
                ],
            )
        )
        st.altair_chart(heatmap, width="stretch")

    with st.container(border=True):
        st.subheader("Trend over time")
        granularity = st.radio(
            "Granularity", ["Daily", "Monthly"], horizontal=True, key="trend_granularity"
        )
        trend_df = df.copy()
        dates = pd.to_datetime(trend_df["FULL_DATE"])
        if granularity == "Monthly":
            # Samla alla datum i en månad på månadens första dag
            trend_df["PERIOD"] = dates.dt.to_period("M").dt.to_timestamp()
        else:
            trend_df["PERIOD"] = dates
        trend = kpi_table(trend_df, ["PERIOD"]).sort_values("PERIOD")
        st.line_chart(
            data=trend,
            x="PERIOD",
            y="PCT_DELAYED",
            x_label="Date",
            y_label="Delayed flights (%)",
        )


# Airports & Routes
with tab_routes:
    st.subheader("Airports & Routes")

    min_flights = st.slider(
        "Minimum number of flights",
        min_value=1,
        max_value=200,
        value=20,
        help="Hides airports/routes with too few flights to be meaningful.",
    )

    col_cfg = {
        "FLIGHTS": st.column_config.NumberColumn("Flights"),
        "DELAYED": st.column_config.NumberColumn("Delayed flights"),
        "AVG_DELAY": st.column_config.NumberColumn("Avg delay (min)", format="%.1f"),
        "PCT_DELAYED": st.column_config.ProgressColumn(
            "Delayed (%)", min_value=0, max_value=100, format="%.1f%%"
        ),
    }

    with st.container(border=True):
        st.subheader("Airport comparison")
        by_airport = kpi_table(df, ["AIRPORT"])
        by_airport = by_airport[by_airport["FLIGHTS"] >= min_flights]
        st.bar_chart(
            data=by_airport,
            x="AIRPORT",
            y="PCT_DELAYED",
            x_label="Airport",
            y_label="Delayed flights (%)",
            sort="-PCT_DELAYED",
        )

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.subheader("Most delayed routes")
            routes = kpi_table(df, ["AIRPORT", "OTHER_AIRPORT"])
            routes["ROUTE"] = routes["AIRPORT"] + " ↔ " + routes["OTHER_AIRPORT"]
            routes = routes[routes["FLIGHTS"] >= min_flights].sort_values(
                "PCT_DELAYED", ascending=False
            )
            st.dataframe(
                routes[["ROUTE", "FLIGHTS", "DELAYED", "AVG_DELAY", "PCT_DELAYED"]].head(25),
                column_config={"ROUTE": "Route", **col_cfg},
                width="stretch",
                hide_index=True,
            )

    with right:
        with st.container(border=True):
            st.subheader("Most delayed origins/destinations")
            others = kpi_table(df, ["OTHER_AIRPORT"])
            others = others[others["FLIGHTS"] >= min_flights].sort_values(
                "PCT_DELAYED", ascending=False
            )
            st.dataframe(
                others[["OTHER_AIRPORT", "FLIGHTS", "DELAYED", "AVG_DELAY", "PCT_DELAYED"]].head(25),
                column_config={"OTHER_AIRPORT": "Other airport", **col_cfg},
                width="stretch",
                hide_index=True,
            )