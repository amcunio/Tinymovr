
from typing import Dict
from pint import Quantity as _Q
from tinymovr.units import get_registry

ureg = get_registry()


class Endpoint:

    def __init__(self, node_id, iface):
        self.node_id = node_id
        self.iface = iface
        self.codec = self.iface.get_codec()


class ReadEndpoint(Endpoint):

    def __init__(self, node_id, iface, read_ep: Dict):
        Endpoint.__init__(self, node_id, iface)
        self.read_ep = read_ep
        self.attrib_cache = {}
        self.data_cache = []

    def clear_cache(self):
        self.attrib_cache.clear()
        self.data_cache.clear()

    def get_data(self):
        if len(self.data_cache) == 0:
            self.iface.send(self.node_id, self.read_ep["ep_id"])
            response = self.iface.receive(self.node_id, self.read_ep["ep_id"])
            self.data_cache = self.codec.deserialize(response, *self.read_ep["types"])
        return self.data_cache

    def __getattr__(self, attrib):
        if attrib not in self.attrib_cache:
            try:
                assert attrib in self.read_ep["labels"]
            except AssertionError:
                import ipdb; ipdb.set_trace()
            data = self.get_data()
            i_attrib = self.read_ep["labels"].index(attrib)
            val = data[i_attrib]
            if "units" in self.read_ep:
                val = val * ureg(self.read_ep["units"][i_attrib])
            self.attrib_cache[attrib] = val
            return val
        return self.attrib_cache[attrib]        

    def __dir__(self):
        return self.read_ep["labels"]

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text('Endpoint(...)')
        else:
            data = self.get_data()
            if "units" in self.read_ep:
                data = [v * ureg(u) for v, u in zip (data, self.read_ep["units"])]
            with p.group(8, 'Endpoint([', '])'):
                for idx, item in enumerate(zip(data, self.read_ep["labels"])):
                    if idx:
                        p.text(',')
                        p.breakable()
                    p.pretty(item)


class WriteEndpoint(Endpoint):

    def __init__(self, node_id, iface, write_ep: Dict):
        Endpoint.__init__(self, node_id, iface)
        self.write_ep = write_ep
            
    def __call__(self, *args, **kwargs):
        assert len(args) == 0 or len(kwargs) == 0
        if len(kwargs) > 0:
            assert "labels" in self.write_ep
            inputs = [
                kwargs[k] if k in kwargs else self.write_ep["defaults"][k]
                for k in self.write_ep["labels"]
            ]
        elif len(args) > 0:
            inputs = [
                args[i] if i < len(args) else self.write_ep["defaults"][k]
                for i, k in enumerate(self.write_ep["labels"])
            ]
        else:
            inputs = []
        if "units" in self.write_ep:
            inputs = [
                v.to(self.write_ep["units"][i]).magnitude if isinstance(v, _Q) else v
                for i, v in enumerate(inputs)
            ]
        payload = None
        if len(inputs) > 0:
            payload = self.codec.serialize(inputs, *self.write_ep["types"])
        self.iface.send(self.node_id, self.write_ep["ep_id"], payload=payload)


class MixedEndpoint(ReadEndpoint, WriteEndpoint):

    def __init__(self, node_id, iface, read_ep: Dict, write_ep: Dict):
        ReadEndpoint.__init__(self, node_id, iface, read_ep)
        WriteEndpoint.__init__(self, node_id, iface, write_ep)

