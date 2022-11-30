import os
import supervisely_lib as sly
from dotenv import load_dotenv

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

my_app = sly.AppService()
api: sly.Api = my_app.public_api

TASK_ID = my_app.task_id
TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
INPUT_DIR = sly.env.folder()
IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
PROJECT_NAME = os.environ.get("modal.state.projectName")
