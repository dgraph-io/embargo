#
#  Copyright (C) 2014 Dell, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class EmbargoError(Exception):
    """Expected error within Embargo
    """


class EmbargoConfigError(EmbargoError):
    """Error in configuration
    """


class EmbargoUsageError(EmbargoError):
    """Error in configuration
    """


class EmbargoContainerConflictError(EmbargoError):
    """Error on conflicting containers
    """


class AlreadyInitializedError(EmbargoError):
    """Embargo already created in this context
    """


class NotInitializedError(EmbargoError):
    """Embargo not created in this context
    """


class InconsistentStateError(EmbargoError):
    """Embargo state is inconsistent (partially created or destroyed)
    """


class InsufficientPermissionsError(EmbargoError):
    """Embargo is executed with insufficient permissions
    """


class InvalidEmbargoName(EmbargoError):
    """Invalid embargo name
    """


class DockerContainerNotFound(EmbargoError):
    """Docker container not found
    """


class HostExecError(EmbargoError):
    """Error in host command
    """

    def __init__(self, message, output=None, exit_code=None):
        super(HostExecError, self).__init__(message)
        self.output = output
        self.exit_code = exit_code

    def __str__(self):
        message = super(HostExecError, self).__str__()
        if self.exit_code is not None and self.output is not None:
            return "%s rc=%s output=%s" % (message, self.exit_code, self.output)
        if self.output is not None:
            return "%s output=%s" % (message, self.output)
        return message


class EmbargoStateTransitionError(EmbargoError):
    """The state machine was given an invalid event.  Based on the state that
     it is in and the event received the state machine could not process the
     event"""
    def __init__(self, current_state, event, msg=None):
        super(EmbargoStateTransitionError, self).__init__(msg)
        self.state = current_state
        self.event = event

    def __str__(self):
        return "Error processing the event %s when in the %s state" % (
            self.event, self.state)


class EmbargoHttpError(EmbargoError):
    """Errors from the REST API
    """
    def __init__(self, http_code, http_msg, msg=None):
        super(EmbargoStateTransitionError, self).__init__(msg)
        self.http_code = http_code
        self.http_msg = http_msg
