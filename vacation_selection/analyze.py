# analyze.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from vacation_selection.file_io import read_analysis_from_json

def use_dummy_data():
    return {"average_picks_per_person":14.023255813953488,"total_picks_processed":2412,"total_picks_approved":1444,"total_picks_denied":968,"percent_picks_approved":59.86733001658375,"percent_picks_denied":40.13266998341625,"denial_reasons_overall":{"Day already has maximum firefighters off":734,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":5,"Increment is a holiday, and already has 0 Captains, and 1 Battalion Chiefs off":2,"Already requested this day off (FULL)":2,"Max days off already reached":175,"Schedule Reassignment: (Training Division)":21,"Schedule Reassignment: (PARAMEDIC CLASS)":29},"denial_reasons_by_shift":{"B":{"Day already has maximum firefighters off":381,"Max days off already reached":75,"Schedule Reassignment: (Training Division)":1,"Schedule Reassignment: (PARAMEDIC CLASS)":1},"C":{"Day already has maximum firefighters off":170,"Increment is a holiday, and already has 0 Captains, and 1 Battalion Chiefs off":2,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":1,"Already requested this day off (FULL)":1,"Max days off already reached":19,"Schedule Reassignment: (PARAMEDIC CLASS)":11},"A":{"Day already has maximum firefighters off":183,"Increment is a holiday, and already has 1 Captains, and 0 Battalion Chiefs off":4,"Max days off already reached":81,"Already requested this day off (FULL)":1,"Schedule Reassignment: (Training Division)":20,"Schedule Reassignment: (PARAMEDIC CLASS)":17}},"approval_rate_by_shift":{},"approval_rate_by_rank":{"Captain":{"approved":67.0967741935484,"denied":32.903225806451616},"Lieutenant":{"approved":68.57142857142857,"denied":31.428571428571427},"Battalion Chief":{"approved":58.0952380952381,"denied":41.904761904761905},"Apparatus Specialist":{"approved":66.83804627249359,"denied":33.16195372750643},"Firefighter":{"approved":55.765340525960895,"denied":44.23465947403911}},"distribution_of_requests_by_month":{"1":52,"2":179,"3":244,"4":187,"5":208,"6":247,"7":259,"8":169,"9":169,"10":185,"11":249,"12":264},"top_5_most_requested_weeks_overall":[[52,114],[48,98],[27,88],[12,84],[16,71]],"top_5_most_requested_weeks_by_shift":{"B":[[52,48],[12,37],[27,34],[48,34],[25,34]],"C":[[52,33],[12,29],[48,27],[11,26],[1,25]],"A":[[48,37],[27,35],[52,33],[24,26],[51,25]]}}

# ===============  Analysis  =================================================================================


