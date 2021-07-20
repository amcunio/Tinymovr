from tinymovr.endpoint.endpoint import Endpoint, ReadEndpoint, WriteEndpoint, MixedEndpoint
from tinymovr.endpoint.state import State

endpoint_types = {
    "default_read": ReadEndpoint,
    "default_write": WriteEndpoint,
    "default_mixed": MixedEndpoint,
    "state": State
}

def endpoint_class_for_descriptor(label, node_id, iface, desc):
    
    
    try:
        ep = endpoint_types[label]
        if "write" in desc and "read" in desc:
            return ep(node_id, iface, desc["read"], desc["write"])
        elif "write" in desc:
            return ep(node_id, iface, desc["write"])
        elif "read" in desc:
            return ep(node_id, iface, desc["read"])
    except KeyError:
        if "write" in desc and "read" in desc:
            return MixedEndpoint(node_id, iface, desc["read"], desc["write"])
        elif "write" in desc:
            return WriteEndpoint(node_id, iface, desc["write"])
        elif "read" in desc:
            return ReadEndpoint(node_id, iface, desc["read"])
    raise ValueError("No valid read/write accessors in endpoint")
