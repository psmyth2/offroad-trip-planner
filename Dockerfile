# Use the official Mamba image
FROM mambaorg/micromamba:1.4.2

# Set working directory
WORKDIR /app

# Switch to root to manage permissions
USER root

# Copy environment file
COPY environment.yml /tmp/environment.yml

# Create Conda environment
RUN micromamba create -y -n offroad-trip -f /tmp/environment.yml && \
    micromamba clean --all --yes

# ✅ Fix permissions: Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/static/cesium && \
    chown -R mambauser:mambauser /app && \
    chmod -R 775 /app/logs /app/uploads

# Switch back to the default user (mambauser)
USER mambauser

# Ensure the environment is activated
SHELL ["micromamba", "run", "-n", "offroad-trip", "/bin/bash", "-c"]

# Copy the rest of the app files
COPY . .

# Expose Flask and Jupyter ports
EXPOSE 5001 8888

# Set Flask environment variables
ENV FLASK_APP=app/main.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# Run Jupyter in background & Flask in foreground
ENTRYPOINT ["micromamba", "run", "-n", "offroad-trip"]
CMD ["bash", "-c", "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root & flask run --host=0.0.0.0 --port=5001 --debug --reload"]

