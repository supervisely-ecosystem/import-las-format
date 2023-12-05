import os
import shutil

import laspy
import numpy as np
import open3d as o3d
import supervisely as sly
from supervisely.io.fs import get_file_name

import globals as g


def las2pcd(input_path, output_path):
    las = laspy.read(input_path)
    point_cloud = np.vstack((las.X, las.Y, las.Z)).T
    pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(point_cloud))
    o3d.io.write_point_cloud(output_path, pc)


@g.my_app.callback("import_las")
@sly.timeit
def import_las(api: sly.Api, task_id, context, state, app_logger):
    storage_dir = g.my_app.data_dir
    if g.IS_ON_AGENT:
        agent_id, curr_file_path = g.api.file.parse_agent_id_and_path(g.INPUT_DIR)
        local_save_dir = os.path.join(
            storage_dir, os.path.basename(os.path.normpath(curr_file_path))
        )
    else:
        local_save_dir = os.path.join(storage_dir, os.path.basename(os.path.normpath(g.INPUT_DIR)))
    api.file.download_directory(g.TEAM_ID, g.INPUT_DIR, local_save_dir)

    if len(g.PROJECT_NAME) == 0:
        project_name = os.path.basename(os.path.normpath(local_save_dir))
    else:
        project_name = g.PROJECT_NAME

    project = None

    datasets = [d.path for d in os.scandir(local_save_dir) if d.is_dir()]
    files = [
        os.path.join(local_save_dir, file)
        for file in os.listdir(local_save_dir)
        if os.path.isfile(os.path.join(local_save_dir, file))
        and (file.endswith(".las") or file.endswith(".laz"))
    ]
    if len(files) >= 1:
        for file in files:
            if len(datasets) == 0:
                sly.fs.mkdir(os.path.join(local_save_dir, "ds0"))
                shutil.move(file, os.path.join(local_save_dir, "ds0"))
                datasets = [d.path for d in os.scandir(local_save_dir) if d.is_dir()]
            else:
                shutil.move(file, datasets[0])

    uploaded_pcd = 0
    for dataset in datasets:
        dataset_name = os.path.basename(os.path.normpath(dataset))
        created_dataset = None

        ds_file_paths = os.listdir(dataset)
        progress = sly.Progress(
            f"Processing {dataset_name} dataset files:", len(ds_file_paths), sly.logger
        )
        for ds_file_name in ds_file_paths:
            if ds_file_name.endswith(".las") or ds_file_name.endswith(".laz"):
                input_path = os.path.join(dataset, ds_file_name)
                output_path = os.path.join(dataset, f"{get_file_name(ds_file_name)}.pcd")
                las2pcd(input_path, output_path)
                if not sly.fs.file_exists(output_path):
                    sly.logger.warn(
                        f"File {get_file_name(ds_file_name)} could not be converted to .pcd format. Skipping..."
                    )
                    continue
                if project is None:
                    project = g.api.project.create(
                        g.WORKSPACE_ID,
                        project_name,
                        type=sly.ProjectType.POINT_CLOUDS,
                        change_name_if_conflict=True,
                    )
                if created_dataset is None:
                    created_dataset = g.api.dataset.create(
                        project.id, dataset_name, change_name_if_conflict=True
                    )
                    g.my_app.logger.info(f"New dataset has been created: {created_dataset.name}")

                sly.fs.silent_remove(input_path)
                api.pointcloud.upload_path(
                    created_dataset.id, name=f"{get_file_name(ds_file_name)}.pcd", path=output_path
                )
                uploaded_pcd += 1
                g.my_app.logger.info(
                    f"LAS File {get_file_name(ds_file_name)} has been successfully uploaded to dataset: {created_dataset.name}"
                )

                progress.iter_done_report()

    if uploaded_pcd == 0:
        msg = "No LAS files were uploaded to Supervisely."
        description = "Please, check the logs and your input data."
        g.my_app.logger.error(f"{msg} {description}")
        api.task.set_output_error(task_id, msg, description)
    g.my_app.stop()


def main():
    sly.logger.info(
        "Script arguments", extra={"TEAM_ID": g.TEAM_ID, "WORKSPACE_ID": g.WORKSPACE_ID}
    )
    g.my_app.run(initial_events=[{"command": "import_las"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
