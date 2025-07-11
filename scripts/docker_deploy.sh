#!/bin/bash
# Altium to KiCAD Database Migration Tool - Docker Deployment Script
# This script builds and deploys the tool as a Docker container

set -e  # Exit on error

# Print with colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Altium to KiCAD Database Migration Tool - Docker Deployment${NC}"
echo "This script will build and deploy the tool as a Docker container."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker before continuing."
    exit 1
fi

echo -e "${GREEN}Docker detected.${NC}"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: docker-compose is not installed.${NC}"
    echo "It is recommended to install docker-compose for easier management."
    use_compose=false
else
    echo -e "${GREEN}docker-compose detected.${NC}"
    use_compose=true
fi

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found.${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ] && [ "$use_compose" = true ]; then
    echo -e "${RED}Error: docker-compose.yml not found.${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Ask for deployment mode
echo "Select deployment mode:"
echo "1. API server only"
echo "2. API server with web interface"
echo "3. Full deployment (API, web interface, and CLI tools)"
read -p "Enter your choice (1-3): " deploy_mode

# Set deployment options based on mode
case $deploy_mode in
    1)
        echo -e "${YELLOW}Deploying API server only...${NC}"
        export DEPLOY_MODE="api"
        ;;
    2)
        echo -e "${YELLOW}Deploying API server with web interface...${NC}"
        export DEPLOY_MODE="web"
        ;;
    3)
        echo -e "${YELLOW}Deploying full stack...${NC}"
        export DEPLOY_MODE="full"
        ;;
    *)
        echo -e "${RED}Invalid choice. Defaulting to API server only.${NC}"
        export DEPLOY_MODE="api"
        ;;
esac

# Ask for port configuration
read -p "Enter port for API server (default: 8000): " api_port
api_port=${api_port:-8000}
export API_PORT=$api_port

if [ "$deploy_mode" = "2" ] || [ "$deploy_mode" = "3" ]; then
    read -p "Enter port for web interface (default: 8080): " web_port
    web_port=${web_port:-8080}
    export WEB_PORT=$web_port
fi

# Ask for volume configuration
read -p "Do you want to persist data in a Docker volume? (y/n) [default: y]: " use_volume
use_volume=${use_volume:-y}

if [[ $use_volume == "y" || $use_volume == "Y" ]]; then
    read -p "Enter volume name (default: altium2kicad_data): " volume_name
    volume_name=${volume_name:-altium2kicad_data}
    export VOLUME_NAME=$volume_name
    
    # Create volume if it doesn't exist
    if ! docker volume inspect $volume_name &> /dev/null; then
        echo -e "${YELLOW}Creating Docker volume $volume_name...${NC}"
        docker volume create $volume_name
    fi
fi

# Build and deploy
if [ "$use_compose" = true ]; then
    echo -e "${YELLOW}Building and deploying with docker-compose...${NC}"
    docker-compose up -d
else
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t altium2kicad:latest .
    
    echo -e "${YELLOW}Deploying Docker container...${NC}"
    
    # Set up Docker run command based on deployment mode
    docker_cmd="docker run -d --name altium2kicad"
    
    # Add port mappings
    docker_cmd="$docker_cmd -p $api_port:8000"
    if [ "$deploy_mode" = "2" ] || [ "$deploy_mode" = "3" ]; then
        docker_cmd="$docker_cmd -p $web_port:8080"
    fi
    
    # Add volume if requested
    if [[ $use_volume == "y" || $use_volume == "Y" ]]; then
        docker_cmd="$docker_cmd -v $volume_name:/app/data"
    fi
    
    # Add environment variables
    docker_cmd="$docker_cmd -e DEPLOY_MODE=$DEPLOY_MODE"
    
    # Add image name
    docker_cmd="$docker_cmd altium2kicad:latest"
    
    # Execute the command
    eval $docker_cmd
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""

# Display access information
echo "Access Information:"
echo "API Server: http://localhost:$api_port/api/v1"
echo "API Documentation: http://localhost:$api_port/docs"

if [ "$deploy_mode" = "2" ] || [ "$deploy_mode" = "3" ]; then
    echo "Web Interface: http://localhost:$web_port"
fi

echo ""
echo "To view logs:"
if [ "$use_compose" = true ]; then
    echo "  docker-compose logs -f"
else
    echo "  docker logs -f altium2kicad"
fi

echo ""
echo "To stop the container:"
if [ "$use_compose" = true ]; then
    echo "  docker-compose down"
else
    echo "  docker stop altium2kicad"
    echo "  docker rm altium2kicad"
fi