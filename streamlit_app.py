import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from urllib.parse import unquote

# ============================================================================
# Data Loading Functions
# ============================================================================


def load_data_from_aggregation_csv(url, scenario_name):
    """
    Load data from a single aggregation CSV file.

    Expected CSV format from Firebase:
    - marketUnits050Sum: <=50% MFI units
    - marketUnits51100Sum: 51%-100% MFI units
    - marketUnits101150Sum: 101-150% MFI units
    - marketUnits151200Sum: 151-200% MFI units
    - marketUnits201250Sum: 201-250% MFI units
    - marketUnits251Sum: >251% MFI units
    - countMarket0BrSum: 0 bedroom units
    - countMarket1BrSum: 1 bedroom units
    - countMarket2BrSum: 2 bedroom units
    - countMarket3BrSum: 3+ bedroom units
    - totalUnitsSum: total units
    - affordableUnitsSum: affordable units
    - surfaceParkingStallsSum, garageParkingStallsSum, etc.
    """
    try:
        if not url:
            return None

        df = pd.read_csv(url)

        # Helper to get first row value or 0
        def get_value(column):
            if column in df.columns and len(df) > 0:
                return df[column].iloc[0]
            return 0

        # Extract income bracket data
        income_values = [
            get_value("marketUnits050Sum"),
            get_value("marketUnits51100Sum"),
            get_value("marketUnits101150Sum"),
            get_value("marketUnits151200Sum"),
            get_value("marketUnits201250Sum"),
            get_value("marketUnits251Sum"),
        ]

        total_income = sum(income_values)
        income_pct = [
            round(v / total_income * 100) if total_income > 0 else 0
            for v in income_values
        ]

        # Extract bedroom count data
        bedroom_values = [
            get_value("countMarket0BrSum"),
            get_value("countMarket1BrSum"),
            get_value("countMarket2BrSum"),
            get_value("countMarket3BrSum"),
        ]

        total_bedroom = sum(bedroom_values)
        bedroom_pct = [
            round(v / total_bedroom * 100) if total_bedroom > 0 else 0
            for v in bedroom_values
        ]

        # Extract parking data
        parking_values = [
            get_value("surfaceParkingStallsSum"),
            get_value("garageParkingStallsSum"),
            get_value("podiumParkingStallsSum"),
            get_value("structuredParkingStallsSum"),
            get_value("undergroundParkingStallsSum"),
        ]

        total_parking = sum(parking_values)
        parking_pct = [
            round(v / total_parking * 100) if total_parking > 0 else 0
            for v in parking_values
        ]

        # Get totals
        total_units = get_value("totalUnitsSum")
        affordable_units = get_value("affordableUnitsSum")

        return {
            "scenario_name": scenario_name,
            "income_values": [round(v, 1) for v in income_values],
            "income_pct": income_pct,
            "bedroom_values": [round(v, 1) for v in bedroom_values],
            "bedroom_pct": bedroom_pct,
            "parking_values": [round(v, 1) for v in parking_values],
            "parking_pct": parking_pct,
            "total_units": total_units,
            "affordable_units": affordable_units,
        }

    except Exception as e:
        st.error(f"Error loading CSV data from {url}: {e}")
        import traceback

        st.error(traceback.format_exc())
        return None


# Color schemes
total_feasibility_color = "#D66E6C"
building_type_colors = {
    "Single": "#6B9BD1",
    "Single w/ ADU": "#5DBDB4",
    "Townhomes": "#F07D4A",
    "Plexes": "#6FB573",
    "Walkups": "#F4C04E",
    "Podiums": "#D66E6C",
    "Towers": "#5A7BC4",
}

income_bracket_colors = {
    "<=50% MFI": "#5DBDB4",
    "51%-100% MFI": "#F07D4A",
    "101-150% MFI": "#6FB573",
    "151-200% MFI": "#F4C04E",
    "201-250% MFI": "#D66E6C",
    ">251% MFI": "#6B9BD1",
}

bedroom_count_colors = {
    "0 bedrooms": "#6FB573",
    "1 bedroom": "#F4C04E",
    "2 bedrooms": "#D66E6C",
    "3+ bedrooms": "#6B9BD1",
}

parking_type_colors = {
    "Surface": "#6FB573",
    "Garage": "#F4C04E",
    "Podium": "#D66E6C",
    "Structured": "#6B9BD1",
    "Underground": "#5DBDB4",
}

# ============================================================================
# Chart Functions
# ============================================================================


