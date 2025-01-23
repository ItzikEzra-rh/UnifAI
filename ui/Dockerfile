#FROM  registry.access.redhat.com/ubi9/nodejs-18-minimal as build
FROM  registry.access.redhat.com/ubi9/nodejs-20-minimal as build
WORKDIR $HOME
RUN mkdir -p . $HOME/ui
ADD . $HOME/ui
WORKDIR $HOME/ui
RUN cd $HOME/ui
RUN cat $HOME/ui/package.json
RUN npm install -g npm yarn
RUN npm install -g @fontsource/red-hat-display
RUN yarn install
RUN npm run build
RUN yarn global add serve
CMD serve -s build
# Stage 2: Serve the built app with Nginx

FROM registry.access.redhat.com/ubi9/nginx-120
COPY --from=build $HOME/ui/build $HOME
EXPOSE 8080
HEALTHCHECK CMD curl --fail http://localhost:8080 || exit 1
CMD ["nginx", "-g", "daemon off;"]
