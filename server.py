import plotly.express as px
import polars as pl

# Load data and compute static values
from shared import expenses, years, grouped
from shiny import reactive, render, ui
from shinywidgets import render_plotly

def server(input, output, session):
    
    @reactive.calc
    def exp_data():
        chosen_category = input.chosen_category()
        selected_years = input.year()
        years_sel = [int(y) for y in selected_years]
        return expenses.filter(
            pl.col("Object_cat").is_in(chosen_category),
            pl.col('Year').is_in(years_sel))

    @render.data_frame
    def tab_data():

        # get the single most recent year as a Python int
        recent_year = expenses["Year"].max()

        return (
            exp_data()
            .filter(pl.col("Year") == recent_year)
            .group_by("Object", "Object_cat")
            .agg(pl.col("amount").sum().alias("total_expenses"))
            .sort("total_expenses", descending=True)
            .with_columns(
                pl.col("total_expenses")
                .map_elements(lambda v: f"${v:,.0f}")
                .alias("total_expenses")
            )
        )

    @render.download(filename=lambda: "table.csv")
    def download_tab():
        df = tab_data()
        # Polars → CSV
        if hasattr(df, "write_csv"):  # Polars
            df.write_csv(download_tab)   # download_tab is a file-like
        else:                            # pandas
            df.to_csv(download_tab, index=False)

    @render.ui
    def year_change():

        df = exp_data()

        # latest and previous year
        max_year = exp_data()["Year"].max()
        prev_year = max_year - 1

        # total for latest year
        curr_total = (
            exp_data()
            .filter(pl.col("Year") == max_year)
            .select(pl.col("amount").sum())
            .item()
        )

        # total for previous year
        prev_total = (
            exp_data()
            .filter(pl.col("Year") == prev_year)
            .select(pl.col("amount").sum())
            .item()
            if (df["Year"] == prev_year).any()
            else None
        )

        if prev_total is None or prev_total == 0:
            # fallback: just show current total if no prior year
            return f"${curr_total:,.0f}"

        diff = curr_total - prev_total           # absolute change
        pct  = diff / prev_total * 100           # percent change

        sign = "+" if diff >= 0 else "−"
        diff_str = f"{sign}${abs(diff):,.0f}"

        return diff_str

    @render.ui
    def calender_year_exp():

        df_sum = (
            exp_data()
            .filter(pl.col("Year") == exp_data()["Year"].max())
            .select(pl.col("amount").sum())
        )

        total = df_sum.item()  # or df_sum.to_series()[0]

        money_str = f"${total:,.0f}"   # no decimals
        # or: 

        return money_str

    @render.ui
    def average_monthly():

        monthly = (
            exp_data()
            .group_by("dt")
            .agg(pl.col("amount").sum().alias("month_total"))
            .select(pl.col("month_total").mean())
            .item()
        )
        return f"${monthly:,.0f}"
    
    @reactive.calc
    def plot_calc():
        
        dat = (
            exp_data()
            .group_by("dt")
            .agg(pl.col("amount").sum().alias("total_expenses"))
            .with_columns(pl.col("dt").str.strptime(pl.Date, format="%Y-%m-%d").alias("dt_parsed"))
            .with_columns(pl.col("dt_parsed").dt.year().alias("Year"))
            .with_columns(pl.col("dt_parsed").dt.month().alias("month_idx"))
            .with_columns(pl.col("dt_parsed").dt.strftime("%b").alias("month"))
            .sort(["Year", "month_idx"])
            )
            
        return dat.sort(["Year", "month_idx"])

    @render.download(filename=lambda: "chart.csv")
    def plot_csv():
        
        df = plot_calc()
        # Polars → CSV
        if hasattr(df, "write_csv"):  # Polars
            df.write_csv(download_tab)   # download_tab is a file-like
        else:                            # pandas
            df.to_csv(download_tab, index=False)

    @render_plotly
    def exp_line_plot():
        
        # convert to pandas long form for Plotly Express
        pdf = plot_calc().select(["Year", "month_idx", "month", "total_expenses"]).to_pandas()

        # keep months in calendar order when plotting by using month_idx as x and month labels as ticks
        fig = px.line(
            pdf,
            x="month_idx",
            y="total_expenses",
            color="Year",
            markers=True,
            labels={"month_idx": "Month", "total_expenses": "Total expenses"},
            title=""
        )

        fig.update_xaxes(tickmode="array", tickvals=list(range(1,13)), ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
        fig.update_layout(legend_title_text="Year", hovermode="x unified")
        
        return fig

    @reactive.effect
    @reactive.event(input.reset)
    def _():
        
        ui.update_selectize("chosen_category",selected=list(grouped.keys()))
        ui.update_checkbox_group("year", selected = years)
