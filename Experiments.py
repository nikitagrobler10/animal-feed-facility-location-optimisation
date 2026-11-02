
## Experiment Functions ##

## 1. Experiment Report: def experiment_report(results, mdl, experiment_id="", scenario_name="", objective_name="")

## 2. Plot experiment solution: def plot_exp_solution()

## 3. Pareto Experiment
## 3.1. Pareto Table: def pareto_table(data, min_cost_results, min_emissions_results, experiment_id, n_points=21, mip_gap=0.001, time_limit=900)
## 3.2. Pareto Plot: def plot_pareto(pareto_table, figsize=(10, 7), label_points=True, show_title=True)
## 3.3. Pareto Plot def pareto_plot(pareto_table, figsize=(10, 7), label_points=True, show_title=True)
## 3.4 Target Emissions Reduction Analysis: def target_reduction_results(data, min_cost_results, experiment_id, reduction_targets=(1, 2, 3, 4), mip_gap=0.001, time_limit=60):

## 4. Sensitivity Analysis
## 4.1. Vary buyer demand: def vary_buyer_demand(data, buyers, factor)
## 4.2. Vary plant capacity: def vary_plant_capacity(data, plants, factor)
## 4.3. Vary transport cost: def vary_transport_cost(data, factor)
## 4.4. Vary transport emission factors: def vary_transport_emission_factor(data, factor)

## 5. Stress test
## 5.1 Stress test report: def stress_test_report( results, mdl, experiment_id="", scenario_name="", objective_name="")




import pandas as pd
from docplex.mp.model import Model
import matplotlib.pyplot as plt
import numpy as np

## 1. Experiment Report

def experiment_report(
    results,
    mdl,
    experiment_id="",
    scenario_name="",
    objective_name=""
):

    if results is None:
        print("\n=== Experiment Report ===")
        print("No feasible solution found.")
        return

    print("\n" + "=" * 60)
    print("EXPERIMENT REPORT")
    print("=" * 60)

    # --------------------------------------------------
    # Experiment information
    # --------------------------------------------------
    if experiment_id:
        print(f"Experiment : {experiment_id}")

    if scenario_name:
        print(f"Scenario   : {scenario_name}")

    if objective_name:
        print(f"Objective  : {objective_name}")

    # --------------------------------------------------
    # Main results
    # --------------------------------------------------
    print(f"\nObjective value : {results['objective_value']:,.2f}")
    print(f"Total cost      : R {results['total_cost']:,.2f}")
    print(f"Total emissions : {results['total_emissions']:,.2f} kg CO2")
    print(f"Open plants     : {', '.join(results['open_plants'])}")

    # --------------------------------------------------
    # Cost breakdown
    # --------------------------------------------------
    print("\n--- Cost breakdown ---")

    for name, value in results["cost_breakdown"].items():
        print(f"{name:30s}: R {value:,.2f}")

    # --------------------------------------------------
    # Emissions breakdown
    # --------------------------------------------------
    print("\n--- Emissions breakdown ---")

    for name, value in results["emissions_breakdown"].items():
        print(f"{name:30s}: {value:,.2f} kg CO2")

    # --------------------------------------------------
    # Production
    # --------------------------------------------------
    print("\n--- Production ---")

    for (p, f), val in results["production"].items():
        print(f"{p} - {f}: {val:,.2f} tonnes")

    # --------------------------------------------------
    # Inbound flows
    # --------------------------------------------------
    print("\n--- Inbound flows ---")

    for (s, p, m), val in results["inbound_flows"].items():
        print(f"{s} -> {p} | {m}: {val:,.2f} tonnes")

    # --------------------------------------------------
    # Outbound flows
    # --------------------------------------------------
    print("\n--- Outbound flows ---")

    for (p, b, f), val in results["outbound_flows"].items():
        print(f"{p} -> {b} | {f}: {val:,.2f} tonnes")

    # --------------------------------------------------
    # Inbound trips
    # --------------------------------------------------
    print("\n--- Inbound trips ---")

    for (s, p, m, t, u), val in results["inbound_trips"].items():
        print(
            f"{s} -> {p} | {m} | {t} | util {u}: "
            f"{val:.0f}"
        )

    # --------------------------------------------------
    # Outbound trips
    # --------------------------------------------------
    print("\n--- Outbound trips ---")

    for (p, b, f, t, u), val in results["outbound_trips"].items():
        print(
            f"{p} -> {b} | {f} | {t} | util {u}: "
            f"{val:.0f}"
        )

    # --------------------------------------------------
    # Run statistics
    # --------------------------------------------------
    print("\n--- Run statistics ---")

    solve_details = mdl.solve_details

    print(f"Solve status        : {solve_details.status}")
    print(f"Solve time          : {solve_details.time:.2f} s")
    print(f"MIP gap             : {solve_details.mip_relative_gap:.6f}")
    print(f"Number of variables : {mdl.number_of_variables}")
    print(f"Number of constraints: {mdl.number_of_constraints}")

    # Variable-type counts
    number_of_binaries = sum(
        1 for var in mdl.iter_variables()
        if var.is_binary()
    )

    number_of_integers = sum(
        1 for var in mdl.iter_variables()
        if var.is_integer() and not var.is_binary()
    )

    print(f"Number of binaries  : {number_of_binaries}")
    print(f"Number of integers  : {number_of_integers}")














## 2. Plot experiment solution 

