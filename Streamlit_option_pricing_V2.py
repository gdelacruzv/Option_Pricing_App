"""
Created on Fri Feb 24 14:39:13 2023

@author: Gilberto
"""
# Standart python imports
from enum import Enum
from datetime import datetime, timedelta

# Third party imports
import streamlit as st

# Local package imports
from BlackScholesModel import BlackScholesModel 
from MonteCarloSimulation import MonteCarloPricing 
from BinomialTreeModel import BinomialTreeModel
from AmericanPricing import AmericanPricing
from ticker import Ticker
import base
import io
import numpy as np
import matplotlib.pyplot as plt
st.sidebar.title("Equity Option Pricing Calculators")




class OPTION_PRICING_MODEL(Enum):
    BLACK_SCHOLES = 'Black Scholes Model'
    MONTE_CARLO = 'Monte Carlo Simulation'
    BINOMIAL = 'Binomial Model'
    AMERICAN = 'American option LSM Model'

@st.cache
def get_historical_data(ticker):
    """Getting historical data for speified ticker and caching it with streamlit app."""
    return Ticker.get_historical_data(ticker)

# Ignore the Streamlit warning for using st.pyplot()
st.set_option('deprecation.showPyplotGlobalUse', False)

# Main title
st.title('Option pricing')


# User selected model from sidebar 
pricing_method = st.sidebar.radio('Please select option pricing method', options=[model.value for model in OPTION_PRICING_MODEL])


# Displaying specified model
st.subheader(f'Pricing method: {pricing_method}')

if pricing_method == OPTION_PRICING_MODEL.BLACK_SCHOLES.value:
    # Parameters for Black-Scholes model
    ticker = st.text_input('Ticker symbol', 'AAPL')
    strike_price = st.number_input('Strike price', 10)
    risk_free_rate = st.slider('Risk-free rate (%)', 0, 100, 10)
    sigma = st.slider('Sigma (%)', 0, 100, 20)
    exercise_date = st.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365))
    
    if st.button(f'Calculate option price for {ticker}'):
        # Getting data for selected ticker
        data = get_historical_data(ticker)
        st.write(data.tail())
        Ticker.plot_data(data, ticker, 'Close')
        st.pyplot()

        # Formating selected model parameters
        spot_price = Ticker.get_last_price(data, 'Close') 
        risk_free_rate = risk_free_rate / 100
        sigma = sigma / 100
        days_to_maturity = (exercise_date - datetime.now().date()).days

        # Calculating option price
        BSM = BlackScholesModel(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma)
        call_option_price = BSM._calculate_option_price('Call Option')
        put_option_price = BSM._calculate_option_price('Put Option')

        # Displaying call/put option price
        st.subheader(f'Call option price: {call_option_price}')
        st.subheader(f'Put option price: {put_option_price}')

elif pricing_method == OPTION_PRICING_MODEL.AMERICAN.value:
    # Parameters for Monte Carlo simulation
    ticker = st.text_input('Ticker symbol', 'AAPL')
    strike_price = st.number_input('Strike price', 10)
    risk_free_rate = st.slider('Risk-free rate (%)', 0, 100, 10)
    sigma = st.slider('Sigma (%)', 0, 100, 20)
    exercise_date = st.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365))
    number_of_simulations = st.slider('Number of simulations', 10000, 100000, 10000)
    

    if st.button(f'Calculate option price for {ticker}'):
        # Getting data for selected ticker
        data = get_historical_data(ticker)
        st.write(data.tail())
        Ticker.plot_data(data, ticker, 'Close')
        st.pyplot()

        # Formating simulation parameters
        spot_price = Ticker.get_last_price(data, 'Close') 
        risk_free_rate = risk_free_rate / 100
        sigma = sigma / 100
        days_to_maturity = (exercise_date - datetime.now().date()).days

        # ESimulating stock movements
        AP = AmericanPricing(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma, number_of_simulations)
        
        # Calculating call/put option price
        call_option_price = AP._calculate_option_price('Call Option')
        put_option_price = AP._calculate_option_price('Put Option')

        # Displaying call/put option price
        st.subheader(f'Call option price: {call_option_price}')
        st.subheader(f'Put option price: {put_option_price}')
        st.subheader('Give option premiuns a few momments to load')
        
        # Visualizing Monte Carlo Simulation
        euro_res = np.array([])
        amer_res = np.array([])
        euro_res_put = np.array([])
        amer_res_put = np.array([])
        strike_price_list = np.arange(strike_price*.50, strike_price*1.50,strike_price*.20 )

        for strike_price_range in strike_price_list:
            AP_range = AmericanPricing(spot_price, strike_price_range, days_to_maturity, risk_free_rate, sigma, number_of_simulations)
            MC_range = MonteCarloPricing(spot_price, strike_price_range, days_to_maturity, risk_free_rate, sigma, number_of_simulations)
            MC_range.simulate_prices()
            euro_res = np.append(euro_res, MC_range._calculate_option_price('Call Option'))
            amer_res = np.append(amer_res, AP_range._calculate_call_option_price())
            euro_res_put = np.append(euro_res_put, MC_range._calculate_option_price('Put Option'))
            amer_res_put = np.append(amer_res_put, AP_range._calculate_put_option_price())
        
        euro_res = np.array(euro_res)
        amer_res = np.array(amer_res)
        euro_res_put = np.array(euro_res_put)
        amer_res_put = np.array(amer_res_put)

        fig, (ax1, ax2) = plt.subplots(2,1, sharex=True, figsize=(10, 6))
        ax1.plot(strike_price_list, euro_res, 'b', label='European Call')
        ax1.plot(strike_price_list, amer_res, 'ro', label='American Call')
        ax1.set_ylabel('Put Option Value')
        ax1.legend(loc=0)
        wi = 1.0
        ax2.bar(strike_price_list - wi/2, (amer_res - euro_res)/euro_res*100, wi)
        ax2.set_xlabel('Strike Price')
        ax2.set_ylabel('Early Exercise Premium (%)')
        ax2.set_xlim(left=strike_price_list[0], right=strike_price_list[-1])
        st.pyplot()
    
        fig, (ax1, ax2) = plt.subplots(2,1, sharex=True, figsize=(10, 6))
        ax1.plot(strike_price_list, euro_res_put, 'b', label='European Put')
        ax1.plot(strike_price_list, amer_res_put, 'ro', label='American Put')
        ax1.set_ylabel('Call Option Value')
        ax1.legend(loc=0)
        wi = 1.0
        ax2.bar(strike_price_list - wi/2, (amer_res_put - euro_res_put)/euro_res_put*100, wi)
        ax2.set_xlabel('Strike Price')
        ax2.set_ylabel('Early Exercise Premium (%)')
        ax2.set_xlim(left=strike_price_list[0], right=strike_price_list[-1])
        st.pyplot()    
     
        
        
        

