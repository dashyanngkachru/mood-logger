import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_autorefresh import st_autorefresh
import pytz

# Constants
COLOR_MAP = {
    "🎉": "darkgreen",
    "😊": "lightgreen",
    "😕": "lightcoral",
    "😠": "darkred"
}

# Set timezone to Pacific Time
PACIFIC = pytz.timezone("America/Los_Angeles")

# Google Sheets Setup
@st.cache_resource(show_spinner=False)
def get_sheet():
    """Authenticate and return the Google Sheet object."""
    try:
        creds_dict = json.loads(st.secrets["creds_json"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("mood_logging").sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Failed to connect to Google Sheets: {e}")
        return None


def get_data(sheet):
    """Fetch data from Google Sheet as DataFrame."""
    try:
        records = sheet.get_all_values()
        if not records or len(records) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(records[1:], columns=records[0])
        return df
    except Exception as e:
        st.error(f"Error reading data: {e}")
        return pd.DataFrame()


def log_mood(sheet, mood, note):
    """Append a new mood entry to the Google Sheet."""
    try:
        now = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, mood, note])
        return True
    except Exception as e:
        st.error(f"Error logging mood: {e}")
        return False


# UI and Logic
def handle_auto_refresh():
    """Setup auto refresh based on user selection."""
    with st.sidebar:
        st.header("🔁 Refresh settings")
        refresh_mode = st.radio("Refresh mode", ["On submission", "Interval (custom)"])

        if refresh_mode == "Interval (custom)":
            time_unit = st.selectbox("Time unit", ["Seconds", "Minutes", "Hours"])
            refresh_value = st.slider(
                f"Refresh every N {time_unit.lower()}",
                min_value=1, max_value=60, value=10, step=1
            )

            multiplier = {"Seconds": 1, "Minutes": 60, "Hours": 3600}
            interval_ms = refresh_value * multiplier[time_unit] * 1000

            st_autorefresh(interval=interval_ms, key="auto-refresh")

        return refresh_mode


def filter_data_by_date(data):
    """Filter data by user-selected date or date range."""
    st.markdown("#### 📆 Filter by Date")
    filter_type = st.radio("View by", ["Single day", "Date range"], horizontal=True)

    filtered = pd.DataFrame()
    try:
        today_pacific = datetime.now(PACIFIC).date()
        if filter_type == "Single day":
            selected_day = st.date_input("Select a date", value=today_pacific)
            filtered = data[data['timestamp'].dt.date == selected_day]
        else:
            date_range = st.date_input(
                "Select date range",
                [today_pacific - timedelta(days=7), today_pacific]
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered = data[
                    (data['timestamp'].dt.date >= start_date) &
                    (data['timestamp'].dt.date <= end_date)
                ]
            else:
                st.warning("Please select a valid date range.")
    except Exception as e:
        st.error(f"Error filtering data: {e}")

    return filtered, filter_type


def plot_mood_distribution(filtered, filter_type):
    """Create and display the mood distribution bar chart."""
    if filtered.empty:
        st.info("No mood entries for the selected date(s).")
        return

    filtered = filtered.copy()
    filtered['date'] = filtered['timestamp'].dt.date

    if filter_type == "Single day":
        mood_counts = filtered['mood'].value_counts().reset_index()
        mood_counts.columns = ['mood', 'count']
        fig = px.bar(
            mood_counts,
            x='mood',
            y='count',
            color='mood',
            color_discrete_map=COLOR_MAP,
            title="Mood Distribution"
        )
        fig.update_layout(showlegend=False)
    else:
        # Calculate grouping period based on date range length
        start_date = filtered['timestamp'].dt.date.min()
        end_date = filtered['timestamp'].dt.date.max()
        range_length = (end_date - start_date).days

        if range_length <= 14:
            filtered['period'] = filtered['timestamp'].dt.strftime('%Y-%m-%d')
            filtered['period_label'] = filtered['period']
            title_suffix = "Day"
        elif range_length <= 90:
            filtered['period'] = (
                filtered['timestamp'] - pd.to_timedelta(filtered['timestamp'].dt.weekday, unit='d')
            ).dt.strftime('%Y-%m-%d')
            filtered['period_label'] = "Week of " + filtered['period']
            title_suffix = "Week"
        elif range_length <= 365:
            filtered['period'] = filtered['timestamp'].dt.strftime('%Y-%m')
            filtered['period_label'] = pd.to_datetime(filtered['period'], format='%Y-%m').dt.strftime('%b %Y')
            title_suffix = "Month"
        else:
            filtered['period'] = filtered['timestamp'].dt.strftime('%Y')
            filtered['period_label'] = filtered['period']
            title_suffix = "Year"

        grouped = (
            filtered.groupby(['period_label', 'mood'])
            .size()
            .reset_index(name='count')
        )

        fig = px.bar(
            grouped,
            x='period_label',
            y='count',
            color='mood',
            color_discrete_map=COLOR_MAP,
            barmode='group',
            title=f"Mood Distribution by {title_suffix}"
        )
        fig.update_xaxes(title_text="period")

    st.plotly_chart(fig)


def main():
    st.set_page_config(page_title="Mood Logger", layout="centered")
    st.title("📝 Mood Logger")

    handle_auto_refresh()

    sheet = get_sheet()
    if sheet is None:
        st.stop()

    # Mood Logging
    st.subheader("Log your mood")
    mood = st.selectbox("How are you feeling?", ["😊", "😠", "😕", "🎉"])
    note = st.text_input("Optional note")
    if st.button("Submit"):
        if log_mood(sheet, mood, note):
            st.success("✅ Mood logged!")
 
    # Mood Overview
    st.subheader("📊 Mood Overview")
    data = get_data(sheet)

    if data.empty:
        st.info("No data available yet.")
        return

    # Process timestamps
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    data.dropna(subset=['timestamp'], inplace=True)

    filtered_data, filter_type = filter_data_by_date(data)
    plot_mood_distribution(filtered_data, filter_type)


if __name__ == "__main__":
    main()