def plot_exp_solution(
    results,
    data,
    coord_file="Master_Coordinates.xlsx",
    figsize=(15, 13),
    label_nodes=True,
    show_title=True,
    show_legend=True,
):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    import Functions

    # --------------------------------------------------
    # Formatting: LaTeX-style font
    # --------------------------------------------------

    plt.rcParams["font.family"] = "serif"
    #plt.rcParams["font.serif"] = ["CMU Serif"]



    # --------------------------------------------------
    # Load full coordinate file
    # --------------------------------------------------
    nodes = Functions.load_node_coordinates(coord_file)

    # --------------------------------------------------
    # Keep only nodes included in this experiment
    # --------------------------------------------------
    experiment_nodes = (
        set(data["S"]) |
        set(data["P"]) |
        set(data["B"])
    )

    nodes = nodes[
        nodes["node_id"].isin(experiment_nodes)
    ].copy()

    # --------------------------------------------------
    # Aggregate solution flows
    # --------------------------------------------------
    inbound_agg, outbound_agg, active_suppliers, active_plants = (
        Functions.aggregate_flows(results)
    )

    node_lookup = nodes.set_index("node_id")[
        ["x", "y", "node_type", "plot_marker"]
    ].to_dict("index")

    fig, ax = plt.subplots(figsize=figsize)

    # --------------------------------------------------
    # Flow scaling
    # --------------------------------------------------
    all_flow_values = (
        list(inbound_agg.values()) +
        list(outbound_agg.values())
    )

    if all_flow_values:
        min_trips = min(all_flow_values)
        max_trips = max(all_flow_values)
    else:
        min_trips = max_trips = 0

    # --------------------------------------------------
    # Inbound flows: suppliers -> plants
    # --------------------------------------------------
    for (s, p), trips in inbound_agg.items():

        if s not in node_lookup or p not in node_lookup:
            continue

        x1, y1 = node_lookup[s]["x"], node_lookup[s]["y"]
        x2, y2 = node_lookup[p]["x"], node_lookup[p]["y"]

        lw = Functions.get_linewidth(
            trips,
            min_trips,
            max_trips
        )

        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="-",
            linewidth=lw,
            color="green",
            alpha=0.75,
            zorder=1,
        )

    # --------------------------------------------------
    # Outbound flows: plants -> buyers
    # --------------------------------------------------
    for (p, b), trips in outbound_agg.items():

        if p not in node_lookup or b not in node_lookup:
            continue

        x1, y1 = node_lookup[p]["x"], node_lookup[p]["y"]
        x2, y2 = node_lookup[b]["x"], node_lookup[b]["y"]

        lw = Functions.get_linewidth(
            trips,
            min_trips,
            max_trips
        )

        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="-",
            linewidth=lw,
            color="red",
            alpha=0.75,
            zorder=1,
        )

    # --------------------------------------------------
    # Nodes
    #
    # Show all suppliers and plants included in the
    # experiment. Buyers are shown if they receive flow.
    # --------------------------------------------------
    active_buyers = {
        b for (p, b) in outbound_agg.keys()
    }

    # Plot suppliers first, buyers second, plants last
    plot_order = {
        "supplier": 1,
        "buyer": 2,
        "plant": 3
    }

    nodes_plot = nodes.copy()

    nodes_plot["plot_order"] = (
        nodes_plot["node_type"].map(plot_order)
    )

    nodes_plot = nodes_plot.sort_values("plot_order")

    for _, row in nodes_plot.iterrows():

        node_id = row["node_id"]
        node_type = row["node_type"]

        # Skip unused buyers only
        if (
            node_type == "buyer"
            and node_id not in active_buyers
        ):
            continue

        x = row["x"]
        y = row["y"]

        if node_type == "supplier":

            color = (
                "lightgreen"
                if node_id in active_suppliers
                else "lightgrey"
            )

            marker = "o"
            z = 3

        elif node_type == "buyer":

            color = "mistyrose"
            marker = "o"
            z = 4

        elif node_type == "plant":

            color = (
                "lightskyblue"
                if node_id in active_plants
                else "lightgrey"
            )

            marker = "s"
            z = 6

        else:

            color = "white"
            marker = "o"
            z = 3

        ax.scatter(
            x,
            y,
            s=900,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=1.2,
            zorder=z,
        )

        if label_nodes:

            ax.text(
                x,
                y,
                node_id,
                fontsize=11,
                ha="center",
                va="center",
                zorder=z + 1,
            )

    # --------------------------------------------------
    # Title
    # --------------------------------------------------
    if show_title:

        cost_million = results["total_cost"] / 1e6
        emissions = results["total_emissions"]

        objective_text = (
            "Minimise Cost"
            if abs(
                results["objective_value"]
                - results["total_cost"]
            ) < 1e-6
            else "Minimise Emissions"
        )

        ax.set_title(
            f"Objective: {objective_text}\n"
            f"Cost = R{cost_million:.2f} million | "
            f"Emissions = {emissions:,.0f} kg CO$_2$",
            fontsize=14,
            pad=20,
            fontfamily="serif",
        )

    # --------------------------------------------------
    # Map-style formatting
    # --------------------------------------------------
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, pos: f"{x:.0f}")
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: f"{y:.0f}")
    )

    ax.set_aspect(
        "equal",
        adjustable="datalim"
    )

    ax.grid(
        True,
        linestyle=":",
        linewidth=0.5,
        alpha=0.5
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --------------------------------------------------
    # Legend
    # --------------------------------------------------
    if show_legend:

        legend_items = [

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Active supplier",
                markerfacecolor="lightgreen",
                markeredgecolor="black",
                markersize=12
            ),

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Inactive supplier",
                markerfacecolor="lightgrey",
                markeredgecolor="black",
                markersize=12
            ),

            Line2D(
                [0], [0],
                marker="s",
                color="w",
                label="Active plant",
                markerfacecolor="lightskyblue",
                markeredgecolor="black",
                markersize=12
            ),

            Line2D(
                [0], [0],
                marker="s",
                color="w",
                label="Inactive plant",
                markerfacecolor="lightgrey",
                markeredgecolor="black",
                markersize=12
            ),

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Buyer",
                markerfacecolor="mistyrose",
                markeredgecolor="black",
                markersize=12
            ),

            Line2D(
                [0], [0],
                color="green",
                lw=2,
                linestyle="-",
                label="Inbound flow"
            ),

            Line2D(
                [0], [0],
                color="red",
                lw=2,
                linestyle="-",
                label="Outbound flow"
            ),
        ]

        ax.legend(
            handles=legend_items,
            loc="upper left",
            bbox_to_anchor=(1, 1)
        )

    plt.tight_layout()
    plt.show()








