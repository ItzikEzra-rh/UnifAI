import asyncio
import time
from pymongo import MongoClient
from be_utils.dpr import DPR, DPRCommands
from be_utils.utils import json_to_yaml, helm_response
import uuid
from be_utils.db.db import mongo, Collections
import json
from bson import ObjectId
import requests 
from config.configParams import config

@mongo
def helm_install(user_data):
    file_path , yaml_data  = json_to_yaml(user_data)
    deployment_name = yaml_data["global"]["deployment_name"]
    hf_token = yaml_data["global"]["hf_token"]
    api_url = yaml_data["global"]["api_url"]
    namespace = yaml_data["global"]["namespace"]

    helm = DPR(hf_token,api_url, namespace)
    helm_install = helm.run_dpr_command(DPRCommands.INSTALL, deployment_name=deployment_name,values=file_path)

    if helm_install["status"] == "success":
        data = json.loads(helm_install["data"])
        data["is_deleted"] = False
        data.pop("manifest", None)
        data.pop("chart", None)

        result = Collections.by_name('dpr').insert_one(data)

        helm_install.pop("data",None)
        helm_install["_id"] = str(result.inserted_id)

    return helm_install

@mongo
def helm_upgrade(user_data):

    id = user_data["_id"]
    helm_set_params = []

    for key, value in user_data["global"].items():
        helm_set_params.append(f"--set global.{key}={value}")

    helm_set_params_str = " ".join(helm_set_params)

    creds = get_config_creds(id)
    if creds:
        helm = DPR(api_url=creds["api_url"], token=creds["hf_token"], namespace=creds["namespace"])
        helm_upgrade = helm.run_dpr_command(DPRCommands.UPGRADE, deployment_name=creds["deployment_name"],helm_set_params=helm_set_params_str)

        if helm_upgrade["status"] == "success":
            result = Collections.by_name('dpr').update_one(
                {"_id": ObjectId(id)},   
                {"$set": {f"config.global.{key}": value for key, value in user_data["global"].items()}}
            )
            if result.matched_count > 0:
                helm_upgrade["data"] = "upgrade dpr process completed"

        return helm_upgrade

@mongo
def helm_uninstall(id, status):
    creds = get_config_creds(id)
    if creds:
        helm = DPR(api_url=creds["api_url"], token=creds["hf_token"], namespace=creds["namespace"])
        helm_uninstall = helm.run_dpr_command(DPRCommands.UNINSTALL, deployment_name=creds["deployment_name"])
        Collections.by_name('dpr').update_one({"_id": ObjectId(id)}, {"$set": {"status": status}, "$currentDate": {"finished_running": True}})
        return helm_uninstall


@mongo
def helm_status(id):
    creds = get_config_creds(id)
    if creds:
        helm = DPR(api_url=creds["api_url"], token=creds["hf_token"], namespace=creds["namespace"])
        status = helm.run_dpr_command(DPRCommands.STATUS, deployment_name=creds["deployment_name"])
        return status


@mongo
def helm_metrics(id, name):
    def fetch_rabbitmq_stats(route):
        try:
            response = requests.get(f"http://{name}-rabbitmq-svc:15672/api/queues", 
            # response = requests.get(f"http://{route}:15672/api/queues", 
                                    auth=(config.get("dpr", "rmq_username"), config.get("dpr", "rmq_password")), 
                                    timeout=5)
            if response.status_code != 200:
                return helm_response(False, f"Failed to fetch metrics from {route}")

            queues = ["prompts_process_queue", "reviewed_queue", "reviewer_queue"]
            return {item["name"]: item for item in response.json() if item["name"] in queues}
        except requests.exceptions.RequestException:
            return {}

    def fetch_mongodb_stats(route):
        try: 
            client = MongoClient(f'mongodb://{name}-mongodb-svc')  
            # client = MongoClient(f'mongodb://{route}')  
            db = client['promptLab']  
            return list(db['statistics'].find())
        except:
            return {}

    creds = get_config_creds(id)
    rabbitmq_route, db_route = creds.get("release_rmq_route"), creds.get("release_db_route")
    if not rabbitmq_route or not db_route:
        helm_route(id)

    rabbitmq_stats = fetch_rabbitmq_stats(rabbitmq_route) if rabbitmq_route else None
    mongodb_stats = fetch_mongodb_stats(db_route) if db_route else None

    errors = [msg for msg, cond in zip(["Missing RabbitMQ route.", "Missing MongoDB route."], [not rabbitmq_route, not db_route]) if cond]

    update_data = {"rabbitmq": rabbitmq_stats, "mongodb": mongodb_stats}
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if update_data:
        result = Collections.by_name('dpr').update_one({"_id": ObjectId(id)}, {"$set": {"metrics": update_data}})
        if result.matched_count == 0:
            errors.append("Failed to update database.")

    if errors:
        return helm_response(False, ", ".join(errors))
    
    # Check if the deployment should be uninstalled
    progress_data = next((item for item in mongodb_stats if item.get('_id') == "progress_data"), None)
    if progress_data:
        no_remaining_prompts = progress_data['prompts_failed'] + progress_data['prompts_pass'] == progress_data['number_of_prompts']
        if no_remaining_prompts and progress_data.get('exported', False):
            helm_uninstall(id, "DONE")

    return helm_response(True, update_data)

