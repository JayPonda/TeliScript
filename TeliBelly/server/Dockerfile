# Use a Conda-based image
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /app

# Copy the environment file and create the Conda environment
COPY environment.yml .
RUN conda env create -f environment.yml

# Activate the conda environment
RUN echo "conda activate tenv" >> ~/.bashrc

# Copy the rest of the application files
COPY . .

# Expose the port
EXPOSE 8000

# Set the command to run the application
CMD ["conda", "run", "--no-capture-output", "-n", "tenv", "python", "api_server_fastapi.py"]