## 3. Pareto Experiment

## 3.1. Pareto Table

def pareto_table(
    data,
    min_cost_results,
    min_emissions_results,
    experiment_id,
    n_points=21,
    mip_gap=0.001,
    time_limit=900
):

    import numpy as np
    import pandas as pd
    import Functions

    # --------------------------------------------------
    # Establish epsilon range from objective extremes
    # --------------------------------------------------

    epsilon_max = min_cost_results["total_emissions"]
    epsilon_min = min_emissions_results["total_emissions"]

    # Start at the relaxed emissions cap and progressively
    # tighten towards the minimum-emissions extreme
    epsilon_values = np.linspace(
        epsilon_max,
        epsilon_min,
        n_points
    )

    # --------------------------------------------------
    # Storage
    # --------------------------------------------------

    all_results = {}
    pareto_records = []

    # --------------------------------------------------
    # Run epsilon-constraint models
    # --------------------------------------------------

    for i, epsilon in enumerate(epsilon_values, start=1):

        run_id = f"{experiment_id}.{i:02d}"

        print("\n" + "=" * 60)
        print(f"Running {run_id}")
        print(f"Emissions cap: {epsilon:,.2f} kg CO2")
        print("=" * 60)

        # --------------------------------------------------
        # Build model
        # --------------------------------------------------

        mdl, vars_ = Functions.build_model(
            data,
            objective="cost",
            emissions_cap=float(epsilon)
        )

        # --------------------------------------------------
        # Solver settings
        # --------------------------------------------------

        mdl.parameters.mip.tolerances.mipgap = mip_gap
        mdl.parameters.timelimit = time_limit

        # --------------------------------------------------
        # Solve and extract results
        # --------------------------------------------------

        results = Functions.solve_and_extract(
            mdl,
            vars_,
            data,
            log_output=True
        )

        solve_details = mdl.solve_details

        # --------------------------------------------------
        # Model statistics
        # --------------------------------------------------

        number_of_binaries = sum(
            1 for var in mdl.iter_variables()
            if var.is_binary()
        )

        number_of_integers = sum(
            1 for var in mdl.iter_variables()
            if var.is_integer() and not var.is_binary()
        )

        # --------------------------------------------------
        # Store complete run
        # --------------------------------------------------

        all_results[run_id] = {
            "epsilon": float(epsilon),
            "results": results,
            "solve_status": solve_details.status,
            "solve_time": solve_details.time,
            "mip_gap": solve_details.mip_relative_gap,
            "number_of_variables": mdl.number_of_variables,
            "number_of_constraints": mdl.number_of_constraints,
            "number_of_binaries": number_of_binaries,
            "number_of_integers": number_of_integers,
        }

        # --------------------------------------------------
        # Compact Pareto record
        # --------------------------------------------------

        if results is not None:

            pareto_records.append({
                "run_id": run_id,
                "epsilon": float(epsilon),
                "total_cost": results["total_cost"],
                "total_emissions": results["total_emissions"],
                "open_plants": ", ".join(results["open_plants"]),
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
                "number_of_variables": mdl.number_of_variables,
                "number_of_constraints": mdl.number_of_constraints,
                "number_of_binaries": number_of_binaries,
                "number_of_integers": number_of_integers,
            })

        else:

            pareto_records.append({
                "run_id": run_id,
                "epsilon": float(epsilon),
                "total_cost": np.nan,
                "total_emissions": np.nan,
                "open_plants": "",
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
                "number_of_variables": mdl.number_of_variables,
                "number_of_constraints": mdl.number_of_constraints,
                "number_of_binaries": number_of_binaries,
                "number_of_integers": number_of_integers,
            })

    # --------------------------------------------------
    # Create Pareto summary table
    # --------------------------------------------------

    pareto_summary = pd.DataFrame(pareto_records)

    return all_results, pareto_summary



## 3. Pareto Experiment

## 3.1 Pareto Results

