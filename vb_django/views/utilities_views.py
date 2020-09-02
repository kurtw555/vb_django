from vb_django.app.linear_regression import LinearRegressionAutomatedVB
from django.http import HttpResponse, JsonResponse


def analytical_model_details(request):
    """
    Returns the details for each of the implemented analytical models and their corresponding hyperparameters
    """
    details = []

    # Linear Regression Automated class
    lra = LinearRegressionAutomatedVB()
    details.append(lra.get_info())

    return JsonResponse(details, safe=False)
