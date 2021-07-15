import os
import supervisely_lib as sly

my_app = sly.AppService()
api: sly.Api = my_app.public_api

task_id = my_app.task_id
team_id = int(os.environ['context.teamId'])
workspace_id = int(os.environ['context.workspaceId'])
input_dir = os.environ.get("modal.state.slyFolder")
input_file = os.environ.get("modal.state.slyFile")
project_name = os.environ.get("modal.state.projectName")