def analyze_results(ffighters):
    """
    Analyze firefighter processed picks and provide summary statistics.
    """
    analysis = {
        "average_picks_per_person": 0,
        "total_picks_processed": 0,
        "total_picks_approved": 0,
        "total_picks_denied": 0,
        "percent_picks_approved": 0.0,
        "percent_picks_denied": 0.0,
        "denial_reasons_overall": {},
        "denial_reasons_by_shift": {},
        "approval_rate_by_shift": {},
        "approval_rate_by_rank": {},
        "distribution_of_requests_by_month": {},
        "top_5_most_requested_weeks_overall": [],
        "top_5_most_requested_weeks_by_shift": {},
    }

    total_picks = 0
    approved_picks = 0
    denied_picks = 0
    picks_per_person = []
    total_requests_by_month = {}
    weekly_requests = {}
    shift_weekly_requests = {}
    rank_approval_stats = {}

    for ff in ffighters:
        shift = ff.shift
        rank = ff.rank
        if shift not in analysis["denial_reasons_by_shift"]:
            analysis["denial_reasons_by_shift"][shift] = {}
            shift_weekly_requests[shift] = {}

        if rank not in rank_approval_stats:
            rank_approval_stats[rank] = {"approved": 0, "denied": 0}

        # Use processed picks instead of picks
        picks_per_person.append(len(ff.processed))
        for pick in ff.processed:
            total_picks += 1
            if pick.determination == "Approved":
                approved_picks += 1
                rank_approval_stats[rank]["approved"] += 1
            elif pick.determination == "Rejected":
                denied_picks += 1
                reason = pick.reason
                rank_approval_stats[rank]["denied"] += 1
                analysis["denial_reasons_overall"][reason] = (
                    analysis["denial_reasons_overall"].get(reason, 0) + 1
                )
                analysis["denial_reasons_by_shift"][shift][reason] = (
                    analysis["denial_reasons_by_shift"][shift].get(reason, 0) + 1
                )

            # Track requests by month
            month = pick.date.month
            total_requests_by_month[month] = total_requests_by_month.get(month, 0) + 1

            # Track weekly requests
            week = pick.date.isocalendar()[1]
            weekly_requests[week] = weekly_requests.get(week, 0) + 1
            shift_weekly_requests[shift][week] = shift_weekly_requests[shift].get(week, 0) + 1

    # Calculate averages and percentages
    analysis["average_picks_per_person"] = sum(picks_per_person) / len(picks_per_person) if picks_per_person else 0
    analysis["total_picks_processed"] = total_picks
    analysis["total_picks_approved"] = approved_picks
    analysis["total_picks_denied"] = denied_picks
    analysis["percent_picks_approved"] = (approved_picks / total_picks) * 100 if total_picks else 0
    analysis["percent_picks_denied"] = (denied_picks / total_picks) * 100 if total_picks else 0

    # Approval rate by rank
    for rank, stats in rank_approval_stats.items():
        total = stats["approved"] + stats["denied"]
        analysis["approval_rate_by_rank"][rank] = {
            "approved": (stats["approved"] / total * 100) if total else 0,
            "denied": (stats["denied"] / total * 100) if total else 0,
        }

    # Distribution of requests by month
    analysis["distribution_of_requests_by_month"] = {
        month: count for month, count in sorted(total_requests_by_month.items())
    }

    # Top 5 most requested weeks overall
    analysis["top_5_most_requested_weeks_overall"] = sorted(
        weekly_requests.items(), key=lambda x: x[1], reverse=True
    )[:5]

    # Top 5 most requested weeks by shift
    for shift, weeks in shift_weekly_requests.items():
        analysis["top_5_most_requested_weeks_by_shift"][shift] = sorted(
            weeks.items(), key=lambda x: x[1], reverse=True
        )[:5]

    return analysis



def create_monthly_requests_chart(analysis, chart_frame):
    # Create bar chart for monthly requests
    months = list(analysis["distribution_of_requests_by_month"].keys())
    requests = list(analysis["distribution_of_requests_by_month"].values())

    fig, ax = plt.subplots(figsize=(5, 4), facecolor="white")
    ax.bar(months, requests, color="#0066CC")
    ax.set_title("")
    ax.set_xlabel("Month")
    ax.set_ylabel("Requests")
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#999")
    ax.spines["bottom"].set_color("#999")
    ax.tick_params(colors="#333")

    chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# =======  Pie Chart  =============================
import matplotlib.colors as mcolors

def create_pie_chart(analysis, summary_frame):
    # Generate consistent luminosity levels for approved (green) and denied (red)
    green_base = mcolors.to_rgb("#22ff22")  # Base green
    red_base = mcolors.to_rgb("#ff2222")    # Base red
    luminosity_levels = [0.99, 0.8, 0.6, 0.4, 0.25]  # Decreasing luminosity levels
    
    rank_colors_approved = [
        mcolors.to_hex([l * c for c in green_base]) for l in luminosity_levels
    ]
    rank_colors_denied = [
        mcolors.to_hex([l * c for c in red_base]) for l in luminosity_levels
    ]

    # Pie Chart for Metrics
    fig, ax = plt.subplots(figsize=(6, 6), facecolor="white")

    # Data for total approvals and denials
    total_pie_data = [
        analysis['total_picks_approved'],
        analysis['total_picks_denied']
    ]
    total_pie_labels = [
        f"Approved ({analysis['total_picks_approved']})",
        f"Denied ({analysis['total_picks_denied']})"
    ]
    total_pie_colors = ["#66BB6A", "#E57373"]

    # Data for approvals and denials by rank
    rank_labels = list(analysis['approval_rate_by_rank'].keys())
    rank_data_approved = [
        (analysis['approval_rate_by_rank'][rank]['approved'] / 100) * analysis['total_picks_approved']
        for rank in rank_labels
    ]
    rank_data_denied = [
        (analysis['approval_rate_by_rank'][rank]['denied'] / 100) * analysis['total_picks_denied']
        for rank in rank_labels
    ]

    # Normalize inner pie data to match total proportions
    inner_pie_data = rank_data_approved + rank_data_denied
    inner_pie_data_normalized = [x / sum(inner_pie_data) * sum(total_pie_data) for x in inner_pie_data]
    inner_colors = rank_colors_approved + rank_colors_denied

    # Plot outer pie chart (total approval/denial) with reduced thickness
    ax.pie(
        total_pie_data, radius=1, labels=total_pie_labels, autopct="%.1f%%", startangle=90, colors=total_pie_colors,
        wedgeprops=dict(width=0.2, edgecolor='w')  # Reduced thickness for outer chart
    )

    # Plot inner pie chart (by rank) with normalized data
    ax.pie(
        inner_pie_data_normalized, radius=0.8, labels=None, startangle=90, colors=inner_colors,
        wedgeprops=dict(width=0.3, edgecolor='w')  # Adjusted thickness for inner chart
    )

    # Add a legend for inner pie chart with smaller font size
    ax.legend(
        handles=[
            plt.Line2D([0], [0], marker="o", color="w", label=f"{rank} Approved", markerfacecolor=rank_colors_approved[i], markersize=8)
            for i, rank in enumerate(rank_labels)
        ] + [
            plt.Line2D([0], [0], marker="o", color="w", label=f"{rank} Denied", markerfacecolor=rank_colors_denied[i], markersize=8)
            for i, rank in enumerate(rank_labels)
        ],
        loc="upper left", bbox_to_anchor=(1, 0.5), title="By Rank", fontsize=8
    )

    ax.set_title("Approval vs Denial Overview")

    # Adjust layout to prevent clipping
    fig.tight_layout()

    # Attach pie chart to the Tkinter frame
    pie_canvas = FigureCanvasTkAgg(fig, summary_frame)
    pie_canvas.get_tk_widget().grid(row=2, column=0, columnspan=2, pady=10)

