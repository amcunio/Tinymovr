
''' Tinymovr CAN bus interface module.

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
import math
import can
from typing import Tuple, Dict, List
import serial
from serial.tools import list_ports
import logging

from tinymovr.iface import IFace
from tinymovr.iface.can_bus import can_descriptors
from tinymovr.codec import MultibyteCodec


CAN_EP_SIZE: int = 6
CAN_EP_MASK: int = int(math.pow(2, CAN_EP_SIZE) - 1)

can_devices: Dict[str, tuple] = {
    "slcan": ("canable", "cantact"),
    "robotell": ("CP210",),
}


class CANBus(IFace):
    """
    Class implementing a CAN bus interface
    """

    def __init__(self, bus):
        self.bus = bus

    def get_codec(self):
        return MultibyteCodec()

    def get_ep_descriptors(self) -> Dict:
        return can_descriptors

    def send(self, node_id: int, endpoint_id: int, payload: bytearray = None):
        rtr: bool = False if payload and len(payload) else True
        self.bus.send(create_frame(node_id, endpoint_id, rtr, payload))

    def receive(self, node_id: int, endpoint_id: int, timeout: float = 0.1):
        frame_id: int = create_node_id(node_id, endpoint_id)
        frame: can.Message = self.bus.recv(timeout=timeout)
        if frame:
            if frame.arbitration_id == frame_id:
                return frame.data
            else:
                error_data = extract_node_message_id(frame_id)
                error_data += extract_node_message_id(frame.arbitration_id)
                raise IOError("Received id mismatch. Expected: Node: {}, Endpoint:{}; Got: Node: {}, Endpoint:{}".format(
                    *error_data))
        else:
            raise TimeoutError()


def create_frame(
    node_id: int, endpoint_id: int, rtr: bool = False, payload: bytearray = None
) -> can.Message:
    """
    Generate and return a CAN frame using python-can Message class
    """
    return can.Message(
        arbitration_id=create_node_id(node_id, endpoint_id),
        is_extended_id=False,
        is_remote_frame=rtr,
        data=payload,
    )


def create_node_id(node_id: int, endpoint_id: int) -> int:
    """
    Generate a CAN id from node and endpoint ids
    """
    return (node_id << CAN_EP_SIZE) | endpoint_id


def extract_node_message_id(arbitration_id: int) -> Tuple[int, int]:
    node_id = arbitration_id >> CAN_EP_SIZE & 0xFF
    message_id = arbitration_id & CAN_EP_MASK
    return node_id, message_id


def guess_channel(bustype_hint: str) -> str:
    """
    Tries to guess a channel based on an interface hint.
    """
    device_strings: List[str] = [s.lower() for s in can_devices[bustype_hint]]
    ports: List[str] = []
    for p in serial.tools.list_ports.comports():
        desc_lower: str = p.description.lower()
        if any([s in desc_lower for s in device_strings]):
            ports.append(p.device)
    if not ports:
        raise IOError("Could not autodiscover CAN channel")
    if len(ports) > 1:
        logging.warning("Multiple channels discovered - using the first")

    return ports[0]