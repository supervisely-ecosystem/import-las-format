import os
import supervisely_lib as sly

my_app = sly.AppService()
api: sly.Api = my_app.public_api

TASK_ID = my_app.task_id
TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
INPUT_DIR = os.environ.get("modal.state.slyFolder")
IS_ON_AGENT = api.file.is_on_agent(INPUT_DIR)
PROJECT_NAME = os.environ.get("modal.state.projectName")
