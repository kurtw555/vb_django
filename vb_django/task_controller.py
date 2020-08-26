from dask.distributed import Client, fire_and_forget
from dask import delayed
from vb_django.models import Dataset, AnalyticalModel
from io import StringIO
from vb_django.app.linear_regression import LinearRegressionAutomatedVB
from vb_django.app.metadata import Metadata
import pickle
import pandas as pd
import os
import socket


dask_scheduler = os.getenv("DASK_SCHEDULER", "tcp://" + socket.gethostbyname(socket.gethostname()) + ":8786")
target = "Response"


class DaskTasks:

    @staticmethod
    def setup_task(dataset_id, amodel_id, prepro_id=None):

        dataset = Dataset.objects.get(id=int(dataset_id))
        amodel = AnalyticalModel.objects.get(id=int(amodel_id))
        amodel.dataset = dataset.id
        amodel.save()

        dask_client = Client(dask_scheduler)
        df = pd.read_csv(StringIO(dataset.data.decode()))
        # add preprocessing to task
        task = dask_client.submit(DaskTasks.execute_task, df, amodel.id, amodel.name)
        fire_and_forget(task)

    @staticmethod
    def execute_task(df, model_id, model_name):
        DaskTasks.update_status(model_id, "Loading and validating data", "1/5")
        y = df[target]
        x = df.drop(target, axis=1)
        if model_name == "lra":
            DaskTasks.update_status(model_id, "Initializing automated linear regressor", "2/5")
            t = LinearRegressionAutomatedVB()
            t.set_data(x, y)
            DaskTasks.update_status(model_id, "Constructing pipeline", "3/5")
            t.set_pipeline()
            DaskTasks.update_status(model_id, "Saving fitted model", "4/5")
            amodel = AnalyticalModel.objects.get(id=model_id)
            amodel.model = pickle.dumps(t.lr_estimator)
            DaskTasks.update_status(model_id, "Complete", "5/5")

    @staticmethod
    def update_status(_id, status, stage):
        meta = 'ModelMetadata'
        amodel = AnalyticalModel.objects.get(id=int(_id))
        m = Metadata(parent=amodel, metadata={"status": status, "stage": stage})
        m.set_metadata(meta)

    @staticmethod
    def make_prediction(amodel_id, data=None):
        amodel = AnalyticalModel.objects.get(id=int(amodel_id))
        dataset = Dataset.objects.get(id=int(amodel.dataset))
        y = None
        if data is None:
            df = pd.read_csv(StringIO(dataset.data.decode()))
            y = df[target]
            x = df.drop(target, axis=1)
            t = LinearRegressionAutomatedVB()
            t.set_data(x, y)
            data = t.x_test
        model = pickle.load(amodel.model)
        results = model.predict(data)
        residuals = y - results.to_numpy().flatten() if y else y
        return {"results": results, "residuals": residuals}
