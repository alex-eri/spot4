FROM node:24-trixie AS node-builder
RUN apt -y update && apt -y install git make debhelper dpkg-dev git-buildpackage build-essential && apt -y clean
WORKDIR /app/build
COPY --parents=true Makefile debian admin uam frontend mikrotik .git ./
RUN dpkg-buildpackage -A --rules-file=debian/spot4-static.rules --no-sign


FROM python:3.13-trixie AS trixie-builder
RUN apt -y update && apt -y install git make debhelper dpkg-dev git-buildpackage build-essential patchelf && apt -y clean
WORKDIR /app/build
COPY  --parents=true requrements.txt ./server/Makefile .
RUN make -C server venv
COPY --parents=true debian server Makefile systemd config .git .
RUN dpkg-buildpackage -B --rules-file=debian/spot4.rules --no-sign

FROM python:3.13-bookworm AS bookworm-builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt -y update && apt -y install git make debhelper dpkg-dev git-buildpackage build-essential patchelf && apt -y clean
WORKDIR /app/build
COPY  --parents=true requrements.txt ./server/Makefile .
RUN make -C server venv
COPY --parents=true debian server Makefile systemd config .git .
RUN dpkg-buildpackage -B --rules-file=debian/spot4.rules --no-sign


# FROM ubuntu:24.04 as noble-builder
# ENV DEBIAN_FRONTEND=noninteractive
# RUN apt -y update && apt -y install git make debhelper dpkg-dev git-buildpackage build-essential python3-dev python3-pip python3-venv && apt -y clean
# WORKDIR /app/build
# COPY . .
# RUN dpkg-buildpackage -B --rules-file=debian/spot4.rules --no-sign


FROM debian:trixie AS trixie-runner
WORKDIR /app/debs
RUN mkdir trixie bookworm noble ../out
COPY --from=trixie-builder /app/spot4_*.deb trixie/
# COPY --from=noble-builder /app/spot4_*.deb noble/
COPY --from=node-builder  /app/spot4-mikrotik-builder_*.deb .
COPY --from=node-builder /app/spot4-static_*.deb .
COPY --from=bookworm-builder /app/spot4_*.deb bookworm/
CMD ["cp","-R","/app/debs/","/app/out/"]