elif pricing_method == OPTION_PRICING_MODEL.MONTE_CARLO.value:
    # Parameters for Monte Carlo simulation
    ticker = st.text_input('Ticker symbol', 'AAPL')
    strike_price = st.number_input('Strike price', 10)
    risk_free_rate = st.slider('Risk-free rate (%)', 0, 100, 10)
    sigma = st.slider('Sigma (%)', 0, 100, 20)
    exercise_date = st.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365))
    number_of_simulations = st.slider('Number of simulations', 100, 100000, 10000)
    num_of_movements = st.slider('Number of price movement simulations to be visualized ', 0, int(number_of_simulations/10), 100)

    if st.button(f'Calculate option price for {ticker}'):
        # Getting data for selected ticker
        data = get_historical_data(ticker)
        st.write(data.tail())
        Ticker.plot_data(data, ticker, 'Close')
        st.pyplot()

        # Formating simulation parameters
        spot_price = Ticker.get_last_price(data, 'Close') 
        risk_free_rate = risk_free_rate / 100
        sigma = sigma / 100
        days_to_maturity = (exercise_date - datetime.now().date()).days

        # ESimulating stock movements
        MC = MonteCarloPricing(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma, number_of_simulations)
        MC.simulate_prices()

        # Visualizing Monte Carlo Simulation
        MC.plot_simulation_results(num_of_movements)
        st.pyplot()

        # Calculating call/put option price
        call_option_price = MC._calculate_option_price('Call Option')
        put_option_price = MC._calculate_option_price('Put Option')

        # Displaying call/put option price
        st.subheader(f'Call option price: {call_option_price}')
        st.subheader(f'Put option price: {put_option_price}')

elif pricing_method == OPTION_PRICING_MODEL.BINOMIAL.value:
    # Parameters for Binomial-Tree model
    ticker = st.text_input('Ticker symbol', 'AAPL')
    strike_price = st.number_input('Strike price', 10)
    risk_free_rate = st.slider('Risk-free rate (%)', 0, 100, 10)
    sigma = st.slider('Sigma (%)', 0, 100, 20)
    exercise_date = st.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365))
    number_of_time_steps = st.slider('Number of time steps', 5000, 100000, 15000)

    if st.button(f'Calculate option price for {ticker}'):
         # Getting data for selected ticker
        data = get_historical_data(ticker)
        st.write(data.tail())
        Ticker.plot_data(data, ticker, 'Close')
        st.pyplot()

        # Formating simulation parameters
        spot_price = Ticker.get_last_price(data, 'Close') 
        risk_free_rate = risk_free_rate / 100
        sigma = sigma / 100
        days_to_maturity = (exercise_date - datetime.now().date()).days

        # Calculating option price
        BOPM = BinomialTreeModel(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma, number_of_time_steps)
        call_option_price = BOPM._calculate_option_price('Call Option')
        put_option_price = BOPM._calculate_option_price('Put Option')

        # Displaying call/put option price
        st.subheader(f'Call option price: {call_option_price}')
        st.subheader(f'Put option price: {put_option_price}')
        

  
st.sidebar.subheader("App by Gil De La Cruz Vazquez")
st.sidebar.markdown(
    """
    
    
    For additional information please contact at:
        <div style='font-size:12px'>
        https://www.linkedin.com/in/gil-de-la-cruz-vazquez-62049b125/
    
    GitHub code:
        <div style='font-size:12px'>
        https://github.com/gdelacruzv/Option_Pricing_App
        
    <div style='font-size:10px'>    
         Disclaimer:     
          Price information is pulled from Yahoo Finance. The Content in this site is for informational purposes only, 
         you should not construe any such information or other material as legal, tax, 
         investment, financial, or other advice.
    </div>
    """,
    unsafe_allow_html=True
)
  
