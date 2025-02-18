# analyze.py

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.colors as mcolors
from datetime import datetime
from vacation_selection.file_io import read_analysis_from_json

def use_dummy_data():
    return {"total":{"processed":2412,"approved":1443,"denied":969,"approval_rate":59.82587064676616,"average_picks_per_person":14.023255813953488,"top_rejected_reasons":{"Day already has maximum firefighters off":734,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":5,"Increment is a holiday, and already has 0 Captains, and 1 Battalion Chiefs off":2,"Already requested this day off (FULL)":3,"Max days off already reached":175,"Schedule Reassignment: (PARAMEDIC CLASS)":29,"Schedule Reassignment: (Training Division)":21},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]]},"by_shift":{"C":{"processed":640,"approved":436,"denied":204,"approval_rate":68.125,"top_rejected_reasons":{"Day already has maximum firefighters off":169,"Increment is a holiday, and already has 0 Captains, and 1 Battalion Chiefs off":2,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":1,"Already requested this day off (FULL)":2,"Max days off already reached":19,"Schedule Reassignment: (PARAMEDIC CLASS)":11},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]],"monthly_approvals":{"1":10,"2":36,"3":47,"4":42,"5":41,"6":44,"7":36,"8":41,"9":37,"10":23,"11":41,"12":38},"monthly_denials":{"1":13,"2":19,"3":35,"4":20,"5":11,"6":11,"7":18,"8":6,"9":18,"10":1,"11":23,"12":29}},"B":{"processed":991,"approved":532,"denied":459,"approval_rate":53.68314833501514,"top_rejected_reasons":{"Day already has maximum firefighters off":382,"Max days off already reached":75,"Schedule Reassignment: (PARAMEDIC CLASS)":1,"Schedule Reassignment: (Training Division)":1},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]],"monthly_approvals":{"1":13,"2":44,"3":50,"4":37,"5":50,"6":50,"7":55,"8":44,"9":43,"10":45,"11":49,"12":52},"monthly_denials":{"1":1,"2":23,"3":53,"4":23,"5":27,"6":64,"7":60,"8":25,"9":19,"10":26,"11":68,"12":70}},"A":{"processed":781,"approved":475,"denied":306,"approval_rate":60.819462227912936,"top_rejected_reasons":{"Day already has maximum firefighters off":183,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":4,"Max days off already reached":81,"Already requested this day off (FULL)":1,"Schedule Reassignment: (PARAMEDIC CLASS)":17,"Schedule Reassignment: (Training Division)":20},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]],"monthly_approvals":{"1":14,"2":40,"3":42,"4":45,"5":47,"6":47,"7":49,"8":41,"9":32,"10":50,"11":35,"12":33},"monthly_denials":{"1":1,"2":17,"3":17,"4":20,"5":32,"6":31,"7":41,"8":12,"9":20,"10":40,"11":33,"12":42}}},"by_rank":{"Lieutenant":{"processed":280,"approved":192,"denied":88,"approval_rate":68.57142857142857,"top_rejected_reasons":{"Day already has maximum firefighters off":88},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]]},"Captain":{"processed":155,"approved":104,"denied":51,"approval_rate":67.0967741935484,"top_rejected_reasons":{"Day already has maximum firefighters off":45,"Increment is a holiday, and already has 0 Captains, and 1 Battalion Chiefs off":2,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":4},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]]},"Battalion Chief":{"processed":105,"approved":61,"denied":44,"approval_rate":58.0952380952381,"top_rejected_reasons":{"Day already has maximum firefighters off":43,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":1},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]]},"Apparatus Specialist":{"processed":389,"approved":260,"denied":129,"approval_rate":66.83804627249359,"top_rejected_reasons":{"Day already has maximum firefighters off":128,"Already requested this day off (FULL)":1},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]]},"Firefighter":{"processed":1483,"approved":826,"denied":657,"approval_rate":55.69790964261632,"top_rejected_reasons":{"Day already has maximum firefighters off":430,"Already requested this day off (FULL)":2,"Max days off already reached":175,"Schedule Reassignment: (PARAMEDIC CLASS)":29,"Schedule Reassignment: (Training Division)":21},"top_5_weeks":[[52,114],[48,98],[27,88],[12,84],[16,71]]}},"distribution_of_requests_by_month":{}}

# ===============  Analysis  =================================================================================


def analyze_results(ffighters):
    analysis = {
        "total": {"processed": 0, "approved": 0, "denied": 0, "approval_rate": 0.0, "average_picks_per_person": 0.0,
                  "top_rejected_reasons": {}, "top_5_weeks": []},
        "by_shift": {},
        "by_rank": {},
        "distribution_of_requests_by_month": {}  # Added to track requests by month
    }

    picks_per_person = []
    weekly_requests = {}

    for ff in ffighters:
        shift = ff.shift
        rank = ff.rank

        # Initialize dicts if they don’t exist
        if shift not in analysis["by_shift"]:
            analysis["by_shift"][shift] = {"processed": 0, "approved": 0, "denied": 0, "approval_rate": 0.0,
                                           "top_rejected_reasons": {}, "top_5_weeks": []}

        if rank not in analysis["by_rank"]:
            analysis["by_rank"][rank] = {"processed": 0, "approved": 0, "denied": 0, "approval_rate": 0.0,
                                          "top_rejected_reasons": {}, "top_5_weeks": []}

        # Track picks per person
        picks_per_person.append(len(ff.processed))

        # Process each pick
        for pick in ff.processed:
            analysis["total"]["processed"] += 1
            analysis["by_shift"][shift]["processed"] += 1
            analysis["by_rank"][rank]["processed"] += 1

            # Approval or Denial
            if pick.determination == "Approved":
                analysis["total"]["approved"] += 1
                analysis["by_shift"][shift]["approved"] += 1
                analysis["by_rank"][rank]["approved"] += 1
            elif pick.determination == "Rejected":
                analysis["total"]["denied"] += 1
                analysis["by_shift"][shift]["denied"] += 1
                analysis["by_rank"][rank]["denied"] += 1

                # Track top rejection reasons
                reason = pick.reason
                for group in [analysis["total"], analysis["by_shift"][shift], analysis["by_rank"][rank]]:
                    group["top_rejected_reasons"][reason] = group["top_rejected_reasons"].get(reason, 0) + 1

            # Track weekly requests
            week = pick.date.isocalendar()[1]
            weekly_requests[week] = weekly_requests.get(week, 0) + 1

            # Track monthly approvals/denials by shift
            month = pick.date.month

            # Initialize if not already set
            if "monthly_approvals" not in analysis["by_shift"][shift]:
                analysis["by_shift"][shift]["monthly_approvals"] = {m: 0 for m in range(1, 13)}
                analysis["by_shift"][shift]["monthly_denials"] = {m: 0 for m in range(1, 13)}

            if pick.determination == "Approved":
                analysis["by_shift"][shift]["monthly_approvals"][month] += 1
            elif pick.determination == "Rejected":
                analysis["by_shift"][shift]["monthly_denials"][month] += 1


    # Calculate approval rates and top 5 weeks
    for group in [analysis["total"]] + list(analysis["by_shift"].values()) + list(analysis["by_rank"].values()):
        group["approval_rate"] = (group["approved"] / group["processed"] * 100) if group["processed"] else 0.0
        group["top_5_weeks"] = sorted(weekly_requests.items(), key=lambda x: x[1], reverse=True)[:5]

    # Average picks per person
    analysis["total"]["average_picks_per_person"] = sum(picks_per_person) / len(picks_per_person) if picks_per_person else 0

    return analysis



# =============== Analysis Utilities ============================

def get_analysis_group(analysis, group_key, subgroup):
    """
    Utility function to safely access nested analysis groups.
    """
    return analysis.get(group_key, {}).get(subgroup, {})


# =============== Analysis Display ==============================

import matplotlib.colors as mcolors

def create_monthly_requests_chart(analysis, chart_frame):
    """
    Create stacked bar chart for monthly requests, broken down by shift (A, B, C) and approvals/denials.
    """
    import matplotlib.colors as mcolors

    # Base colors for approvals and denials
    green_base = mcolors.to_rgb("#22ff22")  # Base green
    red_base = mcolors.to_rgb("#ff2222")    # Base red
    luminosity_levels = [0.9, 0.7, 0.5]  # Different luminosity for A, B, C shifts

    shift_colors_approved = [mcolors.to_hex([l * c for c in green_base]) for l in luminosity_levels]
    shift_colors_denied = [mcolors.to_hex([l * c for c in red_base]) for l in luminosity_levels]

    # Prepare data
    months = range(1, 13)  # Months 1 to 12
    shifts = ["A", "B", "C"]

    # Initialize monthly breakdowns
    monthly_approvals = {shift: [0] * 12 for shift in shifts}
    monthly_denials = {shift: [0] * 12 for shift in shifts}

    # Populate monthly approvals and denials by shift
    for shift in shifts:
        shift_data = analysis["by_shift"].get(shift, {})
        for month in range(1, 13):
            approved = shift_data.get("monthly_approvals", {}).get(month, 0)
            denied = shift_data.get("monthly_denials", {}).get(month, 0)
            monthly_approvals[shift][month - 1] = approved
            monthly_denials[shift][month - 1] = denied

    # Create the stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")

    # Plot order: A Approved, B Approved, C Approved, A Denied, B Denied, C Denied
    bottom = [0] * 12
    data_order = [("A", "approved"), ("B", "approved"), ("C", "approved"),
                  ("A", "denied"), ("B", "denied"), ("C", "denied")]

    for shift, status in data_order:
        color = shift_colors_approved if status == "approved" else shift_colors_denied
        shift_idx = shifts.index(shift)
        data = monthly_approvals[shift] if status == "approved" else monthly_denials[shift]

        # Plot the bar
        ax.bar(months, data, color=color[shift_idx], label=f"{shift} Shift {status.capitalize()}", bottom=bottom)

        # Annotate with numbers
        for i, value in enumerate(data):
            if value > 0:  # Avoid annotating 0 values
                ax.text(i + 1, bottom[i] + value / 2, str(value), ha="center", va="center", fontsize=8, color="black")

        # Update bottom for stacking
        bottom = [bottom[j] + data[j] for j in range(12)]

    # Chart aesthetics
    ax.set_title("Monthly Requests by Shift (Approvals and Denials)", fontsize=14, pad=40)  # Increased padding
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Number of Requests", fontsize=12)
    ax.set_xticks(months)
    ax.set_xticklabels([str(m) for m in months])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#999")
    ax.spines["bottom"].set_color("#999")
    ax.tick_params(colors="#333")

    # Move legend above the chart with adjusted spacing and add a frame for readability
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),  # Adjust vertical positioning above the chart
        ncol=3,
        title="Shifts",
        fontsize=10,
        frameon=True  # Add a frame for better readability
    )

    # Adjust layout to prevent overlapping
    fig.subplots_adjust(top=0.85)  # Adjust space above the chart for legend and title

    # Embed the chart into the Tkinter frame
    chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def display_key_statistics(tab_frame, analysis):
    """
    Display the key statistics including average picks/person and approval/denial breakdown.
    """
    # Summary Frame
    summary_frame = ttk.Frame(tab_frame)
    summary_frame.pack(fill="both", expand=True, padx=20, pady=20)

    ttk.Label(summary_frame, text="Key Statistics", style="SubHeader.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
    ttk.Label(summary_frame, text="Average Picks/Person:", style="Bold.TLabel").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Label(summary_frame, text=f"{analysis['total']['average_picks_per_person']:.2f}", style="Bold.TLabel").grid(row=1, column=1, sticky="w")

    # Display Average Picks/Person by Shift in Horizontal Layout
    picks_frame = ttk.Frame(summary_frame)
    picks_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
    ttk.Label(picks_frame, text="Average Picks/Person by Shift:", style="Bold.TLabel").grid(row=0, column=0, sticky="w")
    for i, shift in enumerate(["A", "B", "C"], start=1):
        ttk.Label(picks_frame, text=f"{shift} Shift: {analysis['by_shift'].get(shift, {}).get('average_picks', 0):.2f}",
                  style="TLabel").grid(row=0, column=i, sticky="w", padx=(10, 0))

    create_pie_chart(analysis, summary_frame)



def create_pie_chart(analysis, summary_frame):
    """
    Create a pie chart for total approval/denial and breakdown by rank.
    """
    import matplotlib.colors as mcolors

    # Base colors for approved/denied
    green_base = mcolors.to_rgb("#22ff22")
    red_base = mcolors.to_rgb("#ff2222")
    luminosity_levels = [0.99, 0.8, 0.6, 0.4, 0.25]
    rank_colors_approved = [mcolors.to_hex([l * c for c in green_base]) for l in luminosity_levels]
    rank_colors_denied = [mcolors.to_hex([l * c for c in red_base]) for l in luminosity_levels]

    # Outer Pie: Total Approved and Denied
    total_approved = analysis["total"]["approved"]
    total_denied = analysis["total"]["denied"]
    outer_pie_data = [total_approved, total_denied]
    outer_pie_labels = [f"Approved ({total_approved})", f"Denied ({total_denied})"]
    outer_pie_colors = ["#66BB6A", "#E57373"]

    # Inner Pie: Approved/Denied by Rank
    rank_labels = list(analysis["by_rank"].keys())
    rank_approved = [analysis["by_rank"][rank]["approved"] for rank in rank_labels]
    rank_denied = [analysis["by_rank"][rank]["denied"] for rank in rank_labels]

    inner_pie_data = rank_approved + rank_denied
    inner_pie_colors = rank_colors_approved + rank_colors_denied

    # Plot Pie Charts
    fig, ax = plt.subplots(figsize=(6, 6), facecolor="white")
    ax.pie(
        outer_pie_data, radius=1, labels=outer_pie_labels,
        autopct=lambda p: f'{p:.1f}%' if p > 0 else '',
        startangle=90, colors=outer_pie_colors, wedgeprops=dict(width=0.3, edgecolor="w"),
        pctdistance=0.85, textprops={'color': 'white', 'fontsize': 10}  # White percent text
    )
    ax.pie(
        inner_pie_data, radius=0.7, startangle=90, labels=None,
        colors=inner_pie_colors, wedgeprops=dict(width=0.4, edgecolor="w")
    )

    # Add Legend
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", label=f"{rank} Approved", markerfacecolor=rank_colors_approved[i], markersize=8)
        for i, rank in enumerate(rank_labels)
    ] + [
        plt.Line2D([0], [0], marker="o", color="w", label=f"{rank} Denied", markerfacecolor=rank_colors_denied[i], markersize=8)
        for i, rank in enumerate(rank_labels)
    ]
    ax.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=8, title="By Rank")

    ax.set_title("Approval vs Denial Breakdown", pad=30)
    fig.tight_layout()

    pie_canvas = FigureCanvasTkAgg(fig, summary_frame)
    pie_canvas.get_tk_widget().grid(row=2, column=0, columnspan=2, pady=10)



