#for modeling
import pymc as pm
import nutpie
import arviz as az

#for general data handling
from datasets import Dataset
from tqdm import tqdm
import pandas as pd
import numpy as np

#for the simulated page draws
from scipy.stats import zipfian
from scipy.stats import poisson
from scipy import signal

#
start_seed = 3001
end_seed = 5000
#
def c_zipf_pois_pmf(x,alpha,n,mu):
    """ Convolved probability mass function of a zipf and poisson distribution"""
    return signal.convolve(poisson.pmf(x,mu),zipfian.pmf(x, alpha, n))

def c_zipf_pois_rng(n_vals,zipf_a,zipf_n,poisson_mu,seed):
    """ Generates n_vals from a convolved zipfian-poisson distribution"""
    #find where sum(p) ~ 1
    range_end = zipf_n
    
    p = c_zipf_pois_pmf([i for i in range(range_end)],
                        zipf_a,zipf_n,poisson_mu)
    while sum(p) < 0.9999999:
        range_end += int(zipf_n/20)
        p = c_zipf_pois_pmf([i for i in range(range_end)],
                        zipf_a,zipf_n,poisson_mu)
        
    #assign discrete vals to ps
    d_vals = [i for i in range(len(p))]
    #draw n from a categorical dist with i categories and p probs
    rng = np.random.default_rng(seed=seed)
    draws = rng.choice(a=d_vals,size=n_vals,p=p)
    return draws

def beta_mu(e_alpha_1,e_beta_1):
    mu_1 = e_alpha_1/(e_alpha_1+e_beta_1)
    return mu_1

def beta_var(e_alpha_1,e_beta_1):
    var_1 = (e_alpha_1*e_beta_1)/((e_alpha_1+e_beta_1)**2)*(e_alpha_1+e_beta_1+1)
    return var_1

class Simulated_document_diff:
    """"""
    def __init__(self, alpha_1, beta_1, n_pages_1,
                 alpha_2,beta_2,n_pages_2,seed, ppc = False):
        #params
        self.ppc = ppc
        self.seed = seed
        self.r_a_1 = alpha_1
        self.r_b_1 = beta_1
        self.n_p_1 = n_pages_1
        self.r_a_2 = alpha_2
        self.r_b_2 = beta_2
        self.n_p_2 = n_pages_2
        # simulate the data from the parameters
        doc_dist_1 = pm.Beta.dist(
                                alpha=self.r_a_1,
                                beta=self.r_b_1)
        self.drawn_vals_1 = pm.draw(doc_dist_1,
                                    draws=self.n_p_1,
                                    random_seed=self.seed)
        doc_dist_2 = pm.Beta.dist(
                                alpha=self.r_a_2,
                                beta=self.r_b_2)
        self.drawn_vals_2 = pm.draw(doc_dist_2,
                                    draws=self.n_p_2,
                                    random_seed=self.seed)

    def infer_params(self,prior_lb = 1, prior_ub = 10):
        """infers the distribution from params"""
        bb_model = pm.Model()
        with bb_model:
            # Priors for unknown model parameters
            e_alpha_1 = pm.Uniform("estimate_alpha_1",
                                   prior_lb, prior_ub)
            e_beta_1 = pm.Uniform("estimate_beta_1",
                                  prior_lb, prior_ub)
            e_alpha_2 = pm.Uniform("estimate_alpha_2",
                                   prior_lb, prior_ub)
            e_beta_2 = pm.Uniform("estimate_beta_2",
                                  prior_lb, prior_ub)
            # Likelihood (sampling distribution) of observations
            Y_obs_1 = pm.Beta("Y_obs_1",
                            alpha=e_alpha_1,
                            beta=e_beta_1,
                            observed=self.drawn_vals_1)
            Y_obs_2 = pm.Beta("Y_obs_2",
                            alpha=e_alpha_2,
                            beta=e_beta_2,
                            observed=self.drawn_vals_2)
            #get means 2-1, so + is good
            mu_1 = pm.Deterministic("mu_1", e_alpha_1/(e_alpha_1+e_beta_1))
            mu_2 = pm.Deterministic("mu_2", e_alpha_2/(e_alpha_2+e_beta_2))
            mu_diff = pm.Deterministic("mu_diff", mu_2-mu_1)
            #get variance 1-2, so + is good
            var_1 = pm.Deterministic(
                "variance_1",
                (e_alpha_1*e_beta_1)/((e_alpha_1+e_beta_1)**2)*(e_alpha_1+e_beta_1+1))
            var_2 = pm.Deterministic(
                "variance_2",
                (e_alpha_2*e_beta_2)/((e_alpha_2+e_beta_2)**2)*(e_alpha_2+e_beta_2+1))
            var_diff = pm.Deterministic("var_diff",
                var_1-var_2)
        #prior predictive_checks
        if self.ppc:
            with bb_model:
                self.prior_pred = pm.sample_prior_predictive(draws=4000, random_seed=self.seed)
        #run inference
        compiled_model = nutpie.compile_pymc_model(bb_model)
        self.ests = nutpie.sample(compiled_model,chains=4,draws=1000,seed=self.seed,progress_bar=False)
        #posterior predictive_checks
        if self.ppc:
            with bb_model:
                self.posterior_pred = pm.sample_posterior_predictive(self.ests,progressbar=False,random_seed=self.seed)
        
      
