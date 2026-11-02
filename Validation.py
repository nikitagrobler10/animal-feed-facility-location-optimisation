
## Validation Functions ##

## 1. validation_report(results, scenario_name="", objective_name="")
## 2. load_validation_coordinates(coord_file="Validation_Coordinates.xlsx")
## 3. get_active_validation_links(results)
## 4. def plot_validation_solution( data, results=None, coord_file="Validation_Coordinates.xlsx", title="Validation scenario", show_distances=True, show_supplier_prices=True, figsize=(8, 5))

import pandas as pd
from docplex.mp.model import Model
import matplotlib.pyplot as plt
import numpy as np

## From Functions:
## 1. old_load_data(path)
## 2. new_solve_and_extract(mdl, vars_, data, log_output=True)

## From 

## 1. Report Results ##

def validation_report(results, scenario_name="", objective_name=""):

    if results is None:
        print("\n=== Validation Report ===")
        print("No feasible solution found.")
        return

    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)

    if scenario_name:
        print(f"Scenario : {scenario_name}")

    if objective_name:
        print(f"Objective: {objective_name}")

    print(f"\nObjective value : {results['objective_value']:,.2f}")
    print(f"Total cost      : R {results['total_cost']:,.2f}")
    print(f"Total emissions : {results['total_emissions']:,.2f} kg CO2")
    print(f"Open plants     : {', '.join(results['open_plants'])}")

    print("\n--- Cost breakdown ---")
    for name, value in results["cost_breakdown"].items():
        print(f"{name:30s}: R {value:,.2f}")

    print("\n--- Emissions breakdown ---")
    for name, value in results["emissions_breakdown"].items():
        print(f"{name:30s}: {value:,.2f} kg CO2")

    print("\n--- Production ---")
    for (p, f), val in results["production"].items():
        print(f"{p} - {f}: {val:,.2f} tonnes")

    print("\n--- Inbound flows ---")
    for (s, p, m), val in results["inbound_flows"].items():
        print(f"{s} -> {p} | {m}: {val:,.2f} tonnes")

    print("\n--- Outbound flows ---")
    for (p, b, f), val in results["outbound_flows"].items():
        print(f"{p} -> {b} | {f}: {val:,.2f} tonnes")

    print("\n--- Inbound trips ---")
    for (s, p, m, t, u), val in results["inbound_trips"].items():
        print(f"{s} -> {p} | {m} | {t} | util {u}: {val:.0f}")

    print("\n--- Outbound trips ---")
    for (p, b, f, t, u), val in results["outbound_trips"].items():
        print(f"{p} -> {b} | {f} | {t} | util {u}: {val:.0f}")


## 2. Load Validation Coordinates

