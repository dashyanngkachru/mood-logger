# Mood Logger App

## Overview
`app.py` is the main Streamlit application script for the Mood Logger internal tool. It enables users to log their mood with an optional note and visualize mood trends over different date ranges.

## Main Functions of app.py

### Mood Logging UI:
Provides a simple interface where users can select a mood emoji (e.g., 😊, 😠, 😕, 🎉) and optionally add a short note. On submission, the entry (timestamp, mood, note) is appended to a Google Sheet.

### Mood Visualization:
Displays interactive bar charts summarizing mood counts. Users can filter the data by a single day or a date range. The chart adapts its grouping and labels based on the filter duration (daily, weekly, monthly, yearly).

### Auto Refresh Options:
Offers configurable refresh modes:

1. Refresh on new mood submission.
2. Interval-based auto-refresh with selectable time units and intervals.

### Google Sheets Integration:
Connects to a Google Sheet backend via service account credentials to store and fetch mood entries. The Google Sheet can be viewed  [here](https://docs.google.com/spreadsheets/d/1-5cxvdL1IYtkm8BukR3qB5gmMIIeIfPw3nZkODu-Jog/edit?pli=1&gid=0#gid=0).
