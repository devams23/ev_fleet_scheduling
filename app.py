from pathlib import Path

import streamlit as st

from scheduler.scenario import load_scenario, Weights
from scheduler.solver import solve_schedule
from scheduler.formatting import timeline_rows, station_order_rows

SCENARIO_DIR = Path("data/scenarios")


def load_scenario_names() -> list[str]:
    return sorted(p.stem for p in SCENARIO_DIR.glob("*.json"))


st.set_page_config(page_title="EV Charging Scheduler", layout="wide")
st.title("EV Charging Scheduler")

scenario_names = load_scenario_names()
scenario_name = st.selectbox("Scenario", scenario_names)

scenario_path = SCENARIO_DIR / f"{scenario_name}.json"
scenario = load_scenario(scenario_path)

st.subheader("Scenario input")

st.write("Weights")
st.table(
    [
        {
            "individual": scenario.weights.individual,
            "operator": scenario.weights.operator,
            "overall": scenario.weights.overall,
        }
    ]
)

st.write("Parameters")
st.table(
    [
        {
            "speed_kmph": scenario.parameters.speed_kmph,
            "battery_range_km": scenario.parameters.battery_range_km,
            "charge_minutes": scenario.parameters.charge_minutes,
            "chargers_per_station": scenario.parameters.chargers_per_station,
        }
    ]
)

st.write("Route")
st.table(
    [
        {
            "from": segment.start,
            "to": segment.end,
            "distance_km": segment.distance_km,
        }
        for segment in scenario.route
    ]
)

st.write("Stations")
st.table([{"station": station} for station in scenario.stations])

st.write("Buses")
st.table(
    [
        {
            "bus_id": bus.bus_id,
            "operator": bus.operator,
            "origin": bus.origin,
            "destination": bus.destination,
            "depart_time": bus.depart_time,
        }
        for bus in scenario.buses
    ]
)

st.subheader("Weights")
individual = st.slider("Individual weight", 0.0, 5.0, float(scenario.weights.individual), 0.1)
operator = st.slider("Operator weight", 0.0, 5.0, float(scenario.weights.operator), 0.1)
overall = st.slider("Overall weight", 0.0, 5.0, float(scenario.weights.overall), 0.1)

if st.button("Run schedule"):
    weights = Weights(individual=individual, operator=operator, overall=overall)
    solution = solve_schedule(scenario, weights, time_limit_sec=5)
    st.subheader("Solver status")
    st.write(solution.status)

    st.subheader("Per-bus timeline")
    st.table(timeline_rows(solution))

    st.subheader("Per-station charging order")
    st.table(station_order_rows(solution))