def pareto_results(
    data,
    min_cost_results,
    min_emissions_results,
    experiment_id,
    n_points=21,
    mip_gap=0.001,
    time_limit=900
):

    import numpy as np
    import pandas as pd
    import Functions
    from IPython.display import display

    # --------------------------------------------------
    # Establish epsilon range
    # --------------------------------------------------

    epsilon_max = min_cost_results["total_emissions"]
    epsilon_min = min_emissions_results["total_emissions"]

    epsilon_values = np.linspace(
        epsilon_max,
        epsilon_min,
        n_points
    )

    # --------------------------------------------------
    # Storage
    # --------------------------------------------------

    all_results = {}
    pareto_records = []

    # --------------------------------------------------
    # Run epsilon-constraint models
    # --------------------------------------------------

    for i, epsilon in enumerate(epsilon_values, start=1):

        run_id = f"{experiment_id}.{i:02d}"

        # Progress only
        print(
            f"Running {run_id} of {experiment_id}.{n_points:02d} "
            f"| Emissions cap: {epsilon:,.2f} kg CO2"
        )

        # Build model
        mdl, vars_ = Functions.build_model(
            data,
            objective="cost",
            emissions_cap=float(epsilon)
        )

        # Solver settings
        mdl.parameters.mip.tolerances.mipgap = mip_gap
        mdl.parameters.timelimit = time_limit

        # Solve and extract — CPLEX log suppressed
        results = Functions.solve_and_extract(
            mdl,
            vars_,
            data,
            log_output=False
        )

        solve_details = mdl.solve_details

        # Model statistics
        number_of_binaries = sum(
            1 for var in mdl.iter_variables()
            if var.is_binary()
        )

        number_of_integers = sum(
            1 for var in mdl.iter_variables()
            if var.is_integer() and not var.is_binary()
        )

        # Store complete run
        all_results[run_id] = {
            "epsilon": float(epsilon),
            "results": results,
            "solve_status": solve_details.status,
            "solve_time": solve_details.time,
            "mip_gap": solve_details.mip_relative_gap,
            "number_of_variables": mdl.number_of_variables,
            "number_of_constraints": mdl.number_of_constraints,
            "number_of_binaries": number_of_binaries,
            "number_of_integers": number_of_integers,
        }

        # Store summary record
        if results is not None:

            pareto_records.append({
                "run_id": run_id,
                "epsilon": float(epsilon),
                "total_cost": results["total_cost"],
                "total_emissions": results["total_emissions"],
                "open_plants": ", ".join(results["open_plants"]),
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
                "number_of_variables": mdl.number_of_variables,
                "number_of_constraints": mdl.number_of_constraints,
                "number_of_binaries": number_of_binaries,
                "number_of_integers": number_of_integers,
            })

        else:

            pareto_records.append({
                "run_id": run_id,
                "epsilon": float(epsilon),
                "total_cost": np.nan,
                "total_emissions": np.nan,
                "open_plants": "",
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
                "number_of_variables": mdl.number_of_variables,
                "number_of_constraints": mdl.number_of_constraints,
                "number_of_binaries": number_of_binaries,
                "number_of_integers": number_of_integers,
            })

    # --------------------------------------------------
    # Create and display results DataFrame
    # --------------------------------------------------

    pareto_summary = pd.DataFrame(pareto_records)

    print("\nPareto experiment complete.\n")
    display(pareto_summary)

    return all_results, pareto_summary




## 3.2 Pareto Table

def pareto_table(pareto_summary):

    import pandas as pd
    from IPython.display import display

    # --------------------------------------------------
    # Select plotted Pareto values
    # --------------------------------------------------

    table = pareto_summary[
        [
            "run_id",
            "total_emissions",
            "total_cost"
        ]
    ].copy()

    # --------------------------------------------------
    # Rename columns for display
    # --------------------------------------------------

    table.columns = [
        "Point",
        "Total emissions (kg CO2)",
        "Total cost (R)"
    ]

    # --------------------------------------------------
    # Display table
    # --------------------------------------------------

    display_table = table.copy()

    display_table["Total emissions (kg CO2)"] = (
        display_table["Total emissions (kg CO2)"]
        .map(lambda x: f"{x:,.2f}")
    )

    display_table["Total cost (R)"] = (
        display_table["Total cost (R)"]
        .map(lambda x: f"{x:,.2f}")
    )

    display(display_table)

    return table







## 3.3. Pareto Plot

