<div align="center" markdown>
<img src="https://i.imgur.com/T8nscu4.png"/>



# Import LAS format

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

  
[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/import-las-format)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/import-las-format)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/import-las-format.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/import-las-format.png)](https://supervise.ly)

</div>

## Overview

[LAS](https://www.asprs.org/divisions-committees/lidar-division/laser-las-file-format-exchange-activities) (and its compressed counterpart LAZ), is a popular format for lidar point cloud and full waveform.

File format designed for the interchange and archiving of lidar point cloud data. It is an open, binary format specified by the American Society for Photogrammetry and Remote Sensing (ASPRS). The format is widely used and regarded as an industry standard for lidar data.

#### Structure of directory have to be the following:   
```
.
├── directory_with_las_files
    ├── file_0000001.las  # 
    ├── file_0000002.las  # Will be placed to the 1st dataset automatically
    ├── file_0000003.las  # 
    ├── las_dataset_1
    |	├── file_0000001.las
    |	├── file_0000002.las
    |	├── ...
    ├── las_dataset_2
    |	├── file_0000001.laz
    |	├── file_0000002.las
    |	├── ...
    └── ...
```
**Note:** if there are no dataset folder in the main directory, all `.las/.laz` files inside main directory will be placed into created dataset.

## How To Run 
**Step 1**: Add app to your team from [Ecosystem](https://ecosystem.supervise.ly/apps/import-las-format) if it is not there.

**Step 2**:  Go to Current Team -> `Files` page, right-click on the directory with `.las/.laz` files and choose Run App -> `Import LAS format`.

<img src="https://i.imgur.com/V63kbCP.png"/>

**Step 3**: Type name of the resulting project into text input and press `Run` button.

<img src="https://i.imgur.com/BgLvRct.png" width="600px"/>

**Note:** Your project will be placed to the current workspace with selected name.

<img src="https://i.imgur.com/UF2VPis.png"/>

###### Image credit: https://library.carleton.ca/guides/help/lidar-formats
