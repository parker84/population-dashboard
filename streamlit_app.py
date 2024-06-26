import streamlit as st
import pandas as pd
from plotly import express as px
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Population Dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
    layout='wide',
    initial_sidebar_state='collapsed'
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

country_codes_w_flags = {
    'USA': 'USA 🇺🇸',
    'CAN': 'CAN 🇨🇦',
    'CHN': 'CHN 🇨🇳',
    'IND': 'IND 🇮🇳',
    'JPN': 'JPN 🇯🇵',
    'RUS': 'RUS 🇷🇺',
    'GBR': 'GBR 🇬🇧',
    'BRA': 'BRA 🇧🇷', 
}

@st.cache_data
def get_population_data():
    """Grab Population data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    DATA_FILENAME = Path(__file__).parent/'data/population_data.csv'
    raw_population_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    population_df = raw_population_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'Population',
    ).rename(columns={'Country Code': 'Country'})
    population_df['Country'] = population_df['Country'].replace(country_codes_w_flags)
    population_df['Year'] = pd.to_numeric(population_df['Year'])
    population_df['Population (M)'] = population_df['Population'] / 1e6
    population_df['Population'] = (population_df['Population'] / 1e6).round(0) * 1e6

    return population_df.sort_values(by='Year', ascending=False)

def plot_populations_by_group(
        metric_df, 
        var_to_group_by_col, 
        metric_col,
        bar_chart=True,
        hover_data=None
    ):
    col1, col2 = st.columns(2)
    bar_metric_df = metric_df[metric_df[metric_col].isnull() == False]
    max_year = bar_metric_df['Year'].max()
    bar_metric_df = bar_metric_df[
        bar_metric_df['Year'] == max_year
    ]
    bar_metric_df = bar_metric_df.sort_values(by=metric_col, ascending=False)
    category_orders={
        var_to_group_by_col: bar_metric_df[var_to_group_by_col].tolist()
    }
    with col1:
        p = px.line(
                metric_df,
                x='Year',
                y=metric_col,
                color=var_to_group_by_col,
                title=f'Yearly {metric_col} by {var_to_group_by_col}',
                hover_data=hover_data,
                category_orders=category_orders,

            )
        st.plotly_chart(p, use_container_width=True)
    with col2:
        if bar_chart:
            p = px.bar(
                    bar_metric_df,
                    y=var_to_group_by_col,
                    x=metric_col,
                    orientation='h',
                    title=f'{metric_col} by {var_to_group_by_col} (Year = {int(max_year)})',
                    hover_data=hover_data,
                    category_orders=category_orders
                )
        else:
            p = px.pie(
                bar_metric_df,
                names=var_to_group_by_col,
                values=metric_col,
                title=f'{metric_col} by {var_to_group_by_col} (Year = {int(max_year)})',
                hole=0.4,
                category_orders=category_orders,
                hover_data=hover_data
            )
        st.plotly_chart(p, use_container_width=True)
        return category_orders

def show_metric(
        df, 
        y_col, 
        format_str='{:,}M', 
        delta_color='normal', 
        title=None, 
        help=None, 
        calc_per_change=True
    ):
        if title is None:
            title = y_col
        if calc_per_change:
            try:
                percentage_change = (
                    100 * ((df[y_col].iloc[0] / df[y_col].iloc[1]) - 1)
                )
                delta='{change}% (YoY)'.format(
                    change=round(percentage_change, 2)
                )
            except Exception as err:
                print('❌' + str(err))
                delta = None
        else: 
            delta = None
        st.metric(
            title,
            value=format_str.format(df[y_col].iloc[0]),
            delta=delta,
            delta_color=delta_color,
            help=help
        )


population_df = get_population_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: Population Dashboard
'''

st.caption('Population data from the [World Bank Open Data](https://data.worldbank.org/) website.')

# Add some spacing
''
''

min_value = population_df['Year'].min()
max_value = population_df['Year'].max()


from_year, to_year = st.sidebar.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value]
)
st.sidebar.caption("Want to say thanks? \n[Buy me a coffee ☕](https://www.buymeacoffee.com/brydon)")

population_df_max_year = population_df[population_df['Year'] == to_year].sort_values(by='Population', ascending=False)
countries = population_df_max_year['Country'].tolist()

if not len(countries):
    st.warning("Select at least one country")


selected_countries = st.multiselect(
    'Select Countries',
    countries,
    default=country_codes_w_flags.values()
)

''
''
''

# Filter the data
filtered_population_df = population_df[
    (population_df['Country'].isin(selected_countries))
    & (population_df['Year'] <= to_year)
    & (from_year <= population_df['Year'])
]
max_year_filtered_df = filtered_population_df[filtered_population_df['Year'] == to_year].sort_values(by='Population', ascending=False)

st.header('Annual Population by Country', divider='gray')

''

cols = st.columns(len(selected_countries))
i = 0
for country in max_year_filtered_df['Country']:
    with cols[i]:
        show_metric(
            filtered_population_df[filtered_population_df['Country'] == country],
            'Population (M)',
            title=country,
            format_str='{:,.1f}M',
            delta_color='normal',
        )
    i += 1

plot_populations_by_group(
    filtered_population_df,
    'Country',
    bar_chart=True,
    metric_col='Population'
)

''
''