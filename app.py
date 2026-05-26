from duckdb import order
import faicons as fa
from server import server

# Load data and compute static values
from shared import app_dir, expenses
from shiny import App, ui
from shinywidgets import output_widget
from collections import defaultdict

years = expenses.select("Year").to_series().unique().to_list()

# unique combinations
pairs = expenses.select(["Object_cat", "Object"]).unique()

# build nested dict: {Object_cat: {Object: Object}}
grouped = defaultdict(dict)
for cat, obj in zip(pairs["Object_cat"].to_list(), pairs["Object"].to_list()):
    grouped[cat][obj] = obj


ICONS = {
    "dollar" : fa.icon_svg("money-check-dollar"),
    "deposit" : fa.icon_svg("circle-dollar-to-slot"),
    "chart" : fa.icon_svg("chart-line"),
}

# Add page title and sidebar
app_ui = ui.page_sidebar(
    
    ui.sidebar(
        
        ui.input_selectize(
            "chosen_category",
            "Category of Expenditure",
            choices=list(grouped.keys()),
            selected=list(grouped.keys()),
            multiple=True,
        ),

        ui.input_checkbox_group(
            "year",
            "Year of Expendeture",
            years,
            selected = years,
            inline=True,
        ),

        ui.input_action_button("reset", "Reset filter"),
        open="desktop",
    ),
    
    ui.layout_columns(
        
        ui.value_box(
            "CY Expenses",
            ui.output_ui("calender_year_exp"),
            showcase=ICONS["dollar"]
        ),

        ui.value_box(
            "Average Monthly Expense (all years)",
            ui.output_ui("average_monthly"),
            showcase=ICONS["deposit"]
        ),

        ui.value_box(
            "Previous Year Change",
            ui.output_ui("year_change"),
            showcase=ICONS["chart"],
        ),
        fill=False,
    ),
    
    ui.layout_columns(
        
        ui.card(
            ui.card_header("Object of Expense"),
            ui.download_button("download_tab", "Download CSV"),
            ui.output_data_frame("tab_data"),
            full_screen=True,
            style="height: 100px;"  # or 300px, 50vh, etc.
        ),

        ui.card(
            ui.card_header("Monthly Trends"),
            ui.download_button("plot_csv", "Download CSV"),
            output_widget("exp_line_plot"),
            full_screen=True,
        ),
    
        col_widths=[5, 7],
    ),
    
    ui.include_css(app_dir / "styles.css"),
    title="Illinois Department of Corrections Expenses",
    fillable=True,
)

app = App(app_ui, server)