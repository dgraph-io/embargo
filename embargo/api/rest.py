#
#  Copyright (C) 2016 Dell, Inc.
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
import signal
import sys
import traceback

from flask import Flask, abort, jsonify, request, Response
from gevent.pywsgi import WSGIServer

from .. import chaos
from .. import errors
from ..api.manager import EmbargoManager
from ..config import EmbargoConfig
from ..errors import DockerContainerNotFound
from ..errors import InvalidEmbargoName


app = Flask(__name__)


def stack_trace_handler(signum, frame):
    code = []
    code.append(" === Stack trace Begin === ")
    for threadId, stack in list(sys._current_frames().items()):
        code.append("##### Thread %s #####" % threadId)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('\tFile: "%s", line %d, in %s' %
                        (filename, lineno, name))
        if line:
            code.append(line)
    code.append(" === Stack trace End === ")
    app.logger.warn("\n".join(code))


def start(data_dir='/tmp', port=5000, debug=False, host_exec=None):
    signal.signal(signal.SIGUSR2, stack_trace_handler)

    EmbargoManager.set_data_dir(data_dir)
    if host_exec:
        EmbargoManager.set_host_exec(host_exec)
    app.debug = debug
    http_server = WSGIServer(('', port), app)
    http_server.serve_forever()


############## ERROR HANDLERS ##############


@app.errorhandler(415)
def unsupported_media_type(error):
    return 'Content-Type must be application/json', 415


@app.errorhandler(404)
def embargo_name_not_found(error):
    return 'Embargo name not found', 404


@app.errorhandler(InvalidEmbargoName)
def invalid_embargo_name(error):
    return 'Invalid embargo name', 400


@app.errorhandler(DockerContainerNotFound)
def docker_container_not_found(error):
    return 'Docker container not found', 400


################### ROUTES ###################


@app.route("/embargo")
def list_all():
    embargos = EmbargoManager.get_all_embargo_names()
    return jsonify(embargos=embargos)


@app.route("/embargo/<name>", methods=['POST'])
def create(name):
    if not request.headers['Content-Type'] == 'application/json':
        abort(415)

    if EmbargoManager.embargo_exists(name):
        return 'Embargo name already exists', 400

    # This will abort with a 400 if the JSON is bad
    data = request.get_json()
    config = EmbargoConfig.from_dict(data)
    EmbargoManager.store_config(name, config)

    b = EmbargoManager.get_embargo(name)
    containers = b.create()

    return '', 204


@app.route("/embargo/<name>", methods=['PUT'])
def add(name):
    if not request.headers['Content-Type'] == 'application/json':
        abort(415)

    if not EmbargoManager.embargo_exists(name):
        abort(404)

    data = request.get_json()
    containers = data.get('containers')
    b = EmbargoManager.get_embargo(name)
    b.add_container(containers)

    return '', 204


@app.route("/embargo/<name>/action", methods=['POST'])
def action(name):
    if not request.headers['Content-Type'] == 'application/json':
        abort(415)

    if not EmbargoManager.embargo_exists(name):
        abort(404)

    commands = ['start', 'stop', 'restart', 'kill']
    data = request.get_json()
    command = data.get('command')
    container_names = data.get('container_names')
    if command is None:
        return "'command' not found in body", 400
    if command not in commands:
        error_str = "'%s' is not a valid action" % command
        return error_str, 400
    if container_names is None:
        return "'container_names' not found in body", 400

    b = EmbargoManager.get_embargo(name)
    if 'kill' == command:
        signal = request.args.get('signal', 'SIGKILL')
        getattr(b, command)(container_names, signal=signal)
    else:
        getattr(b, command)(container_names)

    return '', 204


@app.route("/embargo/<name>/partitions", methods=['POST'])
def partitions(name):
    if not request.headers['Content-Type'] == 'application/json':
        abort(415)

    if not EmbargoManager.embargo_exists(name):
        abort(404)

    b = EmbargoManager.get_embargo(name)

    if request.args.get('random', False):
        b.random_partition()
        return '', 204

    data = request.get_json()
    partitions = data.get('partitions')
    if partitions is None:
        return "'partitions' not found in body", 400
    for partition in partitions:
        if not isinstance(partition, list):
            return "'partitions' must be a list of lists", 400
    b.partition(partitions)

    return '', 204


