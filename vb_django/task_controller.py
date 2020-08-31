import vb_django.dask_django
from dask.distributed import Client, fire_and_forget
from vb_django.models import Dataset, AnalyticalModel
from io import StringIO
from vb_django.app.linear_regression import LinearRegressionAutomatedVB
from vb_django.app.metadata import Metadata
from dask import delayed
import pickle
import pandas as pd
import os
import json
import socket
import logging
import time

logger = logging.getLogger("vb_dask")
logger.setLevel(logging.INFO)

dask_scheduler = os.getenv("DASK_SCHEDULER", "tcp://" + socket.gethostbyname(socket.gethostname()) + ":8786")
target = "Response"


class DaskTasks:

    @staticmethod
    def setup_task(dataset_id, amodel_id, prepro_id=None):

        dataset = Dataset.objects.get(id=int(dataset_id))
        amodel = AnalyticalModel.objects.get(id=int(amodel_id))
        amodel.dataset = dataset.id
        amodel.save()

        client = Client(dask_scheduler)
        df = pd.read_csv(StringIO(dataset.data.decode())).drop("ID", axis=1)
        # add preprocessing to task
        fire_and_forget(client.submit(DaskTasks.execute_task, df, int(amodel.id), str(amodel.name)))
        # DaskTasks.execute_task(df, int(amodel.id), str(amodel.name))

    @staticmethod
    def execute_task(df, model_id, model_name):
        logger.info("Starting VB task")
        DaskTasks.update_status(model_id, "Loading and validating data", "1/5")
        y = df[target]
        x = df.drop(target, axis=1)
        logger.info("Model ID: {}; Model Type: {}; step 1/5".format(model_id, model_name))
        if model_name == "lra":
            DaskTasks.update_status(model_id, "Initializing automated linear regressor", "2/5")
            logger.info("Model ID: {}, Initializing automated linear regressor. step 2/5".format(model_id))
            t = LinearRegressionAutomatedVB()
            t.set_data(x, y)
            logger.info("Model ID: {}, Constructing pipeline. step 3/5".format(model_id))
            DaskTasks.update_status(model_id, "Constructing pipeline", "3/5")
            t.set_pipeline()
            logger.info("Model ID: {}, Saving fitted model. step 4/5".format(model_id))
            DaskTasks.update_status(model_id, "Saving fitted model", "4/5")

            saved = False
            save_tries = 0
            while not saved and save_tries < 5:
                try:
                    amodel = AnalyticalModel.objects.get(id=model_id)
                    amodel.model = pickle.dumps(t.lr_estimator)
                    amodel.save()
                    saved = True
                except Exception as ex:
                    logger.warning("Error attempting to save pickled model: {}".format(ex))
                    time.sleep(1)
                    save_tries += 1

            logger.info("Model ID: {}, Completed. step 5/5".format(model_id))
            DaskTasks.update_status(model_id, "Complete", "5/5")

    @staticmethod
    def update_status(_id, status, stage, retry=5):
        if retry == 0:
            pass
        meta = 'ModelMetadata'
        try:
            amodel = AnalyticalModel.objects.get(id=int(_id))
            m = Metadata(parent=amodel, metadata=json.dumps({"status": status, "stage": stage}))
            m.set_metadata(meta)
        except Exception as ex:
            logger.warning("Error attempting to save metadata update: {}".format(ex))
            DaskTasks.update_status(_id, status, stage, retry-1)

    @staticmethod
    def make_prediction(amodel_id, data=None):
        amodel = AnalyticalModel.objects.get(id=int(amodel_id))
        dataset = Dataset.objects.get(id=int(amodel.dataset))
        y_data = None
        if data is None:
            df = pd.read_csv(StringIO(dataset.data.decode()))
            y = df[target]
            x = df.drop(target, axis=1).drop("ID", axis=1)
            t = LinearRegressionAutomatedVB()
            t.set_data(x, y)
            data = t.x_test
            y_data = t.y_test.to_numpy().flatten()
        model = pickle.loads(amodel.model)
        results = model.predict(data)
        residuals = None if y_data is None else y_data - results
        return {"results": results, "residuals": residuals}
