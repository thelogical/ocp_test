FROM registry.access.redhat.com/ubi8/python-38 
ADD . /app
RUN pip install -r requirements.txt
USER root
RUN chmod 777 -R /app && RUN chmod +x -R /opt/app-root/lib64
USER default
WORKDIR /app
ENV MYSQL_SERVER=10.88.0.10
ENV MYSQL_USER=flask
ENV MYSQL_PASS=flask_user
ENV MYSQL_DATABASE=users
ENTRYPOINT ["python3"]
CMD ["app.py"]