def load_validation_coordinates(
    coord_file="Validation_Coordinates.xlsx",
    sheet_name="Coordinates"
):

    df = pd.read_excel(coord_file, sheet_name=sheet_name)

    required_cols = ["node_id", "node_type", "x", "y"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns in validation coordinates: {missing}")

    df["node_id"] = df["node_id"].astype(str).str.strip()
    df["node_type"] = df["node_type"].astype(str).str.strip().str.lower()

    return df

## 3. Active Links

def get_active_validation_links(results):
    active_inbound = set()
    active_outbound = set()

    for (s, p, m), flow in results.get("inbound_flows", {}).items():
        if flow > 1e-6:
            active_inbound.add((s, p))

    for (p, b, f), flow in results.get("outbound_flows", {}).items():
        if flow > 1e-6:
            active_outbound.add((p, b))

    return active_inbound, active_outbound

## 4. Plot Validation Solutions

## 4. Plot Validation Solutions

def plot_validation_solution(
    data,
    results=None,
    coord_file="Validation_Coordinates.xlsx",
    sheet_name="Coordinates",
    title="Validation scenario",
    show_distances=True,
    show_supplier_prices=True,
    show_buyer_demand=False,
    show_supplier_materials=False,
    show_plant_cost=False,
    figsize=(8, 5)
):
    import matplotlib.pyplot as plt

    coords = load_validation_coordinates(coord_file, sheet_name)
    node_lookup = coords.set_index("node_id")[["x", "y", "node_type"]].to_dict("index")

    S = data["S"]
    P = data["P"]
    B = data["B"]
    M = data["M"]
    F = data["F"]

    d_ps = data["d_ps"]
    d_pb = data["d_pb"]
    c_sm = data["c_sm"]
    c_p = data["c_p"]
    h_bf = data["h_bf"]

    if results is not None:
        active_inbound, active_outbound = get_active_validation_links(results)
        open_plants = set(results.get("open_plants", []))
    else:
        active_inbound, active_outbound = set(), set()
        open_plants = set()

    fig, ax = plt.subplots(figsize=figsize)

    # ----------------------------
    # Possible inbound links
    # ----------------------------
    for s in S:
        for p in P:
            if s not in node_lookup or p not in node_lookup:
                continue

            x1, y1 = node_lookup[s]["x"], node_lookup[s]["y"]
            x2, y2 = node_lookup[p]["x"], node_lookup[p]["y"]

            active = (s, p) in active_inbound

            ax.plot(
                [x1, x2],
                [y1, y2],
                color="green" if active else "lightgrey",
                linewidth=3 if active else 1,
                alpha=0.9 if active else 0.5,
                zorder=1
            )

            if show_distances:
                xm = (x1 + x2) / 2
                ym = (y1 + y2) / 2

                ax.text(
                    xm,
                    ym + 0.25,
                    f"{d_ps[(p, s)]:.0f}",
                    color="green",
                    fontsize=10,
                    ha="center"
                )

    # ----------------------------
    # Possible outbound links
    # ----------------------------
    for p in P:
        for b in B:
            if p not in node_lookup or b not in node_lookup:
                continue

            x1, y1 = node_lookup[p]["x"], node_lookup[p]["y"]
            x2, y2 = node_lookup[b]["x"], node_lookup[b]["y"]

            active = (p, b) in active_outbound

            ax.plot(
                [x1, x2],
                [y1, y2],
                color="red" if active else "lightgrey",
                linewidth=3 if active else 1,
                alpha=0.9 if active else 0.5,
                zorder=1
            )

            if show_distances:
                xm = (x1 + x2) / 2
                ym = (y1 + y2) / 2

                ax.text(
                    xm,
                    ym - 0.4,
                    f"{d_pb[(p, b)]:.0f}",
                    color="red",
                    fontsize=10,
                    ha="center"
                )

    # ----------------------------
    # Nodes
    # ----------------------------
    for _, row in coords.iterrows():
        node_id = row["node_id"]
        node_type = row["node_type"]

        if node_type == "supplier":
            color = "lightgreen"
            marker = "o"
        elif node_type == "plant":
            color = "lightskyblue" if node_id in open_plants else "lightgrey"
            marker = "s"
        elif node_type == "buyer":
            color = "mistyrose"
            marker = "o"
        else:
            color = "white"
            marker = "o"

        ax.scatter(
            row["x"],
            row["y"],
            s=900,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=1,
            zorder=3
        )

        ax.text(
            row["x"],
            row["y"],
            node_id,
            fontsize=12,
            ha="center",
            va="center",
            zorder=4
        )

    # ----------------------------
    # Buyer demand labels
    # ----------------------------
        if show_buyer_demand and node_type == "buyer":
            demand_text = "\n".join(
                [f"{f}: {h_bf[(node_id, f)]:.0f} t" for f in F]
            )

            ax.text(
                row["x"],
                row["y"] - 1.2,
                demand_text,
                color="black",
                fontsize=9,
                ha="center",
                zorder=5
            )

    # ----------------------------
    # Supplier material labels
    # ----------------------------
        if show_supplier_materials and node_type == "supplier":

            material_text = "\n".join(
                [f"{m}" for m in M if (node_id, m) in c_sm]
            )

            ax.text(
                row["x"] + 0.9,
                row["y"] - 0.5,
                material_text,
                color="black",
                fontsize=9,
                ha="center",
                zorder=5
            )

    # ----------------------------
    # Plant opening cost labels
    # ----------------------------
        if show_plant_cost and node_type == "plant":
    
                ax.text(
                row["x"],
                row["y"] + 0.9,
                f"Opening cost:\nR{c_p[node_id]:,.0f}",
                color="black",
                fontsize=9,
                ha="center",
                va="bottom",
                zorder=5
            )
    # ----------------------------
    # Supplier price labels
    # ----------------------------
    if show_supplier_prices:
        for s in S:
            if s not in node_lookup:
                continue

            x = node_lookup[s]["x"]
            y = node_lookup[s]["y"]

            price_text = ", ".join(
                [f"{m}: R{c_sm[(s, m)]:.0f}/t" for m in M]
            )

            ax.text(
                x,
                y + 0.45,
                price_text,
                color="black",
                fontsize=9,
                ha="center",
                zorder=5
            )

   

    # ----------------------------
    # Formatting
    # ----------------------------
    ax.set_title(title, fontsize=14, pad=25, fontfamily="serif")
    ax.axis("off")
    ax.set_aspect("equal")

    x_values = coords["x"]
    y_values = coords["y"]

    x_pad = 0.8
    y_pad = 1.0

    ax.set_xlim(x_values.min() - x_pad, x_values.max() + x_pad)
    ax.set_ylim(y_values.min() - y_pad, y_values.max() + y_pad)

    plt.tight_layout()
    plt.show()














def old_plot_validation_solution(
    data,
    results=None,
    coord_file="Validation_Coordinates.xlsx",
    sheet_name="Coordinates",
    title="Validation scenario",
    show_distances=True,
    show_supplier_prices=True,
    figsize=(8, 5)
):
    from matplotlib.lines import Line2D

    coords = load_validation_coordinates(coord_file, sheet_name)
    node_lookup = coords.set_index("node_id")[["x", "y", "node_type"]].to_dict("index")

    S = data["S"]
    P = data["P"]
    B = data["B"]

    d_ps = data["d_ps"]
    d_pb = data["d_pb"]
    c_sm = data["c_sm"]
    M = data["M"]

    if results is not None:
        active_inbound, active_outbound = get_active_validation_links(results)
        open_plants = set(results.get("open_plants", []))
    else:
        active_inbound, active_outbound = set(), set()
        open_plants = set()

    fig, ax = plt.subplots(figsize=figsize)

    # ----------------------------
    # Possible inbound links
    # ----------------------------
    for s in S:
        for p in P:
            if s not in node_lookup or p not in node_lookup:
                continue

            x1, y1 = node_lookup[s]["x"], node_lookup[s]["y"]
            x2, y2 = node_lookup[p]["x"], node_lookup[p]["y"]

            active = (s, p) in active_inbound

            ax.plot(
                [x1, x2],
                [y1, y2],
                color="green" if active else "lightgrey",
                linewidth=3 if active else 1,
                alpha=0.9 if active else 0.5,
                zorder=1
            )

            if show_distances:
                xm = (x1 + x2) / 2
                ym = (y1 + y2) / 2
                ax.text(
                    xm,
                    ym + 0.35,
                    f"{d_ps[(p, s)]:.0f}",
                    color="green",
                    fontsize=10,
                    ha="center"
                )

    # ----------------------------
    # Possible outbound links
    # ----------------------------
    for p in P:
        for b in B:
            if p not in node_lookup or b not in node_lookup:
                continue

            x1, y1 = node_lookup[p]["x"], node_lookup[p]["y"]
            x2, y2 = node_lookup[b]["x"], node_lookup[b]["y"]

            active = (p, b) in active_outbound

            ax.plot(
                [x1, x2],
                [y1, y2],
                color="red" if active else "lightgrey",
                linewidth=3 if active else 1,
                alpha=0.9 if active else 0.5,
                zorder=1
            )

            if show_distances:
                xm = (x1 + x2) / 2
                ym = (y1 + y2) / 2
                ax.text(
                    xm,
                    ym - 0.35,
                    f"{d_pb[(p, b)]:.0f}",
                    color="red",
                    fontsize=10,
                    ha="center"
                )

    # ----------------------------
    # Nodes
    # ----------------------------
    for _, row in coords.iterrows():
        node_id = row["node_id"]
        node_type = row["node_type"]

        if node_type == "supplier":
            color = "lightgreen"
            marker = "o"
        elif node_type == "plant":
            color = "lightskyblue" if node_id in open_plants else "lightgrey"
            marker = "s"
        elif node_type == "buyer":
            color = "mistyrose"
            marker = "o"
        else:
            color = "white"
            marker = "o"

        ax.scatter(
            row["x"],
            row["y"],
            s=900,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=1,
            zorder=3
        )

        ax.text(
            row["x"],
            row["y"],
            node_id,
            fontsize=12,
            ha="center",
            va="center",
            zorder=4
        )

    # ----------------------------
    # Supplier price labels
    # ----------------------------
        if show_supplier_prices:
            for s in S:
             if s not in node_lookup:
               continue
    
             x = node_lookup[s]["x"]
             y = node_lookup[s]["y"]

            price_text = ", ".join(
                [f"{m}: R{c_sm[(s, m)]:.0f}/t" for m in M]
           )

            ax.text(
                x,
                y + 0.35,
               price_text,
                color="black",
                fontsize=9,
                ha="center"
            )

    # ----------------------------
    # Formatting
    # ----------------------------
    ax.set_title(title, fontsize=14, pad=25, fontfamily="serif")
    ax.axis("off")
    ax.set_aspect("equal")

    # Add padding so nodes/text are not cut off
    x_values = coords["x"]
    y_values = coords["y"]

    x_pad = 0.8
    y_pad = 1.0

    ax.set_xlim(x_values.min() - x_pad, x_values.max() + x_pad)
    ax.set_ylim(y_values.min() - y_pad, y_values.max() + y_pad)

    plt.tight_layout()
    plt.show()