@mongo
def helm_route(id):
    creds = get_config_creds(id)
    helm = DPR(api_url=creds["api_url"], token=creds["hf_token"], namespace=creds["namespace"])
    
    routes = {
        "release_rmq_route": DPRCommands.RMQROUTE,
        "release_db_route": DPRCommands.DBROUTE,
    }

    updated_routes = {}
    for route_key, command in routes.items():
        if not creds[route_key]:
            # route_result = helm.run_dpr_command(command, deployment_name=creds["deployment_name"], spec="{.metadata.name}")
            route_result = helm.run_dpr_command(command, deployment_name=creds["deployment_name"], spec="{.status.loadBalancer.ingress[0].hostname}")

            if route_result["data"]:
                update_result = Collections.by_name("dpr").update_one(
                    {"_id": ObjectId(id)},
                    {"$set": {f"config.global.{route_key}": route_result["data"]}}
                )
                if update_result.matched_count <= 0:
                    return helm_response(False, f"Failed to update {route_key} in DB for id {id}")

                updated_routes[route_key] = route_result["data"]

    return helm_response(True, updated_routes)

@mongo
def delete_deployment(id):
    """
    :return: list of deployments that are currently running (haven't been deleted from the db)
    """

    result = Collections.by_name('dpr').update_one({"_id": ObjectId(id)}, {"$set": {"is_deleted": True}})
    return result.modified_count

def get_config_creds(id):
    config_data = Collections.by_name('dpr').find_one({'_id': ObjectId(id)})
    if config_data:
        config = config_data.get("config", {}).get("global", {})
        return {
            "hf_token": config.get("hf_token"),
            "namespace": config.get("namespace"),
            "api_url": config.get("api_url"),
            "deployment_name": config_data.get("name"),
            "release_rmq_route": config.get("release_rmq_route", ""),
            "release_db_route": config.get("release_db_route", ""),
        }
    return {}

def create_json_format(user_data):
    def extract_config(data, exclude_keys=None):
        exclude_keys = exclude_keys or []
        return {k: data.get(k, "") for k in data if k not in exclude_keys}

    global_config = extract_config(user_data["global"])
    promptlab_env = extract_config(user_data["promptLab"], exclude_keys=["vllm_orbiter_args"])
    reviewer_env = extract_config(user_data["reviewer"]) if global_config.get("enable_reviewer") else {}

    json_output = {
        "global": {
            **global_config,
            "orbiter_model_hf_id": user_data["promptLab"].get("PROMPT_LAB_MODEL_HF_ID", ""),
            "promptlab_env": {**promptlab_env, **user_data["file"]},
        }
    }
    
    if global_config.get("enable_reviewer", True):
        json_output["global"].update({
            "reviewer_model_hf_id": reviewer_env.get("REVIEWER_MODEL_HF_ID", ""),
            "reviewer_env": reviewer_env,
        })
    
    return json_output

@mongo
def get_actively_running():
    """
    :return: list of deployments that are currently running (haven't been uninstalled)
    """
    result = Collections.by_name('dpr').find({"status": {"$nin": ["DONE", "UNINSTALLED"]}}, {"_id": 1})

    return [{"_id": str(doc["_id"])} for doc in result]

@mongo
def get_not_deleted_deployments():
    """
    :return: list of deployments that are currently running (haven't been deleted from the db)
    """
    result = Collections.by_name('dpr').find(
        {"is_deleted": False},
        {"_id": 1, "name": 1, "info.first_deployed": 1, "finished_running": 1, "metrics": 1, "status": 1}
    )

    return [{"_id": str(doc["_id"]), 
             "name": doc.get("name"), 
             "first_deployed": doc.get("info", {}).get("first_deployed", "N/A"), 
             "finished_running": doc.get("finished_running", ""), 
             "metrics": doc.get("metrics", {}),
             "status": doc.get("status", "N/A")}
            for doc in result]

@mongo
def get_json_file_config(id):
    """
    :return: list of statistics, both from the rabbitmq and the mongodb
    """
    result = list(Collections.by_name('dpr').find({'_id': ObjectId(id)}, {'config': 1}))
    return result[0]['config'] if result else []

async def celery_fetch_dpr():
    """
    Fetches Helm metrics for all currently running deployments.
    """
    print("Starting fetch metrics for dpr")
    running_deployments = get_actively_running()

    metrics_data = {}
    for deployment in running_deployments:
        deployment_id = deployment["_id"]
        deployment_name = deployment["deployment_name"]
        metrics = helm_metrics(deployment_id, deployment_name)
        if metrics:
            metrics_data[deployment_id] = metrics

    return metrics_data