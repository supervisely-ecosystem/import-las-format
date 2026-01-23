
FROM supervisely/base-py-sdk-light:6.73.506

ARG tag_ref_name

RUN pip install --upgrade supervisely[agent]==$tag_ref_name
RUN pip install laspy[laszip]==2.7.0
RUN pip install pcd-py==0.2.0
