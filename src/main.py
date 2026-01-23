import os
import shutil

import laspy
import numpy as np
import pcd_py
import supervisely as sly
from supervisely.io.fs import get_file_ext, get_file_name, get_file_name_with_ext

import globals as g


def las2pcd(input_path: str, output_path: str) -> None:
    """
    Convert a LAS/LAZ point cloud to PCD format.

    The function reads a LAS/LAZ file, applies coordinate scaling and offsets,
    recenters the point cloud to improve numerical stability, and writes
    the result to a PCD file compatible with common point cloud viewers.

    :param input_path: Path to the input LAS/LAZ file.
    :type input_path: str
    :param output_path: Path where the output PCD file will be written.
    :type output_path: str
    :return: None
    """
    input_file_name = get_file_name_with_ext(input_path)
    sly.logger.info(f"Start processing file: {input_file_name}")

    # Read LAS file
    try:
        las = laspy.read(input_path)
    except Exception as e:
        if "buffer size must be a multiple of element size" in str(e):
            sly.logger.warning(
                f"{input_file_name} file read failed due to buffer size mismatch with EXTRA_BYTES. "
                "Retrying with EXTRA_BYTES disabled as a workaround..."
            )
            from laspy.point.record import PackedPointRecord

            @classmethod
            def from_buffer_without_extra_bytes(cls, buffer, point_format, count=-1, offset=0):
                item_size = point_format.size
                count = len(buffer) // item_size
                points_dtype = point_format.dtype()
                data = np.frombuffer(buffer, dtype=points_dtype, offset=offset, count=count)
                return cls(data, point_format)

            PackedPointRecord.from_buffer = from_buffer_without_extra_bytes
            las = laspy.read(input_path)
        else:
            raise

    # Use scaled coordinates (scale and offset applied)
    x = np.asarray(las.x, dtype=np.float64)
    y = np.asarray(las.y, dtype=np.float64)
    z = np.asarray(las.z, dtype=np.float64)

    # Build Nx3 point array
    pts = np.vstack((x, y, z)).T

    # Check for empty point cloud
    if len(pts) == 0:
        sly.logger.warning(f"{input_file_name} file is empty (0 points).")
        return
    
    # Recenter point cloud to reduce floating point precision issues
    shift = pts.mean(axis=0)
    sly.logger.info(
        f"Applied coordinate shift for {input_file_name}: "
        f"X={shift[0]}, Y={shift[1]}, Z={shift[2]}"
    )
    pts -= shift

    # Base PCD fields
    data = {
        "x": pts[:, 0].astype(np.float32),
        "y": pts[:, 1].astype(np.float32),
        "z": pts[:, 2].astype(np.float32),
        "intensity": las.intensity.astype(np.float32),
    }

    # Handle RGB attributes if present
    if hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue"):
        # Convert LAS colors to 8-bit.
        # Some files store 0–255 values in 16-bit fields; detect this and only shift when needed.
        r_raw = np.asarray(las.red)
        g_raw = np.asarray(las.green)
        b_raw = np.asarray(las.blue)

        # Determine if the values are full 16-bit range (0–65535) or already 0–255.
        max_rgb = max(
            r_raw.max(initial=0),
            g_raw.max(initial=0),
            b_raw.max(initial=0),
        )

        if max_rgb > 255:
            # Typical LAS case: 16-bit colors; downscale to 8-bit.
            r = (r_raw >> 8).astype(np.uint32)
            g = (g_raw >> 8).astype(np.uint32)
            b = (b_raw >> 8).astype(np.uint32)
        else:
            # Values are already in 0–255 range; use as-is.
            r = r_raw.astype(np.uint32)
            g = g_raw.astype(np.uint32)
            b = b_raw.astype(np.uint32)

        # Pack RGB into a single float field (PCL-compatible)
        rgb = (r << 16) | (g << 8) | b
        data["rgb"] = rgb.view(np.float32)

    # Write PCD file
    pcd_py.write_pcd(output_path, data, format="binary_compressed")


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
    listdir = os.listdir(local_save_dir)
    if len(listdir) == 0:
        raise FileNotFoundError("Input directory is empty. Please, check your input data.")
    elif len(listdir) == 1 and sly.fs.is_archive(os.path.join(local_save_dir, listdir[0])):
        sly.logger.info("Single archive detected. Unpacking...")
        unpacked_dir = os.path.join(local_save_dir, sly.fs.get_file_name(listdir[0]))
        sly.fs.unpack_archive(os.path.join(local_save_dir, listdir[0]), unpacked_dir)
        sly.fs.silent_remove(os.path.join(local_save_dir, listdir[0]))
        local_save_dir = unpacked_dir

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
                sly.logger.info("No datasets found. Creating a new one...")
                sly.fs.mkdir(os.path.join(local_save_dir, "ds0"))
                shutil.move(file, os.path.join(local_save_dir, "ds0"))
                datasets = [d.path for d in os.scandir(local_save_dir) if d.is_dir()]
            else:
                sly.logger.info(
                    f"Moving files without datasets to the first dataset ({datasets[0]})..."
                )
                shutil.move(file, datasets[0])

    sly.logger.info(
        f"Starting to process {len(datasets)} dataset{'s' if len(datasets) > 1 else ''}: {datasets}"
    )    
    # Warning about coordinate shift
    sly.logger.info(
        "⚠️ IMPORTANT: Coordinate shift will be applied to all LAS/LAZ files during conversion to PCD format. "
        "This is necessary to avoid floating-point precision issues and visual artifacts. "
        "The shift values (X, Y, Z offsets) will be logged for each file. "
        "If you need to convert annotations back to original LAS coordinates or use them with original LAS files, "
        "you MUST add these shift values back to the PCD/annotation coordinates. "
        "Check the logs for 'Applied coordinate shift' messages for each file."
    )
    uploaded_pcd = 0
    for dataset in datasets:
        dataset_name = os.path.basename(os.path.normpath(dataset))
        created_dataset = None

        ds_file_paths = os.listdir(dataset)
        ds_file_paths = sly.fs.list_files_recursively(dataset, [".las", ".laz"])
        progress = sly.Progress(
            f"Processing {dataset_name} dataset files:", len(ds_file_paths), sly.logger
        )
        for input_path in ds_file_paths:
            if input_path.endswith(".las") or input_path.endswith(".laz"):
                # Determine original format
                original_format = "LAZ" if input_path.endswith(".laz") else "LAS"
                output_path = os.path.join(dataset, f"{get_file_name(input_path)}.pcd")
                las2pcd(input_path, output_path)

                if not sly.fs.file_exists(output_path):
                    sly.logger.warning(
                        f"File {get_file_name_with_ext(input_path)} could not be converted to .pcd format. Skipping..."
                    )
                    continue
                if project is None:
                    project = g.api.project.create(
                        g.WORKSPACE_ID,
                        project_name,
                        type=sly.ProjectType.POINT_CLOUDS,
                        change_name_if_conflict=True,
                    )
                    sly.logger.info(
                        f"New project has been created: {project.name} (ID: {project.id})"
                    )
                if created_dataset is None:
                    created_dataset = g.api.dataset.create(
                        project.id, dataset_name, change_name_if_conflict=True
                    )
                    g.my_app.logger.info(
                        f"New dataset has been created: {created_dataset.name} (ID: {created_dataset.id})"
                    )

                sly.logger.info(
                    f"Successfully converted {original_format} → PCD: {get_file_name(input_path)}.pcd"
                )

                sly.fs.silent_remove(input_path)
                api.pointcloud.upload_path(
                    created_dataset.id, name=f"{get_file_name(input_path)}.pcd", path=output_path
                )
                uploaded_pcd += 1
                g.my_app.logger.info(
                    f"Successfully uploaded {original_format} file '{get_file_name(input_path)}' as PCD to dataset '{created_dataset.name}' (ID: {created_dataset.id})"
                )

                progress.iter_done_report()

    if uploaded_pcd == 0:
        msg = "No LAS/LAZ files were uploaded to Supervisely."
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
