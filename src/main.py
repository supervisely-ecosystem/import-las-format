import os
import shutil

import laspy
import numpy as np
import globals as g
import open3d as o3d
import supervisely_lib as sly
from supervisely_lib.io.fs import get_file_name


def las2pcd(input_path, output_path):
    las = laspy.read(input_path)
    point_cloud = np.vstack((las.X, las.Y, las.Z)).T
    pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(point_cloud))
    o3d.io.write_point_cloud(output_path, pc)


@g.my_app.callback("import_las")
@sly.timeit
def import_las(api: sly.Api, task_id, context, state, app_logger):
    storage_dir = g.my_app.data_dir
    local_save_dir = os.path.join(storage_dir, os.path.basename(os.path.normpath(g.input_dir)))
    api.file.download_directory(g.team_id, g.input_dir, local_save_dir)

    if len(g.project_name) == 0:
        project_name = os.path.basename(os.path.normpath(local_save_dir))
    else:
        project_name = g.project_name

    project = g.api.project.create(g.workspace_id,
                                   project_name,
                                   type=sly.ProjectType.POINT_CLOUDS,
                                   change_name_if_conflict=True)

    datasets = [d.path for d in os.scandir(local_save_dir) if d.is_dir()]
    files = [os.path.join(local_save_dir, file) for file in os.listdir(local_save_dir) if
             os.path.isfile(os.path.join(local_save_dir, file)) and file.endswith(".las") or file.endswith(".laz")]
    if len(files) >= 1:
        for file in files:
            if len(datasets) == 0:
                sly.fs.mkdir(os.path.join(local_save_dir, "ds0"))
                shutil.move(file, os.path.join(local_save_dir, "ds0"))
            else:
                shutil.move(file, datasets[0])

    #progress = sly.Progress("Processing {} dataset".format(dataset_name), len(images_list), sly.logger)
    for dataset in datasets:
        created_dataset = g.api.dataset.create(project.id, os.path.basename(os.path.normpath(dataset)), change_name_if_conflict=True)
        g.my_app.logger.info(f"Api create new dataset: {created_dataset.name}")

        pc_names = []
        pc_paths = []
        ds_file_paths = os.listdir(dataset)
        for ds_file_name in ds_file_paths:
            if ds_file_name.endswith(".las") or ds_file_name.endswith(".laz"):
                input_path = os.path.join(dataset, ds_file_name)
                output_path = os.path.join(dataset, get_file_name(ds_file_name) + ".pcd")
                pc_names.append(get_file_name(ds_file_name) + ".pcd")
                pc_paths.append(output_path)
                las2pcd(input_path, output_path)
                sly.fs.silent_remove(input_path)

        upload_info = api.pointcloud.upload_paths(created_dataset.id, names=pc_names, paths=pc_paths)
        g.my_app.logger.info(f'LAS files has been successfully uploaded to dataset: {created_dataset.name}')

    g.my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "TEAM_ID": g.team_id,
        "WORKSPACE_ID": g.workspace_id
    })
    g.my_app.run(initial_events=[{"command": "import_las"}])


if __name__ == '__main__':
    sly.main_wrapper("main", main)