def pareto_plot(
    pareto_table,
    figsize=(10, 7),
    label_points=True,
    show_title=True
):

    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    # --------------------------------------------------
    # Formatting: LaTeX-style font
    # --------------------------------------------------

    plt.rcParams["font.family"] = "serif"

    # --------------------------------------------------
    # Keep successful Pareto runs only
    # --------------------------------------------------

    plot_data = pareto_table.dropna(
        subset=["total_cost", "total_emissions"]
    ).copy()

    # --------------------------------------------------
    # Create figure
    # --------------------------------------------------

    fig, ax = plt.subplots(figsize=figsize)

    # --------------------------------------------------
    # Plot Pareto frontier
    # --------------------------------------------------

    ax.scatter(
        plot_data["total_emissions"],
        plot_data["total_cost"],
        color="black",
        s=30
    )

    # --------------------------------------------------
    # Point labels
    # --------------------------------------------------

    if label_points:

        for _, row in plot_data.iterrows():

            ax.annotate(
                row["run_id"],
                (
                    row["total_emissions"],
                    row["total_cost"]
                ),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8
            )

    # --------------------------------------------------
    # Axis formatting
    # --------------------------------------------------

    ax.set_xlabel("Total emissions (kg CO$_2$)")
    ax.set_ylabel("Total cost (R)")

    ax.xaxis.set_major_formatter(
        FuncFormatter(
            lambda x, pos: f"{x / 1e6:.2f}M"
        )
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(
            lambda y, pos: f"R{y / 1e9:.2f}bn"
        )
    )

    # --------------------------------------------------
    # Title
    # --------------------------------------------------

    if show_title:

        ax.set_title(
            "Cost vs Emissions Pareto frontier",
            fontsize=14,
            pad=15
        )

    # --------------------------------------------------
    # Formatting
    # --------------------------------------------------

    ax.grid(
        True,
        linestyle=":",
        linewidth=0.5,
        alpha=0.5
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.show()

    return fig, ax

## 3.4 Target Emissions Reduction Analysis

def target_reduction_results(
    data,
    min_cost_results,
    experiment_id,
    reduction_targets=(1, 2, 3, 4),
    mip_gap=0.001,
    time_limit=60
):

    import pandas as pd
    import Functions
    from IPython.display import display

    # --------------------------------------------------
    # Baseline values
    # --------------------------------------------------

    baseline_emissions = min_cost_results["total_emissions"]
    baseline_cost = min_cost_results["total_cost"]

    # --------------------------------------------------
    # Storage
    # --------------------------------------------------

    all_results = {}
    records = []

    # --------------------------------------------------
    # Run target emissions reductions
    # --------------------------------------------------

    for reduction in reduction_targets:

        run_id = f"{experiment_id}.{reduction}%"

        emissions_cap = baseline_emissions * (
            1 - reduction / 100
        )

        print(
            f"Running {run_id} "
            f"| Emissions reduction: {reduction}% "
            f"| Emissions cap: {emissions_cap:,.2f} kg CO2"
        )

        # Build model
        mdl, vars_ = Functions.build_model(
            data,
            objective="cost",
            emissions_cap=float(emissions_cap)
        )

        # Solver settings
        mdl.parameters.mip.tolerances.mipgap = mip_gap
        mdl.parameters.timelimit = time_limit

        # Solve
        results = Functions.solve_and_extract(
            mdl,
            vars_,
            data,
            log_output=False
        )

        solve_details = mdl.solve_details

        # --------------------------------------------------
        # Store results
        # --------------------------------------------------

        if results is not None:

            actual_emissions_reduction = (
                (baseline_emissions - results["total_emissions"])
                / baseline_emissions
                * 100
            )

            cost_increase = (
                (results["total_cost"] - baseline_cost)
                / baseline_cost
                * 100
            )

            all_results[run_id] = {
                "reduction_target": reduction,
                "emissions_cap": emissions_cap,
                "results": results,
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
            }

            records.append({
                "run_id": run_id,
                "reduction_target": reduction,
                "emissions_cap": emissions_cap,
                "total_emissions": results["total_emissions"],
                "actual_emissions_reduction": actual_emissions_reduction,
                "total_cost": results["total_cost"],
                "cost_increase": cost_increase,
                "open_plants": ", ".join(results["open_plants"]),
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
            })

        else:

            all_results[run_id] = {
                "reduction_target": reduction,
                "emissions_cap": emissions_cap,
                "results": None,
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
            }

            records.append({
                "run_id": run_id,
                "reduction_target": reduction,
                "emissions_cap": emissions_cap,
                "total_emissions": None,
                "actual_emissions_reduction": None,
                "total_cost": None,
                "cost_increase": None,
                "open_plants": "",
                "solve_status": solve_details.status,
                "solve_time": solve_details.time,
                "mip_gap": solve_details.mip_relative_gap,
            })

    # Create results table

    summary = pd.DataFrame(records)

    print("\nTarget emissions reduction analysis complete.\n")
    display(summary)

    return all_results, summary



## 4. Sensitivity Analysis

## 4.1. Vary buyer demand 
import copy

def vary_buyer_demand(data, buyers, factor):
    data_new = copy.deepcopy(data)

    for b in buyers:
        for f in data_new["F"]:
            data_new["h_bf"][b, f] *= factor

    return data_new

## 4.2. Vary plant capacity
import copy

def vary_plant_capacity(data, plants, factor):
    data_new = copy.deepcopy(data)

    for p in plants:
        for f in data_new["F"]:
            data_new["a_pf"][p, f] *= factor

    return data_new

## 4.3. Vary transport cost
import copy

def vary_transport_cost(data, factor):
    data_new = copy.deepcopy(data)

    for t in data_new["T"]:
        data_new["c_t"][t] *= factor

    return data_new


## 4.4. Vary transport emission factors
import copy

def vary_transport_emission_factor(data, factor):
    data_new = copy.deepcopy(data)

    for t in data_new["T"]:
        for u in data_new["U"]:
            data_new["e_tu"][t, u] *= factor

    return data_new

## 4.5. Vary plant emission factors

import copy

def vary_plant_emissions(data, factor):
    data_new = copy.deepcopy(data)

    for p in data_new["P"]:
        for f in data_new["F"]:
            data_new["e_pf"][p, f] *= factor

    return data_new


## 4.6. Vary supplier raw-material availability

import copy

def vary_supplier_capacity(data, suppliers, factor):
    data_new = copy.deepcopy(data)

    for s in suppliers:
        for m in data_new["M"]:
            if (s, m) in data_new["a_sm"]:
                data_new["a_sm"][s, m] *= factor

    return data_new








## 5. Stress Test 

## 5.1 Stress test report

def stress_test_report(
    results,
    mdl,
    experiment_id="",
    scenario_name="",
    objective_name=""
):

    print("\n" + "=" * 60)
    print("STRESS TEST REPORT")
    print("=" * 60)

    if experiment_id:
        print(f"Experiment : {experiment_id}")

    if scenario_name:
        print(f"Scenario   : {scenario_name}")

    if objective_name:
        print(f"Objective  : {objective_name}")

    # Model size
    print("\n--- Model size ---")

    print(f"Number of variables   : {mdl.number_of_variables:,}")
    print(f"Number of constraints : {mdl.number_of_constraints:,}")
    print(f"Number of binaries    : {mdl.number_of_binary_variables:,}")
    print(f"Number of integers    : {mdl.number_of_integer_variables:,}")

    # Solve statistics
    details = mdl.solve_details

    print("\n--- Solve statistics ---")
    print(f"Solve status : {details.status}")
    print(f"Solve time   : {details.time:.2f} s")
    print(f"MIP gap      : {details.mip_relative_gap:.6f}")

    # Solution
    print("\n--- Solution ---")

    if results is None:
        print("No feasible solution returned.")
        return

    print(f"Objective value : {results['objective_value']:,.2f}")
    print(f"Total cost      : R {results['total_cost']:,.2f}")
    print(f"Total emissions : {results['total_emissions']:,.2f} kg CO2")
    print(f"Open plants     : {len(results['open_plants'])}")


# 5.2 Run E12 stress-test experiment

def run_E12(
    master_data,
    scenario_id,
    nS,
    nP,
    nB,
    objective,
    time_limit=3600,
    mip_gap=0.001
):
    import Functions
    import gc

    objective_name = {
        "cost": "Min-Cost",
        "emissions": "Min-Emissions"
    }[objective]

    scenario_name = (
        f"{nS} suppliers / {nP} plants / {nB} buyers"
    )

    print("\n" + "=" * 60)
    print(f"{scenario_id} – {scenario_name}")
    print(f"Objective: {objective_name}")
    print("=" * 60)

    # Build dataset
    data = Functions.build_experiment_data(
        master_data,
        suppliers=[f"S{i}" for i in range(1, nS + 1)],
        plants=[f"P{i}" for i in range(1, nP + 1)],
        buyers=[f"B{i}" for i in range(1, nB + 1)],
        materials=[f"M{i}" for i in range(1, 11)],
        feeds=[f"F{i}" for i in range(1, 7)],
        trucks=[f"T{i}" for i in range(1, 6)]
    )

    # Build model
    mdl, model_vars = Functions.build_model(
        data,
        objective=objective
    )

    mdl.parameters.timelimit = time_limit
    mdl.parameters.mip.tolerances.mipgap = mip_gap

    try:
        # Solve
        results = Functions.solve_and_extract(
            mdl,
            model_vars,
            data,
            log_output=True
        )

        # Print report
        stress_test_report(
            results,
            mdl,
            experiment_id=scenario_id,
            scenario_name=scenario_name,
            objective_name=objective_name
        )

        return results

    finally:
        mdl.end()
        del mdl, model_vars, data
        gc.collect()







def old_stress_test_report(
    results,
    mdl,
    experiment_id="",
    scenario_name="",
    objective_name=""
):

    print("\n" + "=" * 60)
    print("STRESS TEST REPORT")
    print("=" * 60)

    # --------------------------------------------------
    # Experiment information
    # --------------------------------------------------
    if experiment_id:
        print(f"Experiment : {experiment_id}")

    if scenario_name:
        print(f"Scenario   : {scenario_name}")

    if objective_name:
        print(f"Objective  : {objective_name}")

    # --------------------------------------------------
    # Model size
    # --------------------------------------------------
    number_of_binaries = sum(
        1 for var in mdl.iter_variables()
        if var.is_binary()
    )

    number_of_integers = sum(
        1 for var in mdl.iter_variables()
        if var.is_integer() and not var.is_binary()
    )

    print("\n--- Model size ---")

    print(f"Number of variables   : {mdl.number_of_variables:,}")
    print(f"Number of constraints : {mdl.number_of_constraints:,}")
    print(f"Number of binaries    : {number_of_binaries:,}")
    print(f"Number of integers    : {number_of_integers:,}")

    # --------------------------------------------------
    # Solve statistics
    # --------------------------------------------------
    solve_details = mdl.solve_details

    print("\n--- Solve statistics ---")

    print(f"Solve status : {solve_details.status}")
    print(f"Solve time   : {solve_details.time:.2f} s")
    print(f"MIP gap      : {solve_details.mip_relative_gap:.6f}")

    # --------------------------------------------------
    # Solution results
    # --------------------------------------------------
    if results is None:
        print("\n--- Solution ---")
        print("No feasible solution returned.")
        return

    print("\n--- Solution ---")

    print(f"Objective value : {results['objective_value']:,.2f}")
    print(f"Total cost      : R {results['total_cost']:,.2f}")
    print(f"Total emissions : {results['total_emissions']:,.2f} kg CO2")
    print(f"Open plants     : {len(results['open_plants'])}")


## 5.2. Plot stress-test solution

def stress_test_plot(
    results,
    data,
    coord_file="E12_Coordinates.xlsx",
    figsize=(12, 10),
    label_nodes=False,
    show_title=True,
    show_legend=True,
):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    import Functions

    # --------------------------------------------------
    # Check whether a feasible solution was returned
    # --------------------------------------------------

    if results is None:
        print("No feasible solution available to plot.")
        return

    # --------------------------------------------------
    # Formatting
    # --------------------------------------------------

    plt.rcParams["font.family"] = "serif"

    # --------------------------------------------------
    # Load full coordinate file
    # --------------------------------------------------

    nodes = Functions.load_node_coordinates(coord_file)

    # --------------------------------------------------
    # Keep only nodes included in this experiment
    # --------------------------------------------------

    experiment_nodes = (
        set(data["S"]) |
        set(data["P"]) |
        set(data["B"])
    )

    nodes = nodes[
        nodes["node_id"].isin(experiment_nodes)
    ].copy()

    # --------------------------------------------------
    # Identify active nodes from solution
    # --------------------------------------------------

    inbound_agg, outbound_agg, active_suppliers, active_plants = (
        Functions.aggregate_flows(results)
    )

    active_buyers = {
        b for (p, b) in outbound_agg.keys()
    }

    # --------------------------------------------------
    # Plot
    # --------------------------------------------------

    fig, ax = plt.subplots(figsize=figsize)

    # Plot order:
    # suppliers first, buyers second, plants last
    plot_order = {
        "supplier": 1,
        "buyer": 2,
        "plant": 3
    }

    nodes["plot_order"] = (
        nodes["node_type"].map(plot_order)
    )

    nodes = nodes.sort_values("plot_order")

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------

    for _, row in nodes.iterrows():

        node_id = row["node_id"]
        node_type = row["node_type"]

        x = row["x"]
        y = row["y"]

        # ----------------------------------------------
        # Suppliers
        # ----------------------------------------------

        if node_type == "supplier":

            color = (
                "lightgreen"
                if node_id in active_suppliers
                else "lightgrey"
            )

            marker = "o"
            size = 30
            z = 3

        # ----------------------------------------------
        # Buyers
        # ----------------------------------------------

        elif node_type == "buyer":

            color = "lightcoral"
            marker = "o"
            size = 30
            z = 4

        # ----------------------------------------------
        # Plants
        # ----------------------------------------------

        elif node_type == "plant":

            color = (
                "lightskyblue"
                if node_id in active_plants
                else "lightgrey"
            )

            marker = "s"
            size = 45
            z = 5

        else:

            color = "white"
            marker = "o"
            size = 30
            z = 2

        ax.scatter(
            x,
            y,
            s=size,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=0.5,
            zorder=z,
        )

        # ----------------------------------------------
        # Optional labels
        # ----------------------------------------------

        if label_nodes:

            ax.annotate(
                node_id,
                (x, y),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=6,
                zorder=z + 1,
            )

    # --------------------------------------------------
    # Title
    # --------------------------------------------------

    if show_title:

        cost_million = results["total_cost"] / 1e6
        emissions = results["total_emissions"]

        objective_text = (
            "Minimise Cost"
            if abs(
                results["objective_value"]
                - results["total_cost"]
            ) < 1e-6
            else "Minimise Emissions"
        )

        ax.set_title(
            f"Objective: {objective_text}\n"
            f"Cost = R{cost_million:.2f} million | "
            f"Emissions = {emissions:,.0f} kg CO$_2$",
            fontsize=13,
            pad=15,
            fontfamily="serif",
        )

    # --------------------------------------------------
    # Map-style formatting
    # --------------------------------------------------

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, pos: f"{x:.0f}")
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: f"{y:.0f}")
    )

    ax.set_aspect(
        "equal",
        adjustable="datalim"
    )

    ax.grid(
        True,
        linestyle=":",
        linewidth=0.5,
        alpha=0.5
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --------------------------------------------------
    # Legend
    # --------------------------------------------------

    if show_legend:

        legend_items = [

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Active supplier",
                markerfacecolor="lightgreen",
                markeredgecolor="black",
                markersize=6
            ),

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Inactive supplier",
                markerfacecolor="lightgrey",
                markeredgecolor="black",
                markersize=6
            ),

            Line2D(
                [0], [0],
                marker="s",
                color="w",
                label="Active plant",
                markerfacecolor="lightskyblue",
                markeredgecolor="black",
                markersize=7
            ),

            Line2D(
                [0], [0],
                marker="s",
                color="w",
                label="Inactive plant",
                markerfacecolor="lightgrey",
                markeredgecolor="black",
                markersize=7
            ),

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Buyer",
                markerfacecolor="lightcoral",
                markeredgecolor="black",
                markersize=6
            ),
        ]

        ax.legend(
            handles=legend_items,
            loc="upper left",
            bbox_to_anchor=(1, 1)
        )

    plt.tight_layout()
    plt.show()


