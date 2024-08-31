FROM debian:stable-slim

# Set environment variables
ENV EXTENSION_ID=ilehaonighjijnmpnagapkhpcdbhclfg
ENV EXTENSION_URL='https://app.getgrass.io/'
ENV GIT_USERNAME=warren-bank
ENV GIT_REPO=chrome-extension-downloader

# Install necessary packages then clean up to reduce image size
RUN apt update && \
    apt upgrade -y && \
    apt install -qqy \
    curl \
    wget \
    git \
    chromium \
    chromium-driver \
    python3 \
    python3-pip \
    python3-selenium && \
    apt autoremove --purge -y && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Download crx downloader from git
RUN git clone "https://github.com/${GIT_USERNAME}/${GIT_REPO}.git" && \
    chmod +x ./${GIT_REPO}/bin/*

# Download the extension selected
RUN ./${GIT_REPO}/bin/crxdl $EXTENSION_ID

# Install python requirements
RUN wget https://raw.githubusercontent.com/snowflake1212/get-grass/main/grass_main.py
RUN pip3 install Flask selenium Thread --break-system-packages
ENTRYPOINT [ "python3", "grass_main.py" ]