def display_additional_information(parent, analysis):
    """
    Displays denial reasons and most popular weeks split into tabs for each shift and a total panel.
    Optimized for compact layout.
    """
    # Create Notebook for Shift Tabs
    notebook = ttk.Notebook(parent)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Add Total Tab
    total_tab = ttk.Frame(notebook)
    notebook.add(total_tab, text="Total")
    add_information_tab(total_tab, "Total", analysis["total"]["top_rejected_reasons"], analysis["total"]["top_5_weeks"])

    # Create Tabs for Each Shift
    shifts = ["A", "B", "C"]
    for shift in shifts:
        shift_tab = ttk.Frame(notebook)
        notebook.add(shift_tab, text=f"{shift} Shift")
        shift_data = analysis["by_shift"].get(shift, {})
        add_information_tab(
            shift_tab,
            f"{shift} Shift",
            shift_data.get("top_rejected_reasons", {}),
            shift_data.get("top_5_weeks", []),
        )


def add_information_tab(tab, title, denial_reasons, popular_weeks):
    """
    Adds denial reasons and popular weeks to a tab in a compact layout.
    """
    # Header
    ttk.Label(tab, text=f"Denial Reasons for {title}:", style="Bold.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    # Denial Reasons (Left Column)
    denial_frame = ttk.Frame(tab)
    denial_frame.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

    for i, (reason, count) in enumerate(denial_reasons.items(), start=1):
        ttk.Label(denial_frame, text=f"• {reason}: {count}").grid(row=i, column=0, sticky="w", pady=2)

    # Popular Weeks (Right Column)
    popular_frame = ttk.Frame(tab)
    popular_frame.grid(row=1, column=1, sticky="ne", padx=10, pady=5)

    ttk.Label(popular_frame, text=f"Most Popular Weeks for {title}:", style="Bold.TLabel").grid(row=0, column=0, sticky="w", pady=2)

    for i, (week, requests) in enumerate(popular_weeks, start=1):
        ttk.Label(popular_frame, text=f"Week {week}: {requests} requests").grid(row=i, column=0, sticky="w", pady=2)

    # Configure the grid for better alignment
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_columnconfigure(1, weight=1)




def apply_styles(root):
    """
    Apply consistent styles to the UI.
    """
    root.configure(bg="white")
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", font=("Helvetica", 11), background="white", foreground="#333")
    style.configure("TLabel", background="white", foreground="#333")
    style.configure("TFrame", background="white")
    style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground="#222")
    style.configure("SubHeader.TLabel", font=("Helvetica", 12, "bold"), foreground="#222")
    style.configure("Bold.TLabel", font=("Helvetica", 11, "bold"), foreground="#333")


