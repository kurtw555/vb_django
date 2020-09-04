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

step_count = {"lra": 6}


class DaskTasks:

    @staticmethod
    def setup_task(dataset_id, amodel_id, prepro_id=None):

        dataset = Dataset.objects.get(id=int(dataset_id))
        amodel = AnalyticalModel.objects.get(id=int(amodel_id))
        amodel.dataset = dataset.id
        amodel.save()

        client = Client(dask_scheduler)
        df = pd.read_csv(StringIO(bytes(dataset.data).decode())).drop("ID", axis=1)
        # add preprocessing to task
        fire_and_forget(client.submit(DaskTasks.execute_task, df, int(amodel.id), str(amodel.name), int(dataset_id)))
        #DaskTasks.execute_task(df, int(amodel.id), str(amodel.name), int(dataset_id))

    @staticmethod
    def execute_task(df, model_id, model_name, dataset_id):
        logger.info("Starting VB task -------- Model ID: {}; Model Type: {}; step 1/{}".format(model_id, model_name, step_count[model_name]))
        DaskTasks.update_status(model_id, "Loading and validating data", "1/{}".format(step_count[model_name]))

        dataset_m = Metadata(parent=Dataset.objects.get(id=dataset_id)).get_metadata("DatasetMetadata")
        target = "Response" if "response" not in dataset_m.keys() else dataset_m["response"]
        attributes = None if "attributes" not in dataset_m.keys() else dataset_m["attributes"]
        y = df[target]
        if attributes:
            attributes_list = json.loads(attributes.replace("\'", "\""))
            x = df[attributes_list]
        else:
            x = df.drop(target, axis=1)

        logger.info("Model ID: {}, loading hyper-parameters step 2/{}".format(model_id, step_count[model_name]))
        DaskTasks.update_status(model_id, "Loading hyper-parameters", "2/{}".format(step_count[model_name]))
        parameters = Metadata(parent=AnalyticalModel.objects.get(id=model_id)).get_metadata("ModelMetadata")

        if model_name == "lra":
            DaskTasks.execute_lra(model_id, parameters, x, y, step_count[model_name])

    @staticmethod
    def update_status(_id, status, stage, message=None, retry=5):
        if retry == 0:
            pass
        meta = 'ModelMetadata'
        try:
            amodel = AnalyticalModel.objects.get(id=int(_id))
            m = Metadata(parent=amodel, metadata=json.dumps({"status": status, "stage": stage, "message": message}))
            m.set_metadata(meta)
        except Exception as ex:
            logger.warning("Error attempting to save metadata update: {}".format(ex))
            DaskTasks.update_status(_id, status, stage, None, retry-1)

    @staticmethod
    def make_prediction(amodel_id, data=None):
        amodel = AnalyticalModel.objects.get(id=int(amodel_id))
        dataset = Dataset.objects.get(id=int(amodel.dataset))
        y_data = None

        df = pd.read_csv(StringIO(bytes(dataset.data).decode()))
        dataset_m = Metadata(parent=dataset).get_metadata("DatasetMetadata")
        target = "Response" if "response" not in dataset_m.keys() else dataset_m["response"]
        attributes = None if "attributes" not in dataset_m.keys() else dataset_m["attributes"]
        y = df[target]
        if attributes:
            attributes_list = json.loads(attributes.replace("\'", "\""))
            x = df[attributes_list]
        else:
            x = df.drop(target, axis=1)

        t = LinearRegressionAutomatedVB()
        t.set_data(x, y)
        x_train = t.x_train
        y_train = t.y_train
        x_data = t.x_test
        y_test = t.y_test.to_numpy().flatten()

        if data is not None:
            x_data = data
        model = pickle.loads(amodel.model)
        response = {
            "results": model.predict(x_data),
            "train_score": model.score(x_train, y_train)
        }
        if data is None:
            response["residuals"] = y_test - response["results"]
            response["test_score"] = model.score(x_data, y_test)
        return response

    @staticmethod
    def execute_lra(model_id, parameters, x, y, step_count):
        DaskTasks.update_status(model_id, "Initializing automated linear regressor", "3/{}".format(step_count))
        logger.info("Model ID: {}, Initializing automated linear regressor. step 3/{}".format(model_id, step_count))
        t = LinearRegressionAutomatedVB()
        t.validate_h_params(parameters)
        try:
            t.set_data(x, y)
        except Exception as ex:
            logger.warning("Model ID: {}, Error setting data. step 3/{}. Error: {}".format(model_id, step_count, ex))
            DaskTasks.update_status(
                model_id,
                "Failed to complete",
                "-1/{}".format(step_count), "Error setting data. Issue with input data"
            )
            return
        logger.info("Model ID: {}, Constructing pipeline. step 4/{}".format(model_id, step_count))
        DaskTasks.update_status(model_id, "Constructing pipeline", "4/{}".format(step_count))
        try:
            t.set_pipeline()
        except Exception as ex:
            logger.warning("Model ID: {}, Error setting data. step 4/{}. Error: {}".format(model_id, step_count, ex))
            DaskTasks.update_status(
                model_id,
                "Failed to complete",
                "-1/{}".format(step_count), "Error setting the pipeline."
            )
            return
        logger.info("Model ID: {}, Saving fitted model. step 5/{}".format(model_id, step_count))
        DaskTasks.update_status(model_id, "Saving fitted model", "5/{}".format(step_count))

        saved = False
        save_tries = 0
        err = None
        while not saved and save_tries < 5:
            try:
                amodel = AnalyticalModel.objects.get(id=model_id)
                amodel.model = pickle.dumps(t.lr_estimator)
                amodel.save()
                saved = True
            except Exception as ex:
                logger.warning("Error attempting to save pickled model: {}".format(ex))
                err = ex
                time.sleep(.5)
                save_tries += 1
        if saved:
            logger.info("Model ID: {}, Completed. step 6/{}".format(model_id, step_count))
            DaskTasks.update_status(model_id, "Complete", "6/{}".format(step_count))
        else:
            logger.warning("Model ID: {}, Error pickling model. step 5/{}. Error: {}".format(model_id, step_count, err))
            DaskTasks.update_status(
                model_id,
                "Failed to complete",
                "-1/{}".format(step_count), "Error saving the fitted model"
            )
