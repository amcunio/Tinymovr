
''' Tinymovr endpoint module.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
'''
from typing import Dict, Any
from pint import Quantity as _Q
from tinymovr.units import get_registry

ureg = get_registry()


class Endpoint:

    def __init__(self, node_id, iface):
        # Note: Use object setter method to avoid infinite recursion
        object.__setattr__(self, "node_id", node_id)
        object.__setattr__(self, "iface", iface)
        object.__setattr__(self, "codec", iface.get_codec())


class ReadEndpoint(Endpoint):

    def __init__(self, node_id, iface, read_ep: Dict):
        # Note: Use object setter method to avoid infinite recursion
        object.__setattr__(self, "attrib_cache", {})
        object.__setattr__(self, "read_ep", read_ep)
        object.__setattr__(self, "data_cache", [])
        Endpoint.__init__(self, node_id, iface)

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
        if attrib in self.read_ep["labels"]:
            if attrib not in self.attrib_cache:
                data = self.get_data()
                i_attrib = self.read_ep["labels"].index(attrib)
                val = data[i_attrib]
                if "units" in self.read_ep:
                    val = val * ureg(self.read_ep["units"][i_attrib])
                self.attrib_cache[attrib] = val
                return val
            return self.attrib_cache[attrib]
        raise AttributeError(attrib)   

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
        # Note: Use object setter method to avoid infinite recursion
        object.__setattr__(self, "write_ep", write_ep)
        Endpoint.__init__(self, node_id, iface)
            
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
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.write_ep["labels"]:
            self(**{name:value})
        else:
            return super().__setattr__(name, value)

    def __dir__(self):
        return self.write_ep["labels"]


class MixedEndpoint(ReadEndpoint, WriteEndpoint):

    def __init__(self, node_id, iface, read_ep: Dict, write_ep: Dict):
        ReadEndpoint.__init__(self, node_id, iface, read_ep)
        WriteEndpoint.__init__(self, node_id, iface, write_ep)
        # Note: At this point subclassed setter method may be used
        self.all_labels = sorted(list(set(self.read_ep["labels"])) + list(set(self.write_ep["labels"])))

    def __dir__(self):
        return self.all_labels