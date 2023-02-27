# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 14:36:39 2023

@author: Gilberto
"""

# Third party imports
import numpy as np
import matplotlib.pyplot as plt
import numpy.random as npr
import scipy.stats as scs
from scipy.stats import norm 
import math as math

# Local package imports
from base import OptionPricingModel
from base import OPTION_TYPE


class AmericanPricing(OptionPricingModel):
    """ 
    Class implementing calculation for European option price using Monte Carlo Simulation.
    We simulate underlying asset price on expiry date using random stochastic process - Brownian motion.
    For the simulation generated prices at maturity, we calculate and sum up their payoffs, average them and discount the final value.
    That value represents option price
    """

    def __init__(self, underlying_spot_price, strike_price, days_to_maturity, risk_free_rate, sigma, number_of_simulations):
        """
        Initializes variables used in Black-Scholes formula .
        underlying_spot_price: current stock or other underlying spot price
        strike_price: strike price for option cotract
        days_to_maturity: option contract maturity/exercise date
        risk_free_rate: returns on risk-free assets (assumed to be constant until expiry date)
        sigma: volatility of the underlying asset (standard deviation of asset's log returns)
        number_of_simulations: number of potential random underlying price movements 
        """
        # Parameters for Variance Reduction
        self.N = number_of_simulations
        self.T = days_to_maturity / 365
        self.r = risk_free_rate
        self.sigma = sigma 
        # Parameters for Brownian
        self.S_0 = underlying_spot_price
        self.K = strike_price
        self.T = days_to_maturity / 365
        self.r = risk_free_rate
        self.sigma = sigma 

        # Parameters for simulation
        self.num_of_steps = days_to_maturity +1
        self.dt = self.T / self.num_of_steps
        self.df=math.exp(self.r*self.dt*-1)       

    def _calculate_call_option_price(self): 
        # Initializing price movements for simulation: rows as time index and columns as different random price movements.
        S = np.zeros((self.num_of_steps, self.N))        
       # Starting value for all price movements is the current spot price
        S[0] = self.S_0
        # cumulative function of standard normal distribution (risk-adjusted probability that the option will be exercised)     
        for t in range(1, self.num_of_steps):
            sn = npr.standard_normal((self.num_of_steps + 1,int(self.N/2)))
            sn = np.concatenate((sn, -sn), axis=1)
            sn = (sn - sn.mean()) / sn.std()
            # Updating prices for next point in time 
            S[t] = S[t - 1] * np.exp((self.r - 0.5 * self.sigma ** 2) * self.dt + (self.sigma * np.sqrt(self.dt) * sn[t]))  
        self.simulation_results_S = S
        self.h = np.maximum(S - self.K, 0)
        V = np.copy(self.h)    
        for t in range(self.num_of_steps -2, 0, -1):
            reg = np.polyfit(S[t], V[t+1] * self.df, 3)
            C = np.polyval(reg, S[t])
            V[t] = np.where(C > self.h[t], V[t+1] * self.df, self.h[t])
        V[0] = V[1] * self.df
        C0 = self.df * np.mean(V[0])
        return C0
    
    def _calculate_put_option_price(self): 
        # Initializing price movements for simulation: rows as time index and columns as different random price movements.
        S = np.zeros((self.num_of_steps, self.N))        
       # Starting value for all price movements is the current spot price
        S[0] = self.S_0
        # cumulative function of standard normal distribution (risk-adjusted probability that the option will be exercised)     
        for t in range(1, self.num_of_steps):
            sn = npr.standard_normal((self.num_of_steps + 1,int(self.N/2)))
            sn = np.concatenate((sn, -sn), axis=1)
            sn = (sn - sn.mean()) / sn.std()
            # Updating prices for next point in time 
            S[t] = S[t - 1] * np.exp((self.r - 0.5 * self.sigma ** 2) * self.dt + (self.sigma * np.sqrt(self.dt) * sn[t]))  
        self.simulation_results_S = S
        self.h = np.maximum(self.K - S, 0)
        V = np.copy(self.h)    
        for t in range(self.num_of_steps -2, 0, -1):
            reg = np.polyfit(S[t], V[t+1] * self.df, 3)
            C = np.polyval(reg, S[t])
            V[t] = np.where(C > self.h[t], V[t+1] * self.df, self.h[t])
        V[0] = V[1] * self.df
        C0 = self.df * np.mean(V[0])
        return C0
    
    def plot_simulation_results(self, num_of_movements):
        """Plots specified number of simulated price movements."""
        plt.figure(figsize=(12,8))
        plt.plot(self.simulation_results_S[:,0:num_of_movements])
        plt.axhline(self.K, c='k', xmin=0, xmax=self.num_of_steps, label='Strike Price')
        plt.xlim([0, self.num_of_steps])
        plt.ylabel('Simulated price movements')
        plt.xlabel('Days in future')
        plt.title(f'First {num_of_movements}/{self.N} Random Price Movements')
        plt.legend(loc='best')
        plt.show()
    
AP = AmericanPricing(146.71, 10, 365, 0.1, 0.2, 10000)
print(AP._calculate_call_option_price())