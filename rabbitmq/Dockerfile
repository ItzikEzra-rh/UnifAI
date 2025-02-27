FROM docker.io/library/rabbitmq:4.0-management

# Define environment variables.
ENV RABBITMQ_USER genie
ENV RABBITMQ_PASSWORD geni123
ENV RABBITMQ_PID_FILE /var/lib/rabbitmq/mnesia/rabbitmq

ADD init.sh /init.sh
RUN chmod +x /init.sh
EXPOSE 15672

# Define default command
CMD ["/init.sh"]