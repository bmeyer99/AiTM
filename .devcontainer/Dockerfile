FROM mcr.microsoft.com/devcontainers/javascript-node:1-20-bullseye

WORKDIR /workspace

# Update system packages, install Python3, pip3, and clean up
RUN . /etc/os-release \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install python3-pip -y

RUN . /etc/os-release \
    && pip install flask python-jose[cryptography] pymongo[srv] requests jwcrypto python-dotenv PyJWT
    
RUN . /etc/os-release \
    && npm cache clean --force \
    && npm install global react react-devtools react-scripts axios \
    && npm install global styled-components @hello-pangea/dnd \
    && npm install global aws-amplify @aws-amplify/ui-react @aws-amplify/cli