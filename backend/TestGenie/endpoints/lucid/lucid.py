import logging
import os
from flask import Blueprint
from flask import jsonify, Response
from exceptions.commands import CommandValidation, NotSupportedCommand, CommandUidWrong
import provider.lucid.lucid as lucid
from be_utils.flask.api_args import from_body, from_query, abort
from be_utils.utils import stream_data
from webargs import fields

lucid_bp = Blueprint("lucid", __name__)


@lucid_bp.route("/", methods=["GET"])
def sanity_check():
    return 'there is access to api lucid'


@lucid_bp.route('/netTopology', methods=["GET"])
@from_query({
    "node_id": fields.Str(data_key="nodeId", required=True),
    "instance_id": fields.Str(data_key="instanceId", required=False),
    "view": fields.Str(data_key="view", required=False),
})
def get_network_toplogy(node_id, instance_id="", view='full'):
    return lucid.get_network_topology(node_id, instance_id, view)


@lucid_bp.route('/resources', methods=["GET"])
def get_resources():
    return jsonify(lucid.get_resources())


@lucid_bp.route('/networkFunctionsResources', methods=["GET"])
def get_network_functions_resources():
    return jsonify(lucid.get_network_functions_resources())


@lucid_bp.route('/fetchResources', methods=["GET"])
@from_query({
    "background": fields.Bool(data_key="background", required=False),
})
def fetch_resources(background=False):
    return jsonify(lucid.fetch_resources(background))


@lucid_bp.route('/fetchResourcesStatus', methods=["GET"])
@from_query({
    "fetch_id": fields.Str(data_key="fetchId", required=True),
})
def fetch_resources_status(fetch_id):
    return jsonify(lucid.fetch_resources_status(fetch_id))


@lucid_bp.route('/metaData', methods=["GET"])
def get_app_meta_data():
    return lucid.metadata()


# TODO CHANGE vr1 and vr2 names to something more generic, do array of vrs
@lucid_bp.route('/sharedNetworks', methods=["GET"])
@from_query({
    "vr1": fields.Str(data_key="vr1", required=True),
    "vr2": fields.Str(data_key="vr2", required=True),
})
def shared_networks(vr1, vr2):
    return jsonify(lucid.shared_networks(vr1, vr2))


@lucid_bp.route('/networkPingConnectivityCheck', methods=["POST"])
@from_body({
    "first_vr_uid": fields.Str(data_key="firstVrUid", required=True),
    "second_vr_uid": fields.Str(data_key="secondVrUid", required=True),
    "networks": fields.List(fields.Dict(), data_key="networks", required=True)
})
def network_ping_connectivity_check(first_vr_uid, second_vr_uid, networks):
    logging.info(networks)
    return jsonify(lucid.network_ping_connectivity_check(first_vr_uid, second_vr_uid, networks))


@lucid_bp.route('/vlanTest', methods=["POST"])
@from_body({
    "servers": fields.List(fields.Dict(), data_key="servers", required=True),
    "mtu": fields.Int(data_key="mtu", required=True),
})
def network_interfaces_vlan_check(servers, mtu):
    return jsonify(lucid.network_interfaces_vlan_check(servers=servers,
                                                       mtu=mtu))


@lucid_bp.route('/getVlanTestTotalTime', methods=["GET"])
def get_vlan_test_total_time():
    return jsonify(lucid.get_vlan_test_total_time())


@lucid_bp.route('/getConfiguredVlans', methods=["GET"])
def get_configured_vlans():
    return jsonify(lucid.get_configured_vlans())


@lucid_bp.route('/fetchInterfacesPerGroup', methods=["GET"])
def fetch_interfaces_per_group():
    return jsonify(lucid.fetch_interfaces_per_group())


@lucid_bp.route('/fetchInterfaces', methods=["GET"])
def fetch_interfaces():
    return jsonify(lucid.fetch_interfaces())


@lucid_bp.route('/audit', methods=["GET"])
def audit():
    return jsonify(lucid.audit())


@lucid_bp.route('/downloadFile', methods=["GET"])
@from_query({
    "file_path": fields.Str(data_key="filePath", required=True),
    "dest_host": fields.Str(data_key="destHost", required=True)
})
def download_file(file_path, dest_host):
    try:
        file_chunks_queue = lucid.download_file(file_path, dest_host)
    except Exception as e:
        raise e

    return Response(stream_data(file_chunks_queue),
                    content_type='application/octet-stream',
                    headers={'Content-Disposition': f'attachment; filename={os.path.basename(file_path)}'})


@lucid_bp.route('/logsConfig', methods=["GET"])
def log_config():
    return jsonify(lucid.logs_config())


@lucid_bp.route('/commandsConfig', methods=["GET"])
def commands_config():
    return jsonify(lucid.commands_config())


@lucid_bp.route('/listDir', methods=["GET"])
@from_query({
    "path": fields.Str(data_key="path", required=True),
    "host": fields.Str(data_key="host", required=True),
})
def list_dir(path, host):
    return jsonify(lucid.list_dir(path, host))


@lucid_bp.route('/runCommand', methods=["POST"])
@from_body({
    "command": fields.Str(data_key="command", required=True),
    "command_id": fields.Str(data_key="commandId", required=True),
    "host": fields.Str(data_key="host", required=True),
    "output_as_file": fields.Bool(data_key="outputAsFile", default=False, required=False),
    "is_stream": fields.Bool(data_key="IsStream", default=False, required=False),
    "timeout": fields.Integer(data_key="timeout", required=False),
    "output_as_bytes": fields.Bool(data_key="outputAsBytes", default=False, required=False),
})
def run_command(command, host, command_id, timeout=None, output_as_file=False, is_stream=False, output_as_bytes=False):
    try:
        res = lucid.run_command(command=command,
                                dest_host=host,
                                command_id=command_id,
                                is_stream=is_stream,
                                output_as_file=output_as_file,
                                timeout=timeout,
                                output_as_bytes=output_as_bytes)
        if is_stream:
            content_type = 'application/octet-stream' if output_as_bytes else 'text/plain'
            response = Response(stream_data(res[0], initiator=b' '), content_type=content_type)
            response.headers['CommandUUID'] = res[1]
            return response
        else:
            return jsonify(res)
    except (CommandValidation, NotSupportedCommand, CommandUidWrong) as e:
        logging.error(e)
        return abort(403)


# TODO what about return code in streaming

@lucid_bp.route('/stopCommand', methods=["POST"])
@from_query({
    "command_uuid": fields.Str(data_key="commandUuid", required=True),
})
def stop_command(command_uuid):
    return jsonify(lucid.stop_command(command_uuid))


@lucid_bp.route('/duplicateIps', methods=["GET"])
def duplicate_ips():
    return jsonify(lucid.duplicate_ips())
