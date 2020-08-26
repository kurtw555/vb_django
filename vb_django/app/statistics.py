from sklearn.linear_model import LinearRegression
import sklearn.metrics as skm
import numpy as np
import scipy.stats as scs
import warnings


class DatasetStatistics:
    def __init__(self, dataset):
        self.dataset = dataset

    def calculate_statistics(self, response):
        warnings.simplefilter('ignore')
        stats = {}
        r_data = self.dataset[response].to_numpy().flatten()
        for name, data in self.dataset.items():
            values = data.to_numpy().flatten()
            lg = LinearRegression(fit_intercept=True, normalize=False).fit(values.reshape(-1, 1), r_data)
            p_values = lg.predict(values.reshape(-1, 1))
            res = values - p_values
            ad = scs.anderson(res)
            if ad[0] < 2:
                p = 1. - np.exp(-1.2337141 / ad[0]) / np.sqrt(ad[0]) * (2.00012 + (
                            .247105 - (.0649821 - (.0347962 - (.011672 - .00168691 * ad[0]) * ad[0]) * ad[0]) * ad[0]) * ad[0])
            else:
                p = 1. - np.exp(-1. * np.exp(
                    1.0776 - (2.30695 - (.43424 - (.082433 - (.008056 - .0003146 * ad[0]) * ad[0]) * ad[0]) * ad[0]) * ad[0]))
            v_stats = {
                "Variable Name": name,
                "Row Count": data.shape[0],
                "Maximum Value": np.float64(np.max(values)),
                "Minimum Value": np.float64(np.min(values)),
                "Average Value": np.average(values),
                "Unique Values": np.unique(values).shape[0],
                "Zero Count": values.shape[0] - np.count_nonzero(values),
                "Median Value": np.median(values),
                "Data Range": np.float64(np.ptp(values)),
                "A-D Statistics": 0 if np.isnan(ad[0]) else ad[0],
                "A-D Stat P-Value": 0 if np.isnan(p) else p,
                "Mean Value": np.mean(values),
                "Standard Deviation": np.std(values),
                "Variance": np.var(values),
                "Kurtosis": scs.kurtosis(values),
                "Skewness": scs.skew(values)
            }
            stats[name] = v_stats
        return stats


def evaluate_results(predicted, actual):
    metrics = {
        "accuracy": skm.accuracy_score(actual, predicted),
        "confusion_matrix": skm.confusion_matrix(actual, predicted),
        "max_error": skm.max_error(actual, predicted),
        "mean_absolute_error": skm.mean_absolute_error(actual, predicted),
        "mean_squared_error": skm.mean_squared_error(actual, predicted),
        "root_mean_squared_error": skm.mean_squared_error(actual, predicted, squared=False),
        "r2": skm.r2_score(actual, predicted)
    }
    return metrics
