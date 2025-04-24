FROM quay-nonprod.elevancehealth.com/multiarchitecture-golden-base-images/rhel-python-image-with-certs:python3.12
 
USER 0
 
RUN cat /etc/os-release
RUN gcc --version
RUN yum -y update && yum install -y \
         wget \
         python3 \
         nginx \
         ca-certificates \
         python3-pip \
&& yum clean all && rm -rf /var/cache/yum && rm -rf /var/lib/apt/lists/*
# RUN pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
# RUN yum install -y gcc-10.2.1
RUN pip install --upgrade pip
RUN pip install --upgrade awscli
CMD ["aws", "--version"]
RUN pip install ragatouille==0.0.8post2 python-dotenv==1.0.1 inflect==7.3.1 snowflake-connector-python==3.11.0 sqlparse==0.5.1 boto3  gunicorn && \
        rm -rf /root/.cache
 
RUN gcc --version
 
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"
 
WORKDIR /opt/program
COPY .. /opt/program
 
EXPOSE 8080
ENTRYPOINT ["python", "/opt/program/predictor.py"]