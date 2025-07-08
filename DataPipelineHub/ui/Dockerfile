#FROM  registry.access.redhat.com/ubi9/nodejs-18-minimal as build
FROM  registry.access.redhat.com/ubi9/nodejs-22 as build
WORKDIR $HOME
RUN mkdir -p . $HOME/ui
ADD . $HOME/ui
WORKDIR $HOME/ui
RUN cd $HOME/ui
RUN npm install -g npm yarn
#RUN yarn global add @fontsource/red-hat-display universalify
RUN yarn install
RUN yarn build
RUN yarn global add serve
CMD serve -s build
# Stage 2: Serve the built app with Nginx

FROM registry.access.redhat.com/ubi9/nginx-120
#Install debugging tools
USER root
RUN dnf update -y && dnf install -y vim less iputils telnet && dnf clean all
#ADD env.conf /usr/share/nginx/modules/env.conf
USER 1001
#ADD be.conf /opt/app-root/etc/nginx.default.d/be.conf.template
COPY --from=build $HOME/ui/build $HOME
EXPOSE 8080
HEALTHCHECK CMD curl --fail http://localhost:8080 || exit 1
RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log 
CMD ["nginx", "-g", "daemon off;"]
#CMD ["/usr/bin/bash", "-c", "envsubst '$LLM_BE_URL $BE_URL' < /opt/app-root/etc/nginx.default.d/be.conf.template > /opt/app-root/etc/nginx.default.d/be.conf && nginx -g 'daemon off;'"]