def display_dashboard(analysis):
    """
    Display the analysis results in a Tkinter dashboard with tabs for Key Statistics,
    Monthly Requests, and Additional Information.
    """
    # Main Window
    root = tk.Tk()
    root.title("Analysis Dashboard")
    apply_styles(root)

    # Handle proper closing of the app
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # Create Notebook for Tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Tab 1: Key Statistics
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Key Statistics")
    display_key_statistics(tab1, analysis)  # Updated to include Picks/Person by shift and enhanced layout

    # Tab 2: Monthly Requests Chart
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Monthly Requests")
    chart_frame = ttk.Frame(tab2)
    chart_frame.pack(fill="both", expand=True, padx=20, pady=20)
    ttk.Label(chart_frame, text="Monthly Requests", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))
    create_monthly_requests_chart(analysis, chart_frame)

    # Tab 3: Additional Information
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Additional Information")
    display_additional_information(tab3, analysis)  # Tabs for Total, A Shift, B Shift, C Shift

    # Start the Tkinter main loop
    root.mainloop()


# =============== File Loader and Main ==========================

def load_analysis_from_file(output_folder="output"):
    """
    Loads analysis data from the specified folder or uses dummy data.
    """
    data = read_analysis_from_json(output_folder)
    if not data:
        print("No valid analysis file found. Exiting.")
        return None
    return data


def main():
    analysis = load_analysis_from_file()
    if analysis:
        display_dashboard(analysis)


if __name__ == "__main__":
    main()
