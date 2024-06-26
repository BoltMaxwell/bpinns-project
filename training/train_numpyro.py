"""
Trains a Bayesian Physics Informed Neural Network on COVID-19 data.
The model is built using Numpyro.
The physics governing the dynamics of the system is a spring-mass-damper system.

Author: Maxwell Bolt
"""
import sys
sys.path.append('.')
import numpy as np
import seaborn as sns
import pickle

import jax
import jax.numpy as jnp
import jax.random as jr

from bpinns.dynamics import smd_dynamics
from preprocessing.process_covid import process_covid_data
import bpinns.numpyro_models as models

## Hyperparameters
# Make sure first layer matches input size, and last layer output size.
layers = [1, 32, 32, 1]
num_collocation = 1000
num_chains = 1
num_warmup = 100
num_samples = 100

# Model Parameters
phys_std = 0.05
data_std = 0.05
c_priorMean = jnp.log(2.2)
k_priorMean = jnp.log(350.0)
x0_priorMean = jnp.log(0.56)
params_std = 0.5
net_std = 2.0
prior_params = (c_priorMean, k_priorMean, x0_priorMean, params_std, net_std)
likelihood_params = (data_std, phys_std)

## Process Data
data = np.loadtxt('data/covid_world.dat')
# This is the data that the original code uses for 2021
start_day = 350
end_day = 700
time, cases, smooth_cases = process_covid_data(data, start_day, end_day)

# ONCE OPERATIONAL: WE WILL SPLIT TO TRAIN AND TEST
train_t = time
train_x = cases

# Normalize 
s_train_t = train_t / jnp.max(train_t)
train_x_mean = jnp.mean(train_x)
train_x_std = jnp.std(train_x)
s_train_x = (train_x - train_x_mean) / train_x_std

rng_key, rng_key_predict = jr.split(jr.PRNGKey(0))

# Take samples
samples = models.run_NUTS(models.bpinn, 
                      rng_key, 
                      s_train_t, 
                      s_train_x,
                      num_collocation,
                      smd_dynamics, 
                      layers, 
                      prior_params,
                      likelihood_params,
                      num_chains=num_chains, 
                      num_warmup=num_warmup, 
                      num_samples=num_samples)

# place the hyperparameters in a dictionary
hyperparams = {'layers': layers, 
               'num_collocation': num_collocation, 
               'num_chains': num_chains,
               'num_warmup': num_warmup, 
               'num_samples': num_samples, 
               'prior_params': prior_params,
               'likelihood_params': likelihood_params}

# save hyperparams and samples
np.save('results/numpyro_hyperparams', hyperparams)
with open('results/numpyro_samples.pkl', 'wb') as f:
    pickle.dump(samples, f)

print('Saved hyperparameters and samples to results/')