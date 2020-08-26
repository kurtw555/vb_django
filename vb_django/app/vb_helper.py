import numpy as np
from sklearn.linear_model import ElasticNetCV, Lars
from sklearn.base import BaseEstimator, TransformerMixin


class ShrinkBigKTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, max_k=500, selector=None):
        self.max_k = max_k
        if selector is None:
            self.selector = 'Lars'
        else:
            self.selector = selector

    def fit(self, X, y):
        assert not y is None, f'y:{y}'
        if self.selector == 'Lars':
            selector = Lars(fit_intercept=1, normalize=1, n_nonzero_coefs=self.max_k)
        elif self.selector == 'elastic-net':
            selector = ElasticNetCV()
        k = X.shape[1]
        selector.fit(X, y)
        self.col_select = np.arange(k)[selector.coef_ > 0]
        return self

    def transform(self, X):
        return X[:, self.col_select]


class LogMinPlus1_T(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        self.x_min_ = np.min(X)
        return self

    def transform(self, X, y=None):
        return np.log(X - self.x_min_ + 1)

    def inverse_transform(self, X, y=None):
        return np.exp(X) - 1 + self.x_min_


class LogP1_T(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        xmin = X.min()
        if xmin < 0:
            self.min_shift_ = -xmin
        else:
            self.min_shift_ = 0
        return self

    def transform(self, X, y=None):

        return np.log1p(X + self.min_shift_)

    def inverse_transform(self, X, y=None):
        return np.expm1(X) - self.min_shift_


class LogMinus_T(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return np.sign(y) * np.log(np.abs(y))

    def inverse_transform(self, X, y=None):
        return np.exp(X)


class Exp_T(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        pass

    def transform(self, X, y=None):
        return np.exp(X)

    def inverse_transform(self, X, y=None):
        xout = np.zeros(X.shape)
        xout[X > 0] = np.log(X[X > 0])
        return xout


class None_T(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X

    def inverse_transform(self, X):
        return X