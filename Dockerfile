FROM python:3.10

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

# Set conda path
ENV PATH="/opt/conda/bin:${PATH}"

# Copy environment file
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml

# Set conda environment
ENV CONDA_DEFAULT_ENV=py310

# Set working directory
WORKDIR /app

# Copy source code
COPY src src
COPY bot.py .