## 5.3 Full Plot Coordinates 

def full_plot_coordinates(
    coord_file="E12_Coordinates.xlsx",
    figsize=(12, 10),
    label_nodes=False,
    show_title=True,
    show_legend=True,
):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    import Functions

    # --------------------------------------------------
    # Formatting
    # --------------------------------------------------

    plt.rcParams["font.family"] = "serif"

    # --------------------------------------------------
    # Load all coordinates
    # --------------------------------------------------

    nodes = Functions.load_node_coordinates(coord_file)

    # --------------------------------------------------
    # Plot
    # --------------------------------------------------

    fig, ax = plt.subplots(figsize=figsize)

    # Plot suppliers first, buyers second, plants last
    plot_order = {
        "supplier": 1,
        "buyer": 2,
        "plant": 3
    }

    nodes["plot_order"] = (
        nodes["node_type"].map(plot_order)
    )

    nodes = nodes.sort_values("plot_order")

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------

    for _, row in nodes.iterrows():

        node_id = row["node_id"]
        node_type = row["node_type"]

        x = row["x"]
        y = row["y"]

        if node_type == "supplier":

            color = "lightgreen"
            marker = "o"
            size = 30
            z = 3

        elif node_type == "buyer":

            color = "lightcoral"
            marker = "o"
            size = 30
            z = 4

        elif node_type == "plant":

            color = "lightskyblue"
            marker = "s"
            size = 45
            z = 5

        else:

            color = "white"
            marker = "o"
            size = 30
            z = 2

        ax.scatter(
            x,
            y,
            s=size,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=0.5,
            zorder=z,
        )

        # ----------------------------------------------
        # Optional labels
        # ----------------------------------------------

        if label_nodes:

            ax.annotate(
                node_id,
                (x, y),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=6,
                zorder=z + 1,
            )

    # --------------------------------------------------
    # Title
    # --------------------------------------------------

    if show_title:

        n_suppliers = (nodes["node_type"] == "supplier").sum()
        n_plants = (nodes["node_type"] == "plant").sum()
        n_buyers = (nodes["node_type"] == "buyer").sum()

        ax.set_title(
            f"E12 Stress-Test Network\n"
            f"{n_suppliers} Suppliers | "
            f"{n_plants} Plants | "
            f"{n_buyers} Buyers",
            fontsize=13,
            pad=15,
            fontfamily="serif",
        )

    # --------------------------------------------------
    # Map-style formatting
    # --------------------------------------------------

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, pos: f"{x:.0f}")
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: f"{y:.0f}")
    )

    ax.set_aspect(
        "equal",
        adjustable="datalim"
    )

    ax.grid(
        True,
        linestyle=":",
        linewidth=0.5,
        alpha=0.5
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --------------------------------------------------
    # Legend
    # --------------------------------------------------

    if show_legend:

        legend_items = [

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Supplier",
                markerfacecolor="lightgreen",
                markeredgecolor="black",
                markersize=6
            ),

            Line2D(
                [0], [0],
                marker="s",
                color="w",
                label="Plant",
                markerfacecolor="lightskyblue",
                markeredgecolor="black",
                markersize=7
            ),

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Buyer",
                markerfacecolor="lightcoral",
                markeredgecolor="black",
                markersize=6
            ),
        ]

        ax.legend(
            handles=legend_items,
            loc="upper left",
            bbox_to_anchor=(1, 1)
        )

    plt.tight_layout()
    plt.show()



