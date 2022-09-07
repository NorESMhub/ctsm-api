FROM python:3.10-bullseye

RUN apt update && apt upgrade -y
RUN apt install -y \
    sudo \
    build-essential \
    python3-dev \
    cmake \
    gfortran-9 \
    zlib1g-dev \
    byacc \
    libblas-dev \
    liblapack-dev \
    libxml2-utils \
    libxml-libxml-perl \
    libgdal-dev \
    xmlstarlet \
    csh \
    diffutils \
    rsync

RUN update-alternatives --install /usr/bin/gfortran gfortran /usr/bin/gfortran-9 100

RUN echo '/usr/local/lib' > /etc/ld.so.conf.d/local.conf && ldconfig

RUN mkdir /tmp/sources

WORKDIR /tmp/sources

RUN wget -q http://www.mpich.org/static/downloads/3.3.2/mpich-3.3.2.tar.gz && \
    tar zxf mpich-3.3.2.tar.gz && \
    cd mpich-3.3.2 && \
    ./configure --prefix=/usr/local && \
    make -j 2 install

RUN  wget -q https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-1.12.0/src/hdf5-1.12.0.tar.gz && \
     tar zxf hdf5-1.12.0.tar.gz && \
     cd hdf5-1.12.0 && \
     ./configure --prefix=/usr/local && \
     make -j 2 install

RUN  wget -q ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-c-4.7.4.tar.gz  && \
     tar zxf netcdf-c-4.7.4.tar.gz && \
     cd netcdf-c-4.7.4 && \
     ./configure --prefix=/usr/local && \
     make -j 2 install && \
     ldconfig

RUN  wget -q ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-fortran-4.5.3.tar.gz && \
     tar zxf netcdf-fortran-4.5.3.tar.gz && \
     cd netcdf-fortran-4.5.3 && \
     ./configure --prefix=/usr/local && \
     make -j 2 install && \
     ldconfig

RUN  wget -q https://parallel-netcdf.github.io/Release/pnetcdf-1.12.1.tar.gz && \
     tar zxf pnetcdf-1.12.1.tar.gz && \
     cd pnetcdf-1.12.1 && \
     ./configure MPIF77=/usr/local/bin/mpif77 MPIF90=/usr/local/bin/mpif90 MPICXX=/usr/local/bin/mpicxx MPICC=/usr/local/bin/mpicc && \
     make -j 2 install && \
     ldconfig

RUN wget -q https://github.com/esmf-org/esmf/archive/refs/tags/ESMF_8_2_0.tar.gz && \
    tar zxf ESMF_8_2_0.tar.gz && \
    cd esmf-ESMF_8_2_0 && \
    export ESMF_DIR='/tmp/sources/esmf-ESMF_8_2_0' && \
    export ESMF_INSTALL_PREFIX='/usr/local' && \
    export ESMF_LAPACK="netlib" && \
    export ESMF_LAPACK_LIBS="-llapack -lblas" && \
    export ESMF_LAPACK_LIBPATH="/usr/lib" && \
    export ESMF_NETCDF="nc-config" && \
    gmake && \
    gmake install && \
    ldconfig

RUN rm -rf /tmp/sources

RUN pip install --upgrade pip setuptools

WORKDIR /ctsm-api

COPY alembic /ctsm-api/alembic
COPY app /ctsm-api/app
COPY docker/entrypoint* /ctsm-api/docker/
COPY scripts /ctsm-api/scripts
COPY alembic.ini mypy.ini requirements.txt /ctsm-api/

RUN chmod +x /ctsm-api/docker/entrypoint*

RUN pip install -r requirements.txt

EXPOSE 8000
