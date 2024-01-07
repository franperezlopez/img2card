FROM python:3.10

ENV CONDA_PATH="/opt/conda"
ENV CONDA_ENV="img2card"

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p "${CONDA_PATH}" && \
    rm Miniconda3-latest-Linux-x86_64.sh

# Set conda path
ENV PATH="${CONDA_PATH}/bin:${PATH}"

ARG TELEGRAM_TOKEN
ENV TELEGRAM_TOKEN=$TELEGRAM_TOKEN
ARG AZURE_OPENAI_API_KEY
ENV AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
ARG AZURE_OPENAI_API_BASE
ENV AZURE_OPENAI_API_BASE=$AZURE_OPENAI_API_BASE
ARG LANGSMITH_API_KEY
ENV LANGSMITH_API_KEY=$LANGSMITH_API_KEY
ARG SERPAPI_API_KEY
ENV SERPAPI_API_KEY=$SERPAPI_API_KEY
ARG GEOAPIFY_API_KEY
ENV GEOAPIFY_API_KEY=$GEOAPIFY_API_KEY

# Copy environment file
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && \
    conda clean -afy && \
    rm environment.yml
ENV PATH="${CONDA_PATH}/envs/${CONDA_ENV}/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy source code
COPY src src

EXPOSE 80

CMD ["python", "-m", "src.bot"]
