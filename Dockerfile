FROM python:3.10-slim

LABEL maintainer="Altium2KiCAD Team"
LABEL description="Altium to KiCAD Database Migration Tool"
LABEL version="0.1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.5.1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use a virtual environment in the container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.py

# Create volume for data persistence
VOLUME /app/data

# Expose port for GUI (if applicable)
EXPOSE 8080

# Set entrypoint to the CLI
ENTRYPOINT ["python", "-m", "migration_tool.cli"]

# Default command (can be overridden)
CMD ["--help"]