## 5.5 NEW Full Plot Coordinates 

def new_full_plot_coordinates(
    coord_file="E12_Coordinates.xlsx",
    figsize=(12, 10),
    label_nodes=False,
    show_title=True,
    show_legend=True,
):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    import Functions

    # --------------------------------------------------
    # Formatting
    # --------------------------------------------------

    plt.rcParams["font.family"] = "serif"

    # --------------------------------------------------
    # Load all coordinates
    # --------------------------------------------------

    nodes = Functions.load_node_coordinates(coord_file)

    # --------------------------------------------------
    # Plot
    # --------------------------------------------------

    fig, ax = plt.subplots(figsize=figsize)

    # Plot suppliers first, buyers second, plants last
    plot_order = {
        "supplier": 1,
        "buyer": 2,
        "plant": 3
    }

    nodes["plot_order"] = (
        nodes["node_type"].map(plot_order)
    )

    nodes = nodes.sort_values("plot_order")

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------

    for _, row in nodes.iterrows():

        node_id = row["node_id"]
        node_type = row["node_type"]

        x = row["x"]
        y = row["y"]

        if node_type == "supplier":

            color = "lightgreen"
            marker = "o"
            size = 30
            z = 3

        elif node_type == "buyer":

            color = "lightcoral"
            marker = "o"
            size = 30
            z = 4

        elif node_type == "plant":

            color = "lightskyblue"
            marker = "s"
            size = 45
            z = 5

        else:

            color = "white"
            marker = "o"
            size = 30
            z = 2

        ax.scatter(
            x,
            y,
            s=size,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=0.5,
            zorder=z,
        )

        # ----------------------------------------------
        # Optional labels
        # ----------------------------------------------

        if label_nodes:

            ax.annotate(
                node_id,
                (x, y),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=6,
                zorder=z + 1,
            )

    # --------------------------------------------------
    # Title
    # --------------------------------------------------

    if show_title:

        n_suppliers = (nodes["node_type"] == "supplier").sum()
        n_plants = (nodes["node_type"] == "plant").sum()
        n_buyers = (nodes["node_type"] == "buyer").sum()

        ax.set_title(
            f"{n_suppliers} Suppliers | "
            f"{n_plants} Plants | "
            f"{n_buyers} Buyers",
            fontsize=13,
            pad=15,
            fontfamily="serif",
        )



    # --------------------------------------------------
    # Legend
    # --------------------------------------------------

    if show_legend:

        legend_items = [

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Supplier",
                markerfacecolor="lightgreen",
                markeredgecolor="black",
                markersize=6
            ),

            Line2D(
                [0], [0],
                marker="s",
                color="w",
                label="Plant",
                markerfacecolor="lightskyblue",
                markeredgecolor="black",
                markersize=7
            ),

            Line2D(
                [0], [0],
                marker="o",
                color="w",
                label="Buyer",
                markerfacecolor="lightcoral",
                markeredgecolor="black",
                markersize=6
            ),
        ]

        ax.legend(
            handles=legend_items,
            loc="upper left",
            bbox_to_anchor=(1, 1)
        )

    plt.tight_layout()
    plt.show()