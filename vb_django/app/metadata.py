from django.apps import apps
from vb_django import models as vbm
import json


class Metadata:
    """

    """
    def __init__(self, parent, metadata=None):
        self.parent = parent
        self.metadata = json.loads(metadata) if metadata else {}

    def get_metadata(self, metadata_type):
        metadata_model = apps.get_model("vb_django", metadata_type)
        metadata = metadata_model.objects.filter(base_id=self.parent)
        meta = {}
        for m in metadata:
            meta[m.name] = m.value
        return meta

    def set_metadata(self, metadata_type):
        metadata_model = apps.get_model("vb_django", metadata_type)
        metadata = metadata_model.objects.filter(base_id=self.parent)
        for m in metadata:
            m.delete()
        for k, v in self.metadata.items():
            if type(v) == object:
                v = json.dumps(v)
            elif type(v) != str:
                v = str(v)
            meta = metadata_model.objects.create(base_id=self.parent, name=k, value=v)
            meta.save()
        meta = self.get_metadata(metadata_type)
        return meta

    def delete_metadata(self, metadata_type):
        metadata_model = apps.get_model("vb_django", metadata_type)
        metadata = metadata_model.objects.filter(base_id=self.parent)
        for m in metadata:
            m.delete()
