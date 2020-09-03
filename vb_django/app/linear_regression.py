from sklearn.model_selection import RepeatedKFold, GridSearchCV, train_test_split
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.compose import TransformedTargetRegressor
from vb_django.app.vb_helper import ShrinkBigKTransformer, None_T, LogP1_T
from dask.distributed import Client
# from dask import array as darray
import pandas as pd
import numpy as np
import joblib
import warnings
import os
import socket
import time
import logging


logger = logging.getLogger("vb_dask")
logger.setLevel(logging.INFO)


class LinearRegressionVB:

    def __init__(self):
        pass


class LinearRegressionAutomatedVB:
    name = "Automated Linear Regression"
    id = "lra"
    description = "Automated pipeline with feature evaluation and selection for a linear regression estimator."

    def __init__(self, test_split=0.2, cv_folds=10, cv_reps=10, seed=42, one_out=False):
        self.hyperparameters = {
            'test_split': 0.2,
            'cv_folds': 10,
            'cv_reps': 10,
            'random_seed': 42,
            'one_out': False
        }
        self.start_time = time.time()
        self.test_split = test_split
        self.cv_folds = cv_folds
        self.cv_reps = cv_reps
        self.seed = seed
        self.one_out = one_out

        self.k = None
        self.n = None
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None

        self.lr_estimator = None
        self.attr = None
        self.results = None
        self.residuals = None

    def validate_h_params(self, parameters):
        for h in self.hyperparameters.keys():
            if h in parameters.keys():
                self.hyperparameters[h] = parameters[h]
        self.test_split = float(self.hyperparameters['test_split'])
        self.cv_folds = int(self.hyperparameters['cv_folds'])
        self.cv_reps = int(self.hyperparameters['cv_reps'])
        self.seed = int(self.hyperparameters['random_seed'])
        self.one_out = bool(self.hyperparameters['one_out'])

    def set_data(self, x, y):
        if self.one_out:
            self.x_train, self.x_test, self.y_train, self.y_test = (x, x, y, y)
        else:
            self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
                x, y,
                test_size=self.test_split,
                random_state=self.seed
            )
        self.n, self.k = self.x_train.shape

    def set_pipeline(self):
        warnings.simplefilter('ignore')

        transformer_list = [None_T(), LogP1_T()]
        steps = [
            ('scaler', StandardScaler()),
            ('shrink_k1', ShrinkBigKTransformer()),
            ('polyfeat', PolynomialFeatures(interaction_only=1)),
            ('shrink_k2', ShrinkBigKTransformer(selector='elastic-net')),
            ('reg', make_pipeline(StandardScaler(), LinearRegression(fit_intercept=1)))
        ]

        inner_params = {'polyfeat__degree': [2]}
        if self.k > 4:
            interv = -(-self.k // 3)
            np.arange(2, self.k + interv, interv)
            inner_params['shrink_k1__max_k'] = np.arange(4, self.k, 4)
        inner_cv = RepeatedKFold(n_splits=5, n_repeats=1, random_state=self.seed)
        X_T_pipe = GridSearchCV(Pipeline(steps=steps), param_grid=inner_params, cv=inner_cv)

        Y_T_X_T_pipe = Pipeline(steps=[('ttr', TransformedTargetRegressor(regressor=X_T_pipe))])
        Y_T__param_grid = {'ttr__transformer': transformer_list}
        lin_reg_Xy_transform = GridSearchCV(Y_T_X_T_pipe, param_grid=Y_T__param_grid, cv=inner_cv)

        self.lr_estimator = lin_reg_Xy_transform
        self.lr_estimator.fit(self.x_train, self.y_train)
        self.attr = pd.DataFrame(self.lr_estimator.cv_results_)
        # generates the model that is saved
        logger.info("Total execution time: {} sec".format(round(time.time() - self.start_time, 3)))

    def predict(self, x_test=None):
        # obsolete within dask stack
        x_test = x_test if x_test else self.x_test
        self.results = self.lr_estimator.predict(x_test)
        self.residuals = self.results - self.y_test.to_numpy().flatten()

    def get_info(self):
        details = {
            "name": LinearRegressionAutomatedVB.name,
            "id": LinearRegressionAutomatedVB.id,
            "description": LinearRegressionAutomatedVB.description,
            "hyperparameters": self.hyperparameters
        }
        return details
