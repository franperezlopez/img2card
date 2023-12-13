FROM python:3.10

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

# Set conda path
ENV PATH="/opt/conda/bin:${PATH}"

ARG TELEGRAM_TOKEN
ENV TELEGRAM_TOKEN=$TELEGRAM_TOKEN
ARG AZURE_OPENAI_API_KEY
ENV AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
ARG AZURE_OPENAI_API_BASE
ENV AZURE_OPENAI_API_BASE=$AZURE_OPENAI_API_BASE
ARG LANGCHAIN_API_KEY
ENV LANGCHAIN_API_KEY=$LANGCHAIN_API_KEY

# Copy environment file
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && \
    conda clean -afy
# RUN conda clean -afy

# Set working directory
WORKDIR /app

# Copy source code
COPY src src
COPY bot.py .

ENV PATH="/opt/conda/envs/img2card/bin:${PATH}"

CMD ["python", "-m", "bot"]
