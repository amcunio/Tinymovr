
''' Tinymovr state endpoint module.

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
from tinymovr.endpoint import MixedEndpoint

from tinymovr.constants import (ControlStates,
    ControlModes, ErrorIDs, error_descriptions)

class State(MixedEndpoint):

    @property
    def state(self):
        return ControlStates(self.get_data()[1])

    @property
    def mode(self):
        return ControlModes(self.get_data()[2])

    @property
    def errors(self):
        if sum(self.get_data()[-5:]) > 0:
            return [ErrorIDs(e) for e in self.get_data()[-5:] if e > 0]
        elif (self.get_data()[0] > 0):
            return [ErrorIDs(self.get_data()[0])]
        return None

    @property
    def error_descriptions(self):
        if self.errors:
            return [error_descriptions[e] for e in self.errors]
        return None

    def __dir__(self):
        return ['state', 'mode', 'errors', 'error_descriptions']

    def _repr_pretty_(self, p, cycle):
        strings = [
            'State: {}; Mode: {}'.format(str(ControlStates(self.get_data()[1])), str(ControlModes(self.data[2]))),
            'Errors:'
        ]
        if self.errors:
            strings.extend(['  ' + str(e) + '(' + str(int(e)) + '): ' + d for e, d in zip(self.errors, self.error_descriptions)])
        else:
            strings.append('  None')
        p.text('\n'.join(strings))
