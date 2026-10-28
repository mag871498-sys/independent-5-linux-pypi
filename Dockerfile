FROM debian:bookworm-slim

ENV container=docker LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       systemd systemd-sysv dbus openssh-server sysstat util-linux fdisk parted \
       python3 python3-venv python3-pip git curl ca-certificates procps iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/lab-venv \
    && mkdir -p /opt/mytest /var/log/journal \
    && truncate -s 0 /etc/machine-id
COPY linux/heartbeat.sh /opt/mytest/heartbeat.sh
COPY linux/mytest.service /etc/systemd/system/mytest.service
COPY linux/container-init.sh /usr/local/sbin/container-init
RUN chmod +x /opt/mytest/heartbeat.sh /usr/local/sbin/container-init \
    && systemctl enable mytest.service ssh.service \
    && systemctl mask systemd-remount-fs.service getty@.service console-getty.service
WORKDIR /work
STOPSIGNAL SIGRTMIN+3
ENTRYPOINT ["/usr/local/sbin/container-init"]
