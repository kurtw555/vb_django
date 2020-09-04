from django.apps import apps
import json


class Metadata:
    """

    """
    def __init__(self, parent, metadata=None):
        self.parent = parent
        self.metadata = json.loads(metadata) if metadata else {}

    def get_metadata(self, metadata_type, names=None):
        metadata_model = apps.get_model("vb_django", metadata_type)
        if names:
            metadata = []
            for n in names:
                m = metadata_model.objects.filter(base_id=self.parent, name=n).values()
                if len(m) > 0:
                    metadata.append(m[0])
        else:
            metadata = metadata_model.objects.filter(base_id=self.parent).values()
        meta = {}
        for m in metadata:
            meta[m['name']] = m['value']
        return meta

    def set_metadata(self, metadata_type):
        metadata_model = apps.get_model("vb_django", metadata_type)
        for k, v in self.metadata.items():
            if type(v) == object:
                v = json.dumps(v)
            elif type(v) != str:
                v = str(v)
            current_metadata = metadata_model.objects.filter(base_id=self.parent, name=k)
            if len(current_metadata) == 0:
                meta = metadata_model.objects.create(base_id=self.parent, name=k, value=v)
                meta.save()
            else:
                current_metadata[0].value = v
                current_metadata[0].save()
        meta = self.get_metadata(metadata_type)
        return meta

    def delete_metadata(self, metadata_type, names=None):
        metadata_model = apps.get_model("vb_django", metadata_type)
        if names:
            metadata = []
            for n in names:
                metadata.append(metadata_model.objects.filter(base_id=self.parent, name=n))
        else:
            metadata = metadata_model.objects.filter(base_id=self.parent)
        for m in metadata:
            m.delete()
