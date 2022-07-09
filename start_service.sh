nginx
python3 src/main.py &
aria2c --conf-path=conf/aria.conf --enable-rpc --rpc-listen-all --rpc-allow-origin-all &
/entrypoint.sh mysqld # for docker
