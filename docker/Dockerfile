ARG tag_ref_name=6.73.506

FROM supervisely/base-py-sdk-light:${tag_ref_name}

RUN apt-get update && apt-get install -y curl bzip2 build-essential gcc g++

RUN curl -LO "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh" \
    && bash Miniforge3-Linux-x86_64.sh -b -p /opt/miniforge \
    && rm Miniforge3-Linux-x86_64.sh \
    && /opt/miniforge/bin/mamba install -c conda-forge python-pdal -y \
    && /opt/miniforge/bin/mamba clean --all -y

ENV PROJ_LIB=/opt/miniforge/share/proj
ENV PATH="/opt/miniforge/bin:$PATH"

RUN pip install supervisely[agent]