#

def apply_styles(root):
    # Style configuration
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

    # Main window
    root = tk.Tk()
    root.title("Analysis Dashboard")

    apply_styles(root)

    # Create Notebook for Tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Tab 1: Key Statistics and Pie Chart
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Key Statistics")

    # Summary Frame
    summary_frame = ttk.Frame(tab1)
    summary_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Summary Title
    summary_title = ttk.Label(summary_frame, text="Key Statistics", style="SubHeader.TLabel")
    summary_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

    # Average Picks per Person
    ttk.Label(summary_frame, text="Average Picks/Person:", style="Bold.TLabel").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Label(summary_frame, text=f"{analysis['average_picks_per_person']:.2f}", style="Bold.TLabel").grid(row=1, column=1, sticky="w", pady=5)

    create_pie_chart(analysis, summary_frame)

    # Tab 2: Monthly Requests Chart
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Monthly Requests")

    # Chart Frame
    chart_frame = ttk.Frame(tab2)
    chart_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Chart Title
    chart_title = ttk.Label(chart_frame, text="Monthly Requests", style="SubHeader.TLabel")
    chart_title.pack(anchor="w", pady=(0,10))

    create_monthly_requests_chart(analysis, chart_frame)

    # Tab 3: Additional Information
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Additional Information")

    # Detailed Frame
    details_frame = ttk.Frame(tab3)
    details_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Detailed Title
    details_title = ttk.Label(details_frame, text="Additional Information", style="SubHeader.TLabel")
    details_title.grid(row=0, column=0, sticky="w", pady=(0,10))

    # Denial Reasons
    denial_frame = ttk.Frame(details_frame)
    denial_frame.grid(row=1, column=0, sticky="w")

    ttk.Label(denial_frame, text="Denial Reasons Overall:", style="Bold.TLabel").grid(row=0, column=0, sticky="w")

    r = 1
    for reason, count in analysis["denial_reasons_overall"].items():
        ttk.Label(denial_frame, text=f"• {reason}: {count}").grid(row=r, column=0, sticky="w", pady=2)
        r += 1

    # Approval Rate By Rank
    approval_frame = ttk.Frame(details_frame)
    approval_frame.grid(row=2, column=0, sticky="w", pady=(20,0))

    ttk.Label(approval_frame, text="Approval Rate by Rank:", style="Bold.TLabel").grid(row=0, column=0, sticky="w")

    r = 1
    for rank, rates in analysis["approval_rate_by_rank"].items():
        ttk.Label(approval_frame, text=f"• {rank}: {rates['approved']:.2f}% Approved, {rates['denied']:.2f}% Denied").grid(row=r, column=0, sticky="w", pady=2)
        r += 1

    root.mainloop()

def load_analysis_from_file(output_folder="output"):
    """
    Loads the most recent analysis file from the specified folder.
    Falls back to dummy data if no file is found or an error occurs.
    """
    data = read_analysis_from_json(output_folder)
    if not data:
        print("No valid analysis file found. Using dummy data.")
        data = use_dummy_data()
    return data
    

def main():
    analysis = load_analysis_from_file()
    display_dashboard(analysis)

if __name__ == "__main__":
    main()
