FROM mysql

RUN apt update
RUN apt install -y nginx python3 python3-pip aria2
RUN pip3 install nyaapy lxml zhconv tormysql tornado bencode.py
ENV MYSQL_ROOT_PASSWORD YOUR_SQL_PASSWORD

COPY src /root/src
COPY conf /root/conf
RUN mv /root/conf/bangumi.conf /etc/nginx/sites-enabled/
COPY Bangumis.sql /docker-entrypoint-initdb.d/
WORKDIR /root/

RUN sed -i "s~YOUR_DIRECTORY~/share~g" /etc/nginx/sites-enabled/bangumi.conf
RUN sed -i 's~covers~/share/covers~g' /root/src/config.py
RUN sed -i 's~video~/share/video~g' /root/src/config.py
RUN mkdir -p /share/covers/
RUN chmod -R 755 /share

COPY start_service.sh /root/
EXPOSE 9000
ENTRYPOINT /root/start_service.sh