def main():
        
    #find problematic_mu_diffs
    ds = []
    #draw n_pages
    zipf_a= 0.84
    zipf_n= 1000
    poisson_mu= 21

    for i in tqdm(range(start_seed,end_seed)):
        seed = i
        ab_vals = pm.draw(pm.Uniform.dist(0.1,10),4,random_seed=seed)
        #pages for origianl ocr drawn from a dist similar to data
        page_1 = c_zipf_pois_rng(1,zipf_a,zipf_n,poisson_mu,seed)[0]
        #pages for re-ocr are page_original + int(page_original * x), x~Normal(0,0.33)
        p2_rng=np.random.default_rng(seed=seed)
        p2_mod = p2_rng.normal(0,0.33)
        page_2 = page_1 + round(p2_mod * page_1)
        if page_1 < 1:
            page_1 = 1
        if page_2 < 1:
            page_2 = 1

        simdoc = Simulated_document_diff(alpha_1=ab_vals[0],
                                alpha_2=ab_vals[1],
                                beta_1=ab_vals[2],
                                beta_2=ab_vals[3],
                                n_pages_1=page_1,
                                n_pages_2=page_2,
                                seed=seed)
        try:
            simdoc.infer_params(0.1,10)
        except RuntimeError:
            continue
        #save
        var_diff = az.summary(simdoc.ests,round_to=4).get("mean").get("var_diff")
        lb_var_diff = az.summary(simdoc.ests,round_to=4).get("hdi_3%").get("var_diff")
        ub_var_diff = az.summary(simdoc.ests,round_to=4).get("hdi_97%").get("var_diff")
        mu_diff = az.summary(simdoc.ests,round_to=4).get("mean").get("mu_diff")
        lb_mu_diff = az.summary(simdoc.ests,round_to=4).get("hdi_3%").get("mu_diff")
        ub_mu_diff = az.summary(simdoc.ests,round_to=4).get("hdi_97%").get("mu_diff")

        true_var_diff = round(beta_var(ab_vals[0],ab_vals[2]) - beta_var(ab_vals[1],ab_vals[3]),4)
        # 2-1 so + is good
        true_mu_diff = round(beta_mu(ab_vals[1],ab_vals[3]) - beta_mu(ab_vals[0],ab_vals[2]),4)

        ab_vals = [round(i,4) for i in ab_vals]
        #result dict
        r_dict = {"seed":i,
                "a1":ab_vals[0],
                "a2":ab_vals[1],
                "b1":ab_vals[2],
                "b2":ab_vals[3],
                "pages_1":page_1,
                "pages_2":page_2,
                "true_var_diff": true_var_diff,
                "true_mu_diff": true_mu_diff,
                "var_diff":var_diff,
                "lb_var_diff":lb_var_diff,
                "ub_var_diff":ub_var_diff,
                "mu_diff":mu_diff,
                "lb_mu_diff":lb_mu_diff,
                "ub_mu_diff":ub_mu_diff}
        ds.append(r_dict)

    ds = Dataset.from_list(ds)
    ds.to_json(f"runs_with_p_{start_seed}_{end_seed}.json")

if __name__ == "__main__":
    main()