@app.route("/embargo/<name>/partitions", methods=['DELETE'])
def delete_partitions(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404)

    b = EmbargoManager.get_embargo(name)
    b.join()
    return '', 204


@app.route("/embargo/<name>/network_state", methods=['POST'])
def network_state(name):
    if not request.headers['Content-Type'] == 'application/json':
        abort(415)

    if not EmbargoManager.embargo_exists(name):
        abort(404)

    network_states = ['flaky', 'slow', 'fast', 'duplicate']
    data = request.get_json()
    network_state = data.get('network_state')
    container_names = data.get('container_names')
    if network_state is None:
        return "'network_state' not found in body", 400
    if network_state not in network_states:
        error_str = "'%s' is not a valid network state" % network_state
        return error_str, 400
    if container_names is None:
        return "'container_names' not found in body", 400

    b = EmbargoManager.get_embargo(name)
    getattr(b, network_state)(container_names)

    return '', 204


@app.route("/embargo/<name>")
def status(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404, "The embargo %s does not exist" % name)

    containers = {}
    b = EmbargoManager.get_embargo(name)
    for container in b.status():
        containers[container.name] = container.to_dict()

    return jsonify(containers=containers)


@app.route("/embargo/<name>/events")
def get_events(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404, "The embargo %s does not exist" % name)

    b = EmbargoManager.get_embargo(name)

    def generate():
        yield '{"events": ['
        for a in b.get_audit().read_logs(as_json=False):
            yield a
        yield ']}'

    return Response(generate(), mimetype='application/json')


@app.route("/embargo/<name>", methods=['DELETE'])
def destroy(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404)

    if _chaos.exists(name):
        try:
            _chaos.delete(name)
        except errors.EmbargoUsageError as bue:
            app.logger.error(bue)

    b = EmbargoManager.get_embargo(name)
    b.destroy()
    b.get_audit().clean()
    EmbargoManager.delete_config(name)

    return '', 204


_chaos = chaos.Chaos()


def _validate_chaos_input(option):
    valid_inputs = [
        "min_start_delay", "max_start_delay",
        "min_run_time", "max_run_time",
        "min_containers_at_once", "max_containers_at_once",
        "event_set"
    ]
    for o in option:
        if o not in valid_inputs:
            raise errors.EmbargoHttpError(400, "%s is not a valid input")


@app.route("/embargo/<name>/chaos", methods=['POST'])
def chaos_new(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404, "The embargo %s does not exist" % name)
    if not request.headers['Content-Type'] == 'application/json':
        abort(415, "The body is not in JSON format")
    options = request.get_json()
    _validate_chaos_input(options)
    try:
        _chaos.new_chaos(EmbargoManager.get_embargo(name), name, **options)
        return "Successfully started chaos on %s" % name, 201
    except errors.EmbargoUsageError as bue:
        app.logger.error(str(bue))
        return bue.http_msg, bue.http_code


@app.route("/embargo/<name>/chaos", methods=['PUT'])
def chaos_update(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404, "The embargo %s does not exist" % name)
    options = request.get_json()
    _validate_chaos_input(options)
    try:
        _chaos.update_options(name, **options)
        return "Updated chaos on %s" % name, 200
    except errors.EmbargoUsageError as bue:
        app.logger.error(str(bue))
        return bue.http_msg, bue.http_code


@app.route("/embargo/<name>/chaos", methods=['DELETE'])
def chaos_destroy(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404, "The embargo %s does not exist" % name)
    try:
        _chaos.stop(name)
        _chaos.delete(name)
        return "Deleted chaos on %s" % name, 200
    except errors.EmbargoUsageError as bue:
        app.logger.error(str(bue))
        return str(bue), 500


@app.route("/embargo/<name>/chaos", methods=['GET'])
def chaos_status(name):
    if not EmbargoManager.embargo_exists(name):
        abort(404, "The embargo %s does not exist" % name)
    try:
        status = _chaos.status(name)
        return jsonify(status=status)
    except errors.EmbargoUsageError as bue:
        app.logger.error(str(bue))
        return str(bue), 500