def create_multi_scenario_stacked_chart(all_data, categories, data_key, colors):
    """Create stacked bar chart with multiple scenarios."""
    fig = go.Figure()

    # Get scenario names
    scenario_names = [d["scenario_name"] for d in all_data]

    # Add bars for each category in normal order
    for i in range(len(categories)):
        category = categories[i]
        # Get values for this category across all scenarios
        if data_key == "income_pct":
            values = [d["income_pct"][i] for d in all_data]
        elif data_key == "bedroom_pct":
            values = [d["bedroom_pct"][i] for d in all_data]
        elif data_key == "parking_pct":
            values = [d["parking_pct"][i] for d in all_data]

        fig.add_trace(
            go.Bar(
                name=category,
                x=scenario_names,
                y=values,
                marker_color=colors[category],
                text=[f"{v}%" if v > 0 else "" for v in values],
                textposition="inside",
                textfont=dict(color="white", size=14),
                hovertemplate=f"{category}: %{{y}}%<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        barmode="stack",
        height=600,
        xaxis=dict(title="", tickfont=dict(size=14)),
        yaxis=dict(
            title="", showticklabels=False, showgrid=True, gridcolor="lightgray"
        ),
        legend=dict(
            title="",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=-0.15,
            font=dict(size=12),
            traceorder="normal",
        ),
        plot_bgcolor="white",
        margin=dict(l=0, r=20, t=30, b=30),
    )

    return fig


def create_total_feasibility_chart_grouped(scenario_names, total_data_dict, color):
    """Create grouped bar chart for total units vs affordable units."""
    fig = go.Figure()

    # Add Total Units bar
    fig.add_trace(
        go.Bar(
            name="Total Units",
            x=scenario_names,
            y=total_data_dict["Total Units"],
            marker_color=color,
            text=[f"{int(v)}" for v in total_data_dict["Total Units"]],
            textposition="inside",
            textfont=dict(color="white", size=14, weight="bold"),
            hovertemplate="Total Units: %{y}<extra></extra>",
        )
    )

    # Add Affordable Units bar with minimum display value
    max_value = max(
        max(total_data_dict["Total Units"]), max(total_data_dict["Affordable Units"])
    )
    min_display_value = max_value * 0.01

    affordable_display = [
        val if val > 0 else min_display_value for val in total_data_dict["Affordable Units"]
    ]

    fig.add_trace(
        go.Bar(
            name="Affordable Units",
            x=scenario_names,
            y=affordable_display,
            marker_color="#5DBDB4",
            text=[
                f"{int(actual)}" if actual > 0 else ""
                for actual in total_data_dict["Affordable Units"]
            ],
            textposition="inside",
            textfont=dict(color="white", size=14, weight="bold"),
            hovertemplate="Affordable Units: %{customdata}<extra></extra>",
            customdata=total_data_dict["Affordable Units"],
        )
    )

    # Update layout
    fig.update_layout(
        barmode="group",
        height=400,
        xaxis=dict(title="", tickfont=dict(size=14)),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor="lightgray",
        ),
        plot_bgcolor="white",
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


# ============================================================================
# Main Dashboard
# ============================================================================

st.set_page_config(page_title="Market-Feasible Units Dashboard", layout="wide")

# Check for CSV URL parameters
params = st.query_params

default_unzoned_url = """https://firebasestorage.googleapis.com/v0/b/mapcraftlabs.appspot.com/o/labs_data%2FStandardCalifornia%2Fsimulations%2F-OgEbfYts3K-dWHr0Shp%2Faggregations%2Ffull_aggregations.csv?alt=media&token=b1fabf4c-9dec-4a55-8136-7bf90585f5d5"""
default_zoned_url = """https://firebasestorage.googleapis.com/v0/b/mapcraftlabs.appspot.com/o/labs_data%2FStandardCalifornia%2Fsimulations%2F-OgEbczgKYktEp6MlRzz%2Faggregations%2Ffull_aggregations.csv?alt=media&token=91f1a256-394e-47cf-a7d1-2b5920bbeba4"""

# Load unzoned baseline
unzoned_csv_url = (
    unquote(params.get("unzoned_url")) if params.get("unzoned_url") else default_unzoned_url
)

# Load multiple zoned scenarios
zoned_scenarios = []
for i in range(1, 10):  # Support up to 9 scenarios
    url_key = f"zoned_url_{i}"
    url = params.get(url_key)
    if url:
        url = unquote(url)
    elif not url and i < 3:
        url = default_zoned_url
    if url:
        zoned_scenarios.append({"url": url, "name": f"Scenario {i}"})

# Validate we have at least one URL
if not unzoned_csv_url and not zoned_scenarios:
    st.error(
        "Data not found. Please provide 'unzoned_url' and/or 'zoned_url' query parameters."
    )
    st.info(
        "Example: ?unzoned_url=https://example.com/unzoned.csv&zoned_url_1=https://example.com/zoned1.csv&zoned_url_2=https://example.com/zoned2.csv"
    )
    st.stop()

# Load all data
all_data = []

# Load unzoned baseline first (will be leftmost in charts)
if unzoned_csv_url:
    unzoned_data = load_data_from_aggregation_csv(unzoned_csv_url, "Unzoned")
    if unzoned_data:
        all_data.append(unzoned_data)

# Load all zoned scenarios
for scenario in zoned_scenarios:
    scenario_data = load_data_from_aggregation_csv(scenario["url"], scenario["name"])
    if scenario_data:
        all_data.append(scenario_data)

# Check if we successfully loaded any data
if not all_data:
    st.error("Failed to load any data. Please check the URLs and try again.")
    st.stop()

# Define category labels
income_brackets = [
    "<=50% MFI",
    "51%-100% MFI",
    "101-150% MFI",
    "151-200% MFI",
    "201-250% MFI",
    ">251% MFI",
]
bedroom_counts = ["0 bedrooms", "1 bedroom", "2 bedrooms", "3+ bedrooms"]
parking_types = ["Surface", "Garage", "Podium", "Structured", "Underground"]

# Define category labels
income_brackets = [
    "<=50% MFI",
    "51%-100% MFI",
    "101-150% MFI",
    "151-200% MFI",
    "201-250% MFI",
    ">251% MFI",
]
bedroom_counts = ["0 bedrooms", "1 bedroom", "2 bedrooms", "3+ bedrooms"]
parking_types = ["Surface", "Garage", "Podium", "Structured", "Underground"]

# Chart 1: Total Feasibility
st.title("Market-Feasible Units Dashboard")
total_data_dict = {"Total Units": [], "Affordable Units": []}
scenario_names = []
for data in all_data:
    scenario_names.append(data["scenario_name"])
    total_data_dict["Total Units"].append(data["total_units"])
    total_data_dict["Affordable Units"].append(data["affordable_units"])

df_total = pd.DataFrame(total_data_dict, index=scenario_names)

# Create grouped bar chart for total feasibility
fig_total = create_total_feasibility_chart_grouped(scenario_names, total_data_dict, total_feasibility_color)

st.plotly_chart(fig_total, use_container_width=True)
st.subheader("Feasibility Data")
st.dataframe(df_total.T, use_container_width=True)

st.markdown("---")

# Chart 3: Income Brackets
st.title("Market-feasible units affordable to different income brackets")
income_data_values = {bracket: [] for bracket in income_brackets}
income_data_pct = {bracket: [] for bracket in income_brackets}
for data in all_data:
    for i, bracket in enumerate(income_brackets):
        income_data_values[bracket].append(data["income_values"][i])
        income_data_pct[bracket].append(data["income_pct"][i])

# Create dataframe for display (actual values)
df_income = pd.DataFrame(income_data_values, index=scenario_names)
fig_income = create_multi_scenario_stacked_chart(
    all_data, income_brackets, "income_pct", income_bracket_colors
)
st.plotly_chart(fig_income, use_container_width=True)
st.subheader("Income Bracket Data")
st.dataframe(df_income.T, use_container_width=True)

st.markdown("---")

# Chart 4: Bedroom Counts
st.title("Market-feasible units by bedroom count")
bedroom_data_values = {count: [] for count in bedroom_counts}
bedroom_data_pct = {count: [] for count in bedroom_counts}
for data in all_data:
    for i, count in enumerate(bedroom_counts):
        bedroom_data_values[count].append(data["bedroom_values"][i])
        bedroom_data_pct[count].append(data["bedroom_pct"][i])

df_bedrooms = pd.DataFrame(bedroom_data_values, index=scenario_names)
fig_bedrooms = create_multi_scenario_stacked_chart(
    all_data, bedroom_counts, "bedroom_pct", bedroom_count_colors
)
st.plotly_chart(fig_bedrooms, use_container_width=True)
st.subheader("Bedroom Count Data")
st.dataframe(df_bedrooms.T, use_container_width=True)

st.markdown("---")

# Chart 5: Parking Types
st.title("Parking stalls by type")
parking_data_values = {ptype: [] for ptype in parking_types}
parking_data_pct = {ptype: [] for ptype in parking_types}
for data in all_data:
    for i, ptype in enumerate(parking_types):
        parking_data_values[ptype].append(data["parking_values"][i])
        parking_data_pct[ptype].append(data["parking_pct"][i])

df_parking = pd.DataFrame(parking_data_values, index=scenario_names)
fig_parking = create_multi_scenario_stacked_chart(
    all_data, parking_types, "parking_pct", parking_type_colors
)
st.plotly_chart(fig_parking, use_container_width=True)
st.subheader("Parking Data")
st.dataframe(df_parking.T, use_container_